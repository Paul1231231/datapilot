import json
from decimal import Decimal

from sqlalchemy import text

from datapilot.database.connection import get_engine
from datapilot.tools.sql_validator import validate_read_only_sql


MAX_ROWS = 500


def execute_read_only_query(query: str) -> str:
    safe_query = validate_read_only_sql(query)

    # Wrap the SELECT to enforce a maximum number of returned rows.
    limited_query = f"""
        SELECT *
        FROM ({safe_query}) AS datapilot_result
        LIMIT :row_limit
    """

    engine = get_engine()

    with engine.connect() as connection:
        with connection.begin():
            # PostgreSQL enforces read-only transaction behavior.
            connection.execute(
                text("SET TRANSACTION READ ONLY")
            )

            # Protect against unexpectedly expensive queries.
            connection.execute(
                text("SET LOCAL statement_timeout = '10s'")
            )

            result = connection.execute(
                text(limited_query),
                {"row_limit": MAX_ROWS},
            )

            rows = result.mappings().all()

    return json.dumps(
        [dict(row) for row in rows],
        default=lambda value: (
            float(value)
            if isinstance(value, Decimal)
            else value.isoformat()
            if hasattr(value, "isoformat")
            else str(value)
        ),
        indent=2,
    )