import streamlit as st
import plotly.express as px

from datapilot.analytics.sales import (
    load_sales_data,
    calculate_total_revenue,
    calculate_monthly_revenue,
    calculate_category_revenue,
)


st.set_page_config(
    page_title="DataPilot",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60)
def get_sales_data():
    return load_sales_data()


def main():
    st.title("📊 DataPilot")
    st.caption("AI-powered business analytics platform")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page",
        ["Sales Overview", "About"],
    )

    if page == "About":
        st.title("About DataPilot")
        st.write(
            "DataPilot is a local-first multi-agent analytics "
            "platform built with CrewAI, PostgreSQL and Python."
        )
        return

    st.header("Sales Overview")

    if st.button("Refresh data"):
        get_sales_data.clear()

    try:
        df = get_sales_data()
    except Exception as exc:
        st.error(f"Could not load sales data: {exc}")
        st.info(
            "Check that PostgreSQL is running and your .env "
            "database configuration is correct."
        )
        return

    # Calculate metrics
    total_revenue = calculate_total_revenue(df)
    monthly_df = calculate_monthly_revenue(df)
    category_df = calculate_category_revenue(df)

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}",
    )

    col2.metric(
        "Product Categories",
        df["category"].nunique(),
    )

    col3.metric(
        "Months of Data",
        monthly_df["month"].nunique(),  # <-- Use monthly_df here!
    )

    st.divider()

    # Monthly revenue chart
    st.subheader("Monthly Revenue")

    monthly_chart = px.bar(
        monthly_df,
        x="month",
        y="revenue",
        title="Revenue by Month",
        labels={
            "month": "Month",
            "revenue": "Revenue ($)",
        },
    )

    st.plotly_chart(
        monthly_chart,
        use_container_width=True,
    )

    # Category revenue chart
    st.subheader("Revenue by Product Category")

    category_chart = px.pie(
        category_df,
        names="category",
        values="revenue",
        title="Revenue Distribution",
        hole=0.4,
    )

    st.plotly_chart(
        category_chart,
        use_container_width=True,
    )

    # Data table
    st.subheader("Monthly Revenue Data")

    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Category Revenue Data")

    st.dataframe(
        category_df,
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()