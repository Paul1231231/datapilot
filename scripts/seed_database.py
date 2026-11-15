from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from datapilot.config.settings import get_settings


DATA_DIR = Path("data/raw")


def main():
    settings = get_settings()
    engine = create_engine(settings.database_url)

    table_order = [
        "regions",
        "customers",
        "products",
        "orders",
        "order_items",
    ]

    with engine.begin() as connection:
        for table in table_order:
            csv_path = DATA_DIR / f"{table}.csv"

            df = pd.read_csv(csv_path)

            if table == "orders":
                df["order_date"] = pd.to_datetime(
                    df["order_date"]
                ).dt.date

            df.to_sql(
                table,
                connection,
                if_exists="append",
                index=False,
                method="multi",
            )

            print(f"Loaded {len(df)} rows into {table}")

        # Explicit CSV IDs do not automatically advance SERIAL sequences.
        # Synchronize them so future inserts don't collide.
        for table, id_column in [
            ("regions", "region_id"),
            ("customers", "customer_id"),
            ("products", "product_id"),
            ("orders", "order_id"),
            ("order_items", "order_item_id"),
        ]:
            connection.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence(
                            '{table}', '{id_column}'
                        ),
                        COALESCE(MAX({id_column}), 1),
                        MAX({id_column}) IS NOT NULL
                    )
                    FROM {table}
                    """
                )
            )

    print("Database seeding completed.")


if __name__ == "__main__":
    main()