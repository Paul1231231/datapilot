from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from datapilot.tools.database import execute_read_only_query


class SQLQueryInput(BaseModel):
    query: str = Field(
        description=(
            "A single read-only PostgreSQL SELECT query "
            "for retrieving business analytics data."
        )
    )


class DatabaseQueryTool(BaseTool):
    name: str = "PostgreSQL Read-Only Query Tool"

    description: str = (
        "Execute a safe, read-only PostgreSQL SELECT query "
        "against the DataPilot sales database. "
        "Use this tool to retrieve customers, orders, products, "
        "regions, and sales metrics. "
        "Only one SELECT query is allowed. "
        "The maximum returned result is 500 rows."
    )

    args_schema: Type[BaseModel] = SQLQueryInput

    def _run(self, query: str) -> str:
        return execute_read_only_query(query)