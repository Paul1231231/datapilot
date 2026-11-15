from crewai import Crew, Process, Task
from crewai.flow import Flow, listen, start

from datapilot.agents import create_all_agents
from datapilot.database.metadata import (
    save_agent_event,
    save_analysis_run,
)
from datapilot.flows.state import AnalyticsState
from datapilot.flows.task_executor import (
    execute_plan,
    require_mandatory_agents,
    select_correction_agent,
    tasks_ready_for_qa,
    validate_plan,
)
from datapilot.schemas.plan import AnalysisPlan
from datapilot.schemas.qa import QAResult

MAX_RETRIES = 2


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
            Python calculates the verified metrics. The analyst explains
            those figures and must not replace them.

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
            - A dependency must be an earlier task.
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
        validate_plan(plan)
        require_mandatory_agents(plan)

        self.state.plan = plan
        self.state.current_stage = "data_engineering"
        save_analysis_run(self.state)

        save_agent_event(
            run_id=self.state.run_id,
            stage="planning",
            event_type="completed",
            message="Analysis plan created.",
        )
        print("[Planner] Analysis plan created")
        return plan

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
    def review_and_correct(self, initial_analysis: str):
        """Review the report and request bounded corrections."""

        if not tasks_ready_for_qa(self.state):
            raise RuntimeError(
                "QA runs only after every planned task completes."
            )

        agents = create_all_agents()
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
                Set responsible_agent to the specialist who should revise
                the work:
                - data_engineer when the retrieved evidence is wrong or missing
                - analyst when the interpretation or numerical claims are wrong
                - dashboard when the chart specifications are wrong
                Use analyst when more than one area is wrong.
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

            agent_name = select_correction_agent(result)
            correction_agent = agents[agent_name]

            correction_task = Task(
                description=f"""
                You are the {agent_name} specialist.
                Revise the analysis so it satisfies QA.

                Original business question:
                {self.state.user_question}

                Previous report:
                {current_report}

                QA issues:
                {result.issues}

                Required corrections:
                {result.correction_instructions}

                Verified metrics, calculated by Python:
                {self.state.metrics}

                Retrieved data:
                {self.state.query_results}

                Correct the identified problems in your specialty.
                Use the verified metrics exactly.
                Do not invent figures or unsupported explanations.
                Return the complete revised report.
                """,
                expected_output="A corrected analytical report.",
                agent=correction_agent,
            )

            correction_crew = Crew(
                agents=[correction_agent],
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
