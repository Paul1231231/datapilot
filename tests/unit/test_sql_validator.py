import pytest

from datapilot.tools.sql_validator import (
    SQLValidationError,
    validate_read_only_sql,
)


def test_valid_select():
    query = "SELECT * FROM customers"

    result = validate_read_only_sql(query)

    assert "SELECT" in result.upper()


def test_valid_join():
    query = """
        SELECT c.customer_name, r.region_name
        FROM customers c
        JOIN regions r
            ON c.region_id = r.region_id
    """

    result = validate_read_only_sql(query)

    assert "JOIN" in result.upper()


def test_reject_delete():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            "DELETE FROM customers"
        )


def test_reject_drop():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            "DROP TABLE customers"
        )


def test_reject_multiple_statements():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            "SELECT * FROM customers; DELETE FROM customers;"
        )


def test_reject_insert():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            "INSERT INTO customers VALUES (1, 'Test', 1)"
        )


def test_reject_select_into():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql(
            "SELECT * INTO new_customers FROM customers"
        )


def test_reject_empty_query():
    with pytest.raises(SQLValidationError):
        validate_read_only_sql("")