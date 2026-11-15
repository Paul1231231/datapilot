from crewai import Crew, Process, Task
from crewai.flow import Flow, listen, start

from datapilot.agents import create_all_agents
from datapilot.flows.state import AnalyticsState
from datapilot.schemas.plan import AnalysisPlan

import json

from datapilot.analytics.sales import (
    load_sales_data,
    compare_q2_q3,
)
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

        print("[Data Engineer] Database retrieval completed")
        return result.raw

    @listen(retrieve_data)
    def analyze_results(self, query_results: str): 
        """Calculate metrics and ask the Analyst to interpret them."""

        # 1. Load the aggregated sales dataset.
        df = load_sales_data()

        # 2. Calculate metrics using Python.
        metrics = compare_q2_q3(df)

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
            - Explain the Q2 versus Q3 revenue difference.
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
        self.state.current_stage = "completed"
        self.state.status = "completed"

        return result.raw