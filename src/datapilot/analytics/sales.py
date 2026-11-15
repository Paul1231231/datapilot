import json

import pandas as pd

from datapilot.tools.database import execute_read_only_query


SALES_QUERY = """
SELECT
    DATE_TRUNC('month', o.order_date)::date AS month,
    r.region_name,
    p.category,
    SUM(oi.quantity * oi.unit_price)::numeric AS revenue
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN regions r
    ON c.region_id = r.region_id
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
GROUP BY
    DATE_TRUNC('month', o.order_date)::date,
    r.region_name,
    p.category
ORDER BY
    month,
    region_name,
    category
"""


def load_sales_data() -> pd.DataFrame:
    """Load aggregated sales data from PostgreSQL."""

    raw_result = execute_read_only_query(SALES_QUERY)

    rows = json.loads(raw_result)

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No sales data found.")

    df["month"] = pd.to_datetime(df["month"])
    df["revenue"] = pd.to_numeric(df["revenue"])

    return df


def calculate_quarterly_revenue(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate total revenue for each quarter."""

    result = df.copy()

    result["quarter"] = (
        result["month"].dt.to_period("Q").astype(str)
    )

    quarterly = (
        result.groupby("quarter", as_index=False)["revenue"]
        .sum()
        .sort_values("quarter")
    )

    return quarterly


def compare_q2_q3(df: pd.DataFrame) -> dict:
    """Compare Q3 revenue with Q2 revenue."""

    quarterly = calculate_quarterly_revenue(df)

    revenue = dict(
        zip(quarterly["quarter"], quarterly["revenue"])
    )

    q2 = float(revenue.get("2026Q2", 0))
    q3 = float(revenue.get("2026Q3", 0))

    if q2 == 0:
        raise ValueError("Q2 revenue is zero; cannot calculate growth.")

    change = q3 - q2
    percentage_change = (change / q2) * 100

    return {
        "q2_revenue": round(q2, 2),
        "q3_revenue": round(q3, 2),
        "revenue_change": round(change, 2),
        "percentage_change": round(percentage_change, 2),
    }


def calculate_regional_revenue(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate revenue by region and quarter."""

    result = df.copy()

    result["quarter"] = (
        result["month"].dt.to_period("Q").astype(str)
    )

    return (
        result.groupby(
            ["region_name", "quarter"],
            as_index=False,
        )["revenue"]
        .sum()
        .sort_values(["region_name", "quarter"])
    )


def calculate_category_revenue(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate revenue by product category and quarter."""

    result = df.copy()

    result["quarter"] = (
        result["month"].dt.to_period("Q").astype(str)
    )

    return (
        result.groupby(
            ["category", "quarter"],
            as_index=False,
        )["revenue"]
        .sum()
        .sort_values(["category", "quarter"])
    )