from crewai import Agent

from datapilot.config.llm import get_crewai_llm


def create_analyst_agent() -> Agent:
    return Agent(
        role="Senior Business Data Analyst",
        goal=(
            "Turn validated business data into accurate, "
            "evidence-based insights and actionable recommendations."
        ),
        backstory=(
            "You are an experienced business analyst with "
            "expertise in revenue analysis, KPI measurement, "
            "trend analysis, segmentation, and anomaly detection. "
            "You distinguish facts from hypotheses, explain "
            "calculations, and never claim causation without "
            "sufficient supporting evidence."
        ),
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=3,
        verbose=True,
    )