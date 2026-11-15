from crewai import Agent

from datapilot.config.llm import get_crewai_llm


def create_dashboard_agent() -> Agent:
    return Agent(
        role="Business Intelligence Dashboard Specialist",
        goal=(
            "Design clear, accurate, and useful visualizations "
            "that communicate analytical findings."
        ),
        backstory=(
            "You are an experienced BI developer specializing "
            "in business dashboards, data storytelling, and "
            "visual analytics. You understand when to use "
            "bar charts, line charts, pie charts, and other "
            "visualizations. You prioritize readability, "
            "correct labels, and faithful representation of data."
        ),
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=3,
        verbose=True,
    )