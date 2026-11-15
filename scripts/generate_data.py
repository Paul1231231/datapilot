import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


random.seed(42)

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


regions = pd.DataFrame({
    "region_id": [1, 2, 3, 4],
    "region_name": [
        "North",
        "South",
        "East",
        "West",
    ],
})

products = pd.DataFrame({
    "product_id": [1, 2, 3, 4, 5, 6],
    "product_name": [
        "Laptop",
        "Smartphone",
        "Monitor",
        "Keyboard",
        "Mouse",
        "Headphones",
    ],
    "category": [
        "Electronics",
        "Electronics",
        "Electronics",
        "Accessories",
        "Accessories",
        "Accessories",
    ],
})

customers = []

for customer_id in range(1, 201):
    customers.append({
        "customer_id": customer_id,
        "customer_name": f"Customer_{customer_id}",
        "region_id": random.choice([1, 2, 3, 4]),
    })

customers = pd.DataFrame(customers)


# Approximate daily order volume by quarter.
quarterly_order_rates = {
    1: 8,
    2: 11,
    3: 7,
    4: 10,
}

# Region West receives a larger Q3 reduction.
region_weights = {
    1: [0.25, 0.25, 0.25, 0.25],
    2: [0.25, 0.25, 0.25, 0.25],
    3: [0.25, 0.25, 0.25, 0.25],
    4: [0.25, 0.25, 0.25, 0.25],
}

# Product demand changes in Q3.
product_weights = {
    1: [0.25, 0.20, 0.15, 0.15, 0.15, 0.10],
    2: [0.25, 0.20, 0.15, 0.15, 0.15, 0.10],
    3: [0.10, 0.10, 0.10, 0.20, 0.25, 0.25],
    4: [0.25, 0.20, 0.15, 0.15, 0.15, 0.10],
}

base_prices = {
    1: 1000,
    2: 700,
    3: 300,
    4: 80,
    5: 40,
    6: 120,
}


def quarter_of(month):
    return (month - 1) // 3 + 1


orders = []
order_items = []

order_id = 1
order_item_id = 1

start_date = date(2026, 1, 1)
end_date = date(2026, 12, 31)

current_date = start_date

while current_date <= end_date:

    quarter = quarter_of(current_date.month)

    daily_orders = random.randint(
        max(1, quarterly_order_rates[quarter] - 3),
        quarterly_order_rates[quarter] + 3,
    )

    while current_date.month in [7, 8, 9]:
        # Intentionally reduce West region orders in Q3.
        if random.random() < 0.20:
            break
        break

    for _ in range(daily_orders):

        customer = random.choice(customers.to_dict("records"))

        region_id = customer["region_id"]

        if quarter == 3 and region_id == 4:
            # Fewer orders from West in Q3.
            if random.random() < 0.45:
                continue

        orders.append({
            "order_id": order_id,
            "customer_id": customer["customer_id"],
            "order_date": current_date,
        })

        num_items = random.randint(1, 3)

        available_products = products["product_id"].tolist()

        weights = product_weights[quarter]

        selected_products = random.choices(
            available_products,
            weights=weights,
            k=num_items,
        )

        for product_id in selected_products:

            quantity = random.randint(1, 4)

            price = base_prices[product_id]

            # Small realistic price variation.
            unit_price = round(
                price * random.uniform(0.9, 1.1),
                2,
            )

            order_items.append({
                "order_item_id": order_item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            })

            order_item_id += 1

        order_id += 1

    current_date += timedelta(days=1)


orders = pd.DataFrame(orders)
order_items = pd.DataFrame(order_items)

regions.to_csv(OUTPUT_DIR / "regions.csv", index=False)
customers.to_csv(OUTPUT_DIR / "customers.csv", index=False)
products.to_csv(OUTPUT_DIR / "products.csv", index=False)
orders.to_csv(OUTPUT_DIR / "orders.csv", index=False)
order_items.to_csv(OUTPUT_DIR / "order_items.csv", index=False)

print("Synthetic sales data generated.")

for name, df in {
    "regions": regions,
    "customers": customers,
    "products": products,
    "orders": orders,
    "order_items": order_items,
}.items():
    print(f"{name}: {len(df):,} rows")