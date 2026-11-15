from crewai import Crew, Process, Task
from crewai.flow import Flow, listen, router, start, or_
from datapilot.agents import create_all_agents
from datapilot.flows.state import AnalyticsState
from datapilot.schemas.plan import AnalysisPlan

import json

from datapilot.analytics.sales import (
    load_sales_data,
    calculate_monthly_revenue,
)
from datapilot.schemas.qa import QAResult
from datapilot.database.metadata import (
    save_analysis_run,
    save_agent_event,
)
MAX_RETRIES = 2
from datapilot.visualization.charts import build_sales_charts
from datapilot.schemas.charts import DashboardOutput
from datapilot.flows.task_executor import execute_plan

class AnalyticsFlow(Flow[AnalyticsState]):

    @start()
    def receive_question(self):
        """Validate the incoming business question."""

        question = self.state.user_question.strip()

        if len(question) < 10:
            raise ValueError("Please provide a more specific business question.")

        self.state.user_question = question
        self.state.status = "running"
        self.state.current_stage = "planning"

        print(f"[{self.state.run_id}] Starting analysis")
        return question

    @listen(receive_question)
    def create_plan(self, question: str):
        """Ask the Planner to produce a structured analysis plan."""

        agents = create_all_agents()
        planner = agents["planner"]

        task = Task(
            description=f"""
            Create an analysis plan for this business question:

            {question}

            Your responsibilities:
            1. Identify the business objective.
            2. Break the investigation into actionable tasks.
            3. Assign each task to the appropriate specialist.
            4. Identify dependencies between tasks.
            5. Focus on evidence available in the sales database.

            Agent selection rules:

            - data_engineer:
            Required for retrieving relevant data from PostgreSQL.

            - analyst:
            Required for calculating and interpreting business results.

            - dashboard:
            Optional.
            Include this agent only when:
            a. The user explicitly requests a chart, graph, or dashboard.
            b. A visualization would materially improve the requested analysis.

            Do not create unnecessary dashboard tasks for questions that only
            require a textual or numerical answer.

            Dependency rules:
            - Every task must have a unique task_id.
            - Dependencies must reference existing task IDs.
            - Dashboard tasks must depend on the relevant analytical task.
            - Tasks must not depend on themselves.
            - Avoid circular dependencies.

            Do not assign QA tasks. QA is always executed by the system.
            """,
            expected_output="A valid structured AnalysisPlan.",
            agent=planner,
            output_pydantic=AnalysisPlan,
        )

        crew = Crew(
            agents=[planner],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        if result.pydantic is None:
            raise ValueError("Planner did not return a valid AnalysisPlan.")
        plan = result.pydantic

        task_ids = [task.task_id for task in plan.tasks]

        # Check duplicate task IDs.
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Planner generated duplicate task IDs.")

        known_ids = set(task_ids)

        # Check dependencies.
        for task in plan.tasks:
            for dependency in task.dependencies:
                if dependency not in known_ids:
                    raise ValueError(
                        f"Task {task.task_id} has unknown dependency: "
                        f"{dependency}"
                    )

            if task.task_id in task.dependencies:
                raise ValueError(
                    f"Task {task.task_id} cannot depend on itself."
                )

            # Check mandatory agents.
            required_agents = {
                task.assigned_agent
                for task in plan.tasks
            }

            mandatory_agents = {"data_engineer", "analyst"}

            missing_agents = mandatory_agents - required_agents

            if missing_agents:
                raise ValueError(
                    f"Planner omitted mandatory agents: {missing_agents}"
                )

            self.state.plan = plan
        self.state.plan = result.pydantic
        self.state.current_stage = "data_engineering"
        save_analysis_run(self.state)

        save_agent_event(
            run_id=self.state.run_id,
            stage="planning",
            event_type="completed",
            message="Analysis plan created.",
        )
        print("[Planner] Analysis plan created")
        return result.pydantic

    @listen(create_plan)
    def execute_planned_tasks(self, plan: AnalysisPlan):
        """Execute exactly the tasks defined by the Planner."""

        print("\n[Flow] Starting Planner-driven execution")

        result = execute_plan(
            plan=plan,
            state=self.state,
        )

        print("\n[Flow] All planned tasks completed")

        return result

    @listen(execute_planned_tasks)
    def route_after_analysis(self) -> str:
        """Decide whether dashboard generation is required."""

        if self.state.plan is None:
            raise ValueError("Analysis plan is missing.")

        dashboard_required = any(
            task.assigned_agent == "dashboard"
            for task in self.state.plan.tasks
        )

        if dashboard_required:
            print("[Flow] Dashboard generation required")
            return "dashboard_required"

        print("[Flow] Dashboard generation skipped")

        self.state.chart_specs = []

        save_agent_event(
            run_id=self.state.run_id,
            stage="dashboard",
            event_type="skipped",
            message="Dashboard was not required by the analysis plan.",
        )

        save_analysis_run(self.state)

        return "dashboard_skipped"

    @listen("dashboard_skipped")
    def skip_dashboard(self):
        """Continue without generating visualizations."""

        self.state.chart_specs = []

        return "Dashboard skipped"

    @listen(or_(generate_dashboard, skip_dashboard))
    def review_and_correct(self, initial_analysis: str):
        """Review the report and request bounded corrections."""

        agents = create_all_agents()
        analyst = agents["analyst"]
        qa_agent = agents["qa"]

        current_report = initial_analysis

        for attempt in range(MAX_RETRIES + 1):
            self.state.current_stage = "quality_assurance"

            qa_task = Task(
                description=f"""
                Review this analytical report.

                Original business question:
                {self.state.user_question}

                Verified metrics:
                {self.state.metrics}

                Retrieved data:
                {self.state.query_results}

                Chart specifications:
                {self.state.chart_specs}

                Analytical report:
                {current_report}

                Check:
                1. Numerical claims match the verified metrics.
                2. Conclusions are supported by retrieved data.
                3. Facts and hypotheses are distinguished.
                4. The report answers the original question.
                5. The report does not invent evidence.

                Return passed=True only when the report is acceptable.
                If it fails, provide specific correction instructions.
                """,
                expected_output="A structured QAResult.",
                agent=qa_agent,
                output_pydantic=QAResult,
            )

            qa_crew = Crew(
                agents=[qa_agent],
                tasks=[qa_task],
                process=Process.sequential,
                verbose=True,
            )

            qa_result = qa_crew.kickoff()

            result = qa_result.pydantic

            if result is None:
                raise ValueError("QA Agent returned no valid QAResult.")

            self.state.qa_result = result
            self.state.analysis = current_report
            self.state.retry_count = attempt

            save_agent_event(
                run_id=self.state.run_id,
                stage="quality_assurance",
                event_type="qa_review",
                message=result.summary,
            )

            if result.passed:
                self.state.status = "completed"
                self.state.current_stage = "completed"

                save_analysis_run(self.state)

                print("[QA] Report approved")
                return current_report

            print(
                f"[QA] Rejected report. "
                f"Correction attempt {attempt + 1}/{MAX_RETRIES}"
            )

            if attempt == MAX_RETRIES:
                break

            # Give the Analyst specific feedback.
            correction_task = Task(
                description=f"""
                Revise your previous analytical report.

                Original business question:
                {self.state.user_question}

                Previous report:
                {current_report}

                QA issues:
                {result.issues}

                Required corrections:
                {result.correction_instructions}

                Verified metrics:
                {self.state.metrics}

                Retrieved data:
                {self.state.query_results}

                Correct the identified problems.
                Do not invent figures or unsupported explanations.
                Return the complete revised report.
                """,
                expected_output="A corrected analytical report.",
                agent=analyst,
            )

            correction_crew = Crew(
                agents=[analyst],
                tasks=[correction_task],
                process=Process.sequential,
                verbose=True,
            )

            correction_result = correction_crew.kickoff()
            current_report = correction_result.raw

        self.state.status = "failed"
        self.state.current_stage = "failed"
        self.state.analysis = current_report
        self.state.error = (
            "QA rejected the report after the maximum correction attempts."
        )

        save_analysis_run(self.state)

        print("[QA] Maximum correction attempts reached")
        return current_report

    