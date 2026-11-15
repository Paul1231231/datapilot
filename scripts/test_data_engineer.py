from crewai import Crew, Process, Task

from datapilot.agents import create_all_agents


def main():
    agents = create_all_agents()
    data_engineer = agents["data_engineer"]

    task = Task(
        description="""
        Investigate quarterly revenue in the sales database.

        1. Inspect the available sales data.
        2. Calculate revenue for each quarter.
        3. Calculate revenue by region.
        4. Return the actual SQL query results.
        5. Do not invent data or claim unsupported causes.

        Revenue is defined as:
        SUM(quantity * unit_price).

        Use the PostgreSQL Read-Only Query Tool.
        """,
        expected_output=(
            "A report showing quarterly revenue and regional "
            "revenue based on actual database query results."
        ),
        agent=data_engineer,
    )

    crew = Crew(
        agents=[data_engineer],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n--- Data Engineer Result ---")
    print(result.raw)


if __name__ == "__main__":
    main()