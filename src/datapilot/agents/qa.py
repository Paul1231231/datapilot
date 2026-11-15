from crewai import Agent

from datapilot.config.llm import get_crewai_llm


def create_qa_agent():
    return Agent(
        role="Analytics Quality Assurance Engineer",
        goal=(
            "Validate analytical reports against source data, "
            "verified metrics, and chart specifications."
        ),
        backstory=(
            "You are a meticulous analytics QA engineer. "
            "You check numerical consistency, evidence quality, "
            "business logic, and unsupported conclusions. "
            "You never approve a report just because it sounds convincing."
        ),
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=3,
        verbose=True,
    )