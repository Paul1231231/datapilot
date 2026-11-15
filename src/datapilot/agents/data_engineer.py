from crewai import Agent

from datapilot.config.llm import get_crewai_llm
from datapilot.tools.database_tool import DatabaseQueryTool


def create_data_engineer_agent() -> Agent:
    return Agent(
        role="Senior Data Engineer",
        goal=(
            "Retrieve accurate business data using safe, "
            "efficient, and relevant database queries."
        ),
        backstory=(
            "You are an experienced data engineer specializing "
            "in PostgreSQL, data modeling, SQL optimization, "
            "and data quality. You understand relational schemas, "
            "joins, aggregations, and query performance. "
            "You never invent query results and never modify "
            "business data during analytical investigations."
        ),
        tools=[DatabaseQueryTool()],
        llm=get_crewai_llm(),
        allow_delegation=False,
        max_iter=5,
        verbose=True,
    )