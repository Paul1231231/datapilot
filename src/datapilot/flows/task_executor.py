import json
from typing import Any

from crewai import Crew, Process, Task

from datapilot.agents import create_all_agents
from datapilot.analytics.sales import compute_verified_metrics
from datapilot.schemas.plan import AnalysisPlan
from datapilot.schemas.charts import DashboardOutput
from datapilot.schemas.qa import QAResult
from datapilot.flows.state import AnalyticsState
from datapilot.database.metadata import (
    save_analysis_run,
    save_agent_event,
)


SUPPORTED_AGENTS = {
    "data_engineer",
    "analyst",
    "dashboard",
}

MANDATORY_AGENTS = {
    "data_engineer",
    "analyst",
}


def validate_plan(plan: AnalysisPlan) -> None:
    """
    Validate the plan before executing any agent.

    This executor follows the Planner's task order.
    Dependencies must therefore refer to earlier tasks.
    """

    if not plan.tasks:
        raise ValueError("The analysis plan contains no tasks.")

    seen_task_ids = set()

    for task in plan.tasks:

        if task.assigned_agent not in SUPPORTED_AGENTS:
            raise ValueError(
                f"Unsupported agent: {task.assigned_agent}"
            )

        if task.task_id in seen_task_ids:
            raise ValueError(
                f"Duplicate task ID: {task.task_id}"
            )

        for dependency in task.dependencies:

            if dependency not in seen_task_ids:
                raise ValueError(
                    f"Task {task.task_id} depends on "
                    f"{dependency}, which has not been completed "
                    f"earlier in the plan."
                )

        seen_task_ids.add(task.task_id)


def require_mandatory_agents(plan: AnalysisPlan) -> None:
    """A business analysis plan must retrieve data and interpret it."""

    assigned = {task.assigned_agent for task in plan.tasks}
    missing = MANDATORY_AGENTS - assigned

    if missing:
        raise ValueError(
            "Planner omitted mandatory agents: "
            f"{sorted(missing)}"
        )


def select_correction_agent(result: QAResult) -> str:
    """Send a QA rejection back to the specialist who owns the issue."""

    if result.responsible_agent in SUPPORTED_AGENTS:
        return result.responsible_agent
    return "analyst"


def tasks_ready_for_qa(state: AnalyticsState) -> bool:
    """QA reviews a run only after every planned task has completed."""

    if state.status == "failed" or state.plan is None:
        return False

    completed = [
        record
        for record in state.task_results
        if record.get("status") == "completed"
    ]
    return len(completed) == len(state.plan.tasks)


def _context_output(output: Any, limit: int = 4000) -> Any:
    text = output if isinstance(output, str) else json.dumps(output, default=str)
    if len(text) <= limit:
        return output
    return text[:limit] + "...[truncated]"


def build_task_context(
    question: str,
    completed_tasks: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> str:
    """Build context from verified metrics and previously completed tasks."""

    context_tasks = [
        {
            **task,
            "output": _context_output(task.get("output")),
        }
        for task in completed_tasks
    ]

    return json.dumps(
        {
            "business_question": question,
            "verified_metrics": metrics,
            "completed_tasks": context_tasks,
        },
        indent=2,
        default=str,
    )


def execute_single_task(
    agent,
    task_description: str,
    context: str,
    expected_output: str,
    output_pydantic=None,
):
    """Execute exactly one Planner-defined task."""

    task = Task(
        description=f"""
        You are executing one task from an approved analysis plan.

        Business context and previous task results:
        {context}

        YOUR CURRENT TASK:
        {task_description}

        Execution rules:
        1. Complete the current task only.
        2. Do not independently create additional tasks.
        3. Do not skip the assigned task.
        4. Use actual database results and available evidence.
        5. Do not invent results.
        6. When verified_metrics are present, treat them as the only
           source of numerical facts. Do not recompute or replace them.
        7. Clearly report the work completed and its evidence.
        """,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=output_pydantic,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()


def record_task_failure(
    state: AnalyticsState,
    planned_task,
    exc: Exception,
) -> None:
    """Persist a failed task and stop the run from looking successful."""

    state.status = "failed"
    state.current_stage = planned_task.assigned_agent
    state.error = str(exc)
    state.task_results.append(
        {
            "task_id": planned_task.task_id,
            "description": planned_task.description,
            "assigned_agent": planned_task.assigned_agent,
            "status": "failed",
            "output": str(exc),
        }
    )

    save_analysis_run(state)
    save_agent_event(
        run_id=state.run_id,
        stage=planned_task.assigned_agent,
        event_type="task_failed",
        message=(
            f"Task {planned_task.task_id} failed: {exc}"
        ),
    )


def execute_plan(
    plan: AnalysisPlan,
    state: AnalyticsState,
) -> str:
    """
    Execute every Planner task sequentially.

    Each task receives one Crew execution.
    The same agent instance is reused for tasks assigned
    to that agent.
    """

    validate_plan(plan)

    state.task_results = []
    state.chart_specs = []

    try:
        state.metrics = compute_verified_metrics()
    except Exception as exc:
        state.status = "failed"
        state.current_stage = "metrics"
        state.error = f"Could not compute verified metrics: {exc}"
        save_analysis_run(state)
        save_agent_event(
            run_id=state.run_id,
            stage="metrics",
            event_type="task_failed",
            message=state.error,
        )
        raise

    agents = create_all_agents()

    completed_tasks: list[dict[str, Any]] = []

    engineer_results = []
    analyst_results = []

    save_agent_event(
        run_id=state.run_id,
        stage="execution",
        event_type="started",
        message=f"Executing {len(plan.tasks)} planned tasks.",
    )

    for index, planned_task in enumerate(plan.tasks, start=1):

        agent_name = planned_task.assigned_agent
        agent = agents[agent_name]

        print(
            f"\n[Task {index}/{len(plan.tasks)}] "
            f"{planned_task.task_id}: "
            f"{planned_task.description}"
        )

        print(f"[Agent] {agent_name}")

        state.current_stage = agent_name

        context = build_task_context(
            state.user_question,
            completed_tasks,
            state.metrics,
        )

        output_schema = None

        expected_output = (
            "A detailed result describing the completed task, "
            "including evidence and relevant findings."
        )

        if agent_name == "analyst":
            expected_output = (
                "An analytical report that explains the verified "
                "metrics. Use those figures exactly."
            )

        if agent_name == "dashboard":
            output_schema = DashboardOutput
            expected_output = (
                "A structured DashboardOutput containing "
                "chart specifications."
            )

        try:
            result = execute_single_task(
                agent=agent,
                task_description=planned_task.description,
                context=context,
                expected_output=expected_output,
                output_pydantic=output_schema,
            )

            if agent_name == "dashboard":
                if result.pydantic is None:
                    raise ValueError(
                        f"Dashboard task {planned_task.task_id} "
                        "returned no valid structured output."
                    )

                task_output = result.pydantic.model_dump()

                state.chart_specs.extend(
                    chart.model_dump()
                    for chart in result.pydantic.charts
                )

            else:
                task_output = result.raw
        except Exception as exc:
            record_task_failure(state, planned_task, exc)
            raise

        record = {
            "task_id": planned_task.task_id,
            "description": planned_task.description,
            "assigned_agent": agent_name,
            "status": "completed",
            "output": task_output,
        }

        completed_tasks.append(record)
        state.task_results.append(record)

        if agent_name == "data_engineer":
            engineer_results.append(task_output)

        elif agent_name == "analyst":
            analyst_results.append(task_output)

        save_analysis_run(state)

        save_agent_event(
            run_id=state.run_id,
            stage=agent_name,
            event_type="task_completed",
            message=(
                f"Task {planned_task.task_id} completed: "
                f"{planned_task.description}"
            ),
        )

        print(
            f"[Completed] {planned_task.task_id}"
        )

    state.query_results = json.dumps(
        engineer_results,
        indent=2,
        default=str,
    )

    state.analysis = "\n\n".join(
        str(result)
        for result in analyst_results
    )

    if not state.analysis:
        state.analysis = json.dumps(
            completed_tasks,
            indent=2,
            default=str,
        )

    state.current_stage = "quality_assurance"

    save_analysis_run(state)

    save_agent_event(
        run_id=state.run_id,
        stage="execution",
        event_type="completed",
        message=(
            f"All {len(completed_tasks)} planned tasks completed."
        ),
    )

    return state.analysis
