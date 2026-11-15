from datapilot.tools.database import execute_read_only_query


def main():
    query = """
        SELECT
            r.region_name,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.customer_id
        JOIN regions r
            ON c.region_id = r.region_id
        JOIN order_items oi
            ON o.order_id = oi.order_id
        GROUP BY r.region_name
        ORDER BY revenue DESC
    """

    result = execute_read_only_query(query)

    print(result)


if __name__ == "__main__":
    main()