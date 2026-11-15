import argparse

from crewai import Crew, Process, Task

from datapilot.agents import create_all_agents


TEST_PROMPTS = {
    "planner": (
        "Create a short investigation plan for a Q3 revenue decline. "
        "Assign work to the available specialist agents."
    ),
    "data_engineer": (
        "Describe the SQL queries you would need to compare Q2 and "
        "Q3 revenue by region. Do not execute SQL or invent results."
    ),
    "analyst": (
        "Explain how you would investigate a revenue decline using "
        "validated quarterly revenue, region, and product data. "
        "Do not invent findings."
    ),
    "dashboard": (
        "Recommend three visualizations for investigating a Q3 "
        "revenue decline. Explain the purpose of each chart."
    ),
    "qa": (
        "Review this hypothetical claim: 'Revenue decreased because "
        "customers stopped buying Product A.' Explain what evidence "
        "would be required before approving this conclusion."
    ),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "agent",
        choices=TEST_PROMPTS.keys(),
    )
    args = parser.parse_args()

    agents = create_all_agents()
    agent = agents[args.agent]

    task = Task(
        description=TEST_PROMPTS[args.agent],
        expected_output=(
            "A concise, structured response appropriate to "
            "the agent's specialist responsibility."
        ),
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n--- Agent Output ---")
    print(result.raw)


if __name__ == "__main__":
    main()