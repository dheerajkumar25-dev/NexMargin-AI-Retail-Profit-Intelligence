"""Shared builders for tests: tiny datasets with hand-checkable totals."""
import pandas as pd

from nexmargin.preprocessing import clean

BASE = {
    "Row ID": 1, "Order ID": "O1", "Order Date": "1/10/2016", "Ship Date": "1/12/2016", "Ship Mode": "Standard Class",
    "Customer ID": "C1", "Customer Name": "Ann", "Segment": "Consumer", "Country": "United States", "City": "X", "State": "Y",
    "Postal Code": 1, "Region": "East", "Product ID": "P1", "Category": "Furniture", "Sub-Category": "Chairs",
    "Product Name": "Chair", "Sales": 100.0, "Quantity": 1, "Discount": 0.0, "Profit": 20.0,
}


def build_orders(rows):
    """rows: list of dicts overriding BASE. Returns the cleaned DataFrame (same schema as production)."""
    raw = pd.DataFrame([{**BASE, **r, "Row ID": i} for i, r in enumerate(rows, start=1)])
    df, _ = clean(raw)
    return df


def small_orders():
    """Revenue 800, profit 100, margin 12.5%, 4 distinct orders, AOV 200."""
    return build_orders([
        {"Order ID": "O1", "Order Date": "1/10/2016", "Sales": 100.0, "Profit": 20.0},
        {"Order ID": "O1", "Order Date": "1/10/2016", "Sales": 50.0, "Profit": 10.0, "Product ID": "P2", "Product Name": "Desk", "Sub-Category": "Tables"},
        {"Order ID": "O2", "Order Date": "2/15/2016", "Sales": 200.0, "Profit": -20.0, "Discount": 0.4, "Region": "West", "Category": "Technology",
         "Sub-Category": "Phones", "Product ID": "P3", "Product Name": "Phone"},
        {"Order ID": "O3", "Order Date": "1/20/2017", "Sales": 300.0, "Profit": 60.0, "Customer ID": "C2", "Customer Name": "Bob", "Segment": "Corporate"},
        {"Order ID": "O4", "Order Date": "2/5/2017", "Sales": 150.0, "Profit": 30.0, "Customer ID": "C3", "Customer Name": "Cy", "Segment": "Home Office",
         "Region": "West", "Category": "Office Supplies", "Sub-Category": "Paper", "Product ID": "P4", "Product Name": "Paper"},
    ])
