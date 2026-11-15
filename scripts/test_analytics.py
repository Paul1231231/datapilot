from datapilot.analytics.sales import (
    load_sales_data,
    calculate_quarterly_revenue,
    calculate_regional_revenue,
    calculate_category_revenue,
    compare_q2_q3,
)


def main():
    df = load_sales_data()

    print("\n========== SOURCE DATA ==========")
    print(df.head())

    print("\n========== QUARTERLY REVENUE ==========")
    print(calculate_quarterly_revenue(df))

    print("\n========== Q2 VS Q3 ==========")
    print(compare_q2_q3(df))

    print("\n========== REGIONAL REVENUE ==========")
    print(calculate_regional_revenue(df))

    print("\n========== CATEGORY REVENUE ==========")
    print(calculate_category_revenue(df))


if __name__ == "__main__":
    main()