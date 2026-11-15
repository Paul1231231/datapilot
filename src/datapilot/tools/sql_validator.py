import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    pass


FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Into,
    exp.Lock,
    exp.Merge,
    exp.TruncateTable,
)


def validate_read_only_sql(query: str) -> str:
    if not query or not query.strip():
        raise SQLValidationError("SQL query cannot be empty")

    try:
        statements = sqlglot.parse(
            query,
            read="postgres",
        )
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError(
            f"Invalid SQL syntax: {exc}"
        ) from exc

    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError(
            "Only one SQL statement is permitted"
        )

    statement = statements[0]

    # Only SELECT-style queries are permitted.
    if not isinstance(statement, exp.Query):
        raise SQLValidationError(
            "Only SELECT queries are permitted"
        )

    # Check the complete expression tree, including CTEs.
    for node in statement.walk():
        if isinstance(node, FORBIDDEN_EXPRESSIONS):
            raise SQLValidationError(
                f"Forbidden SQL operation: {type(node).__name__}"
            )

    return statement.sql(dialect="postgres")