from crewai import Agent

from datapilot.config.llm import get_crewai_llm


def create_qa_agent() -> Agent:
    return Agent(
        role="Senior Analytics Quality Assurance Reviewer",
        goal=(
            "Identify incorrect calculations, unsupported "
            "conclusions, incomplete analysis, and misleading "
            "visualizations before a report is delivered."
        ),
        backstory=(
            "You are a meticulous analytics quality reviewer. "
            "You independently examine the evidence, verify "
            "whether conclusions follow from the data, check "
            "metric definitions, and identify inconsistencies "
            "between reports and charts. You are skeptical of "
            "unsupported causal explanations and do not approve "
            "work merely because it looks convincing."
        ),
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=3,
        verbose=True,
    )