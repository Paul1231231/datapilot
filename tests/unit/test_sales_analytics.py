import pandas as pd
import pytest

from datapilot.analytics.sales import (
    calculate_quarterly_revenue,
    compare_q2_q3,
)


@pytest.fixture
def sample_sales():
    return pd.DataFrame({
        "month": pd.to_datetime([
            "2026-04-01",
            "2026-05-01",
            "2026-07-01",
            "2026-08-01",
        ]),
        "region_name": [
            "North", "South", "North", "South"
        ],
        "category": [
            "Electronics", "Accessories",
            "Electronics", "Accessories"
        ],
        "revenue": [1000, 1000, 500, 500],
    })


def test_quarterly_revenue(sample_sales):
    result = calculate_quarterly_revenue(sample_sales)

    assert result["revenue"].tolist() == [2000, 1000]


def test_q2_q3_comparison(sample_sales):
    result = compare_q2_q3(sample_sales)

    assert result["q2_revenue"] == 2000
    assert result["q3_revenue"] == 1000
    assert result["revenue_change"] == -1000
    assert result["percentage_change"] == -50


def test_q2_zero_raises_error(sample_sales):
    sample_sales.loc[
        sample_sales["month"].dt.quarter == 2,
        "revenue",
    ] = 0

    with pytest.raises(ValueError):
        compare_q2_q3(sample_sales)