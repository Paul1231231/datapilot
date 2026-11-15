from crewai import Agent

from datapilot.config.llm import get_crewai_llm


def create_planner_agent() -> Agent:
    return Agent(
        role="Senior Business Analytics Planner",
        goal=(
            "Convert business questions into clear, ordered, "
            "and achievable analytical tasks. Assign each task "
            "to the most appropriate specialist."
        ),
        backstory=(
            "You are an experienced analytics project lead. "
            "You understand business KPIs, data dependencies, "
            "and analytical workflows. You break complicated "
            "business questions into smaller tasks and ensure "
            "that each task has a clear expected outcome."
        ),
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=3,
        verbose=True,
    )