from crewai import Crew, Process, Task

from datapilot.agents import create_all_agents
from datapilot.schemas.plan import AnalysisPlan


def main():
    agents = create_all_agents()
    planner = agents["planner"]

    task = Task(
        description="""
        A retail company experienced a decrease in revenue
        during Q3 compared with Q2.

        Create a structured investigation plan.

        Include these areas:
        1. Quarterly revenue comparison.
        2. Regional revenue performance.
        3. Product category performance.
        4. Potential contributors to the revenue decline.

        Assign tasks only to the available specialist agents:
        data_engineer, analyst, dashboard.

        Define dependencies where necessary.
        Do not invent business data or conclusions.
        """,
        expected_output=(
            "A structured analytical plan containing an objective, "
            "a list of tasks, task assignments, dependencies, "
            "and a brief explanation."
        ),
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

    print("\n--- Planner Result ---")

    if result.pydantic:
        print(result.pydantic.model_dump_json(indent=2))
    else:
        print(result.raw)


if __name__ == "__main__":
    main()