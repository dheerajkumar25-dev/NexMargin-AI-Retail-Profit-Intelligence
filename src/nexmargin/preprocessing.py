
"""Reproducible cleaning pipeline: raw Superstore export -> validated analytical table.

`clean()` is a pure function (DataFrame in, DataFrame + report out) so it is easy to test.
Rows are only dropped for a stated reason, and every drop is counted in the report.
"""
from __future__ import annotations

import pandas as pd

RENAME = {
    "Row ID": "row_id", "Order ID": "order_id", "Order Date": "order_date",
    "Ship Date": "ship_date", "Ship Mode": "ship_mode", "Customer ID": "customer_id",
    "Customer Name": "customer_name", "Segment": "segment", "Country": "country",
    "City": "city", "State": "state", "Postal Code": "postal_code", "Region": "region",
    "Product ID": "product_id", "Category": "category", "Sub-Category": "subcategory",
    "Product Name": "product_name", "Sales": "sales", "Quantity": "quantity",
    "Discount": "discount", "Profit": "profit",
}
KEY_COLUMNS = ["order_id", "customer_id", "product_id"]
DATE_FORMAT = "%m/%d/%Y"


def _drop(df: pd.DataFrame, mask: pd.Series, reason: str, report: dict) -> pd.DataFrame:
    report["rows_removed"][reason] = int(mask.sum())
    return df.loc[~mask].copy()


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean and validate raw data. Returns (clean_df, quality_report)."""

    # Reject ambiguous input before renaming or selecting columns.
    if raw.columns.duplicated().any():
        duplicates = raw.columns[raw.columns.duplicated()].tolist()
        raise ValueError(f"Raw data contains duplicate columns: {duplicates}")

    missing = set(RENAME) - set(raw.columns)
    if missing:
        raise ValueError(f"Raw data is missing required columns: {sorted(missing)}")

    df = raw.rename(columns=RENAME)[list(RENAME.values())].copy()
    report: dict = {"rows_raw": len(df), "rows_removed": {}}

    # Types: trim text, coerce numbers and dates.
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            df[col] = df[col].astype("string").str.strip()

    for col in ["sales", "quantity", "discount", "profit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["order_date", "ship_date"]:
        df[col] = pd.to_datetime(df[col], format=DATE_FORMAT, errors="coerce")

    report["null_counts_before_cleaning"] = {
        k: int(v) for k, v in df.isna().sum().items() if v
    }

    # Duplicates: identical records that differ only in the surrogate row_id.
    dup_cols = [c for c in df.columns if c != "row_id"]
    df = _drop(
        df,
        df.duplicated(subset=dup_cols, keep="first"),
        "duplicate_records",
        report,
    )

    # Invalid values.
    df = _drop(df, df["order_date"].isna(), "invalid_order_date", report)
    df = _drop(df, df[KEY_COLUMNS].isna().any(axis=1), "missing_key_field", report)
    df = _drop(
        df,
        df[["sales", "profit"]].isna().any(axis=1),
        "missing_sales_or_profit",
        report,
    )
    df = _drop(df, df["sales"] < 0, "negative_sales", report)
    df = _drop(df, ~(df["quantity"] > 0), "invalid_quantity", report)
    df = _drop(df, ~df["discount"].between(0, 1), "invalid_discount", report)

    # Checks that flag but do not remove.
    report["ship_before_order"] = int((df["ship_date"] < df["order_date"]).sum())

    # One canonical name per Product ID.
    names_per_id = df.groupby("product_id")["product_name"].nunique()
    report["product_ids_with_multiple_names"] = int((names_per_id > 1).sum())

    canonical = (
        df.groupby("product_id")["product_name"].agg(lambda s: s.mode().iloc[0])
        if len(df) else None
    )
    if canonical is not None:
        df["product_name"] = df["product_id"].map(canonical)

    # Derived fields. Cost = sales - profit.
    df["cost"] = df["sales"] - df["profit"]
    df["discount_pct"] = (df["discount"] * 100).round(1)
    df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["order_year"] = df["order_date"].dt.year
    df["is_loss"] = df["profit"] < 0

    # Outliers are flagged, never removed.
    if len(df):
        q1, q3 = df["profit"].quantile([0.25, 0.75])
        iqr = q3 - q1
        df["is_profit_outlier"] = (
            (df["profit"] < q1 - 3 * iqr)
            | (df["profit"] > q3 + 3 * iqr)
        )
    else:
        df["is_profit_outlier"] = pd.Series(dtype=bool)

    report["profit_outliers_flagged"] = int(df["is_profit_outlier"].sum())
    report["loss_making_rows"] = int(df["is_loss"].sum())

    df = df.sort_values(
        ["order_date", "order_id", "row_id"]
    ).reset_index(drop=True)

    report["rows_clean"] = len(df)
    report["date_range"] = (
        [
            df["order_date"].min().strftime("%Y-%m-%d"),
            df["order_date"].max().strftime("%Y-%m-%d"),
        ]
        if len(df) else None
    )

    report["notes"] = [
        "cost is derived as sales - profit (the source has no cost column).",
        "Currency is US dollars as provided by the source; no conversion applied.",
    ]

    return df, report
