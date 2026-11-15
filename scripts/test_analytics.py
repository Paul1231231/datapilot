from datapilot.analytics.sales import (
    load_sales_data,
    calculate_total_revenue,
    calculate_monthly_revenue,
    calculate_category_revenue,
)


def main():
    df = load_sales_data()

    print("\n--- DATA OVERVIEW ---")
    print(df.head())
    print("Rows:", len(df))
    print("Date range:", df["order_date"].min(), "to", df["order_date"].max())

    print("\n--- TOTAL REVENUE ---")
    print(calculate_total_revenue(df))

    print("\n--- MONTHLY REVENUE ---")
    print(calculate_monthly_revenue(df))

    print("\n--- CATEGORY REVENUE ---")
    print(calculate_category_revenue(df))


if __name__ == "__main__":
    main()