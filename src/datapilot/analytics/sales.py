import pandas as pd
from datapilot.tools.database import execute_read_only_query
import json

SALES_QUERY = """
SELECT
    o.order_date,
    p.category,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id
GROUP BY
    o.order_date,
    p.category
ORDER BY
    o.order_date,
    p.category;
"""


def load_sales_data() -> pd.DataFrame:
    result = execute_read_only_query(SALES_QUERY)
    result = json.loads(result)  # Convert JSON string to Python object
    df = pd.DataFrame(result)

    if df.empty:
        raise ValueError("No sales data found.")

    df["order_date"] = pd.to_datetime(df["order_date"])
    df["revenue"] = pd.to_numeric(df["revenue"])

    return df


def calculate_total_revenue(df: pd.DataFrame) -> float:
    return float(df["revenue"].sum())


def calculate_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.assign(month=df["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["revenue"]
        .sum()
    )

    return result


def calculate_category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby("category", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )

    return result