import pytest

from datapilot.analytics.sales import load_sales_data


@pytest.mark.integration
def test_load_sales_data_from_postgres():
    df = load_sales_data()

    assert not df.empty
    assert {"order_date", "category", "revenue"}.issubset(
        df.columns
    )

    assert df["revenue"].notna().all()
    assert (df["revenue"] >= 0).all()