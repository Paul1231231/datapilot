import pandas as pd
import pytest

from datapilot.analytics.sales import (
    calculate_total_revenue,
    calculate_monthly_revenue,
    calculate_category_revenue,
)


@pytest.fixture
def sample_sales_data():
    return pd.DataFrame({
        "order_date": pd.to_datetime([
            "2026-01-01",
            "2026-01-01",
            "2026-02-01",
            "2026-02-01",
        ]),
        "category": [
            "Electronics",
            "Accessories",
            "Electronics",
            "Furniture",
        ],
        "revenue": [1000, 500, 2000, 1500],
        "units_sold": [10, 5, 20, 15],
    })


def test_calculate_total_revenue(sample_sales_data):
    result = calculate_total_revenue(sample_sales_data)

    assert result == 5000.0


def test_calculate_monthly_revenue(sample_sales_data):
    result = calculate_monthly_revenue(sample_sales_data)

    assert len(result) == 2
    assert result["revenue"].sum() == 5000

    january = result.loc[
        result["month"] == "2026-01",
        "revenue",
    ].iloc[0]

    assert january == 1500


def test_calculate_category_revenue(sample_sales_data):
    result = calculate_category_revenue(sample_sales_data)

    assert result.iloc[0]["category"] == "Electronics"
    assert result.iloc[0]["revenue"] == 3000


def test_total_revenue_with_empty_dataframe():
    df = pd.DataFrame({"revenue": []})

    assert calculate_total_revenue(df) == 0.0