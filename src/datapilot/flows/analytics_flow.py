from crewai import Crew, Process, Task
from crewai.flow import Flow, listen, start

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

            The plan must:
            - Identify the business objective.
            - Break the investigation into actionable tasks.
            - Assign tasks to the appropriate agents.
            - Identify dependencies between tasks.
            - Focus on evidence that can be retrieved from the sales database.
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
    def retrieve_data(self, plan: AnalysisPlan):
        """Ask the Data Engineer to retrieve the required data."""

        agents = create_all_agents()
        engineer = agents["data_engineer"]

        task = Task(
            description=f"""
            Business question:
            {self.state.user_question}

            Analysis plan:
            {plan.model_dump_json(indent=2)}

            Use the PostgreSQL Read-Only Query Tool to retrieve
            the data needed to answer the question.

            Requirements:
            - Inspect the database if necessary.
            - Use read-only SQL.
            - Do not invent query results.
            - Return the SQL queries and their actual results.
            - Explain what each result represents.
            """,
            expected_output=(
                "SQL queries, actual database results, "
                "and a concise explanation of the retrieved data."
            ),
            agent=engineer,
        )

        crew = Crew(
            agents=[engineer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.query_results = result.raw
        self.state.current_stage = "analysis"
        save_analysis_run(self.state)

        save_agent_event(
            run_id=self.state.run_id,
            stage="data_engineering",
            event_type="completed",
            message="Database retrieval completed.",
        )
        print("[Data Engineer] Database retrieval completed")
        return result.raw

    @listen(retrieve_data)
    def analyze_results(self, query_results: str): 
        """Calculate metrics and ask the Analyst to interpret them."""

        # 1. Load the aggregated sales dataset.
        df = load_sales_data()

        # 2. Calculate metrics using Python.
        metrics = calculate_monthly_revenue(df)
        self.state.metrics = metrics
        # 3. Generate chart specifications.
        chart_specs = build_sales_charts(df)

        self.state.chart_specs = [
            chart.model_dump()
            for chart in chart_specs
        ]

        # 4. Prepare verified results for the Analyst.
        metrics_json = json.dumps(metrics, indent=2)

        charts_json = json.dumps(
            self.state.chart_specs,
            indent=2,
        )

        agents = create_all_agents()
        analyst = agents["analyst"]

        task = Task(
            description=f"""
            Answer this business question:

            {self.state.user_question}

            Retrieved database results:
            {query_results}

            Verified Python-calculated metrics:
            {metrics_json}

            Available chart specifications:
            {charts_json}

            Analyze the business results:
            - Identify relevant regional and category patterns.
            - Use the supplied calculated metrics.
            - Distinguish observed facts from possible explanations.
            - Do not invent numbers or claim causation without evidence.
            """,
            expected_output=(
                "A structured analytical report with KPIs, "
                "findings, evidence, and conclusions."
            ),
            agent=analyst,
        )

        crew = Crew(
            agents=[analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.analysis = result.raw
        self.state.current_stage = "quality_assurance"

        save_analysis_run(self.state)

        return result.raw

    @listen(analyze_results)
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