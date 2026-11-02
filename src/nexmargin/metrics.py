"""Single source of truth for every business metric in NexMargin.

Definitions (all computed on whatever DataFrame is passed in):
    Revenue          = sum(sales)
    Profit           = sum(profit)
    Profit margin    = profit / revenue x 100
    Orders           = number of DISTINCT order_id
    AOV              = revenue / orders
    Average discount = simple mean of discount_pct across order lines
    Growth %         = (current - previous) / |previous| x 100   (None if previous is 0/missing)
Division by zero returns None (shown as "n/a"), never 0 or infinity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def safe_div(numerator, denominator):
    """numerator / denominator, or None when undefined."""
    try:
        if denominator is None or numerator is None or pd.isna(denominator) or pd.isna(numerator) or denominator == 0:
            return None
        return float(numerator) / float(denominator)
    except (TypeError, ValueError):
        return None


def revenue(df: pd.DataFrame) -> float:
    return float(df["sales"].sum()) if len(df) else 0.0


def profit(df: pd.DataFrame) -> float:
    return float(df["profit"].sum()) if len(df) else 0.0


def profit_margin(df: pd.DataFrame):
    r = safe_div(profit(df), revenue(df))
    return None if r is None else r * 100


def order_count(df: pd.DataFrame) -> int:
    return int(df["order_id"].nunique()) if len(df) else 0


def average_order_value(df: pd.DataFrame):
    return safe_div(revenue(df), order_count(df))


def average_discount(df: pd.DataFrame):
    return float(df["discount_pct"].mean()) if len(df) else None


def growth_pct(current, previous):
    """Percentage change vs a previous value. Uses |previous| so a move from a loss to a profit reads as positive."""
    if current is None or previous is None or pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (float(current) - float(previous)) / abs(float(previous)) * 100


def kpis(df: pd.DataFrame) -> dict:
    return {
        "revenue": revenue(df),
        "profit": profit(df),
        "margin_pct": profit_margin(df),
        "orders": order_count(df),
        "aov": average_order_value(df),
        "avg_discount_pct": average_discount(df),
        "customers": int(df["customer_id"].nunique()) if len(df) else 0,
    }


def group_summary(df: pd.DataFrame, by) -> pd.DataFrame:
    """Revenue, profit, margin, orders, AOV and contribution shares per group (sorted by revenue)."""
    by = [by] if isinstance(by, str) else list(by)
    cols = by + ["revenue", "profit", "margin_pct", "orders", "aov", "avg_discount_pct",
                 "revenue_share_pct", "profit_share_pct"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby(by, observed=True).agg(
        revenue=("sales", "sum"), profit=("profit", "sum"),
        orders=("order_id", "nunique"), avg_discount_pct=("discount_pct", "mean"),
    ).reset_index()
    g["margin_pct"] = np.where(g["revenue"] != 0, g["profit"] / g["revenue"].replace(0, np.nan) * 100, np.nan)
    g["aov"] = g["revenue"] / g["orders"].replace(0, np.nan)
    tot_rev, tot_profit = df["sales"].sum(), df["profit"].sum()
    g["revenue_share_pct"] = g["revenue"] / tot_rev * 100 if tot_rev else np.nan
    g["profit_share_pct"] = g["profit"] / tot_profit * 100 if tot_profit > 0 else np.nan
    return g[cols].sort_values("revenue", ascending=False).reset_index(drop=True)


def monthly_series(df: pd.DataFrame) -> pd.DataFrame:
    """Continuous monthly revenue / profit / margin / orders (months without sales appear as zero)."""
    cols = ["month", "revenue", "profit", "margin_pct", "orders"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    m = df.groupby("order_month").agg(revenue=("sales", "sum"), profit=("profit", "sum"),
                                      orders=("order_id", "nunique"))
    m = m.reindex(pd.date_range(m.index.min(), m.index.max(), freq="MS"), fill_value=0)
    m.index.name = "month"
    m = m.reset_index()
    m["margin_pct"] = np.where(m["revenue"] != 0, m["profit"] / m["revenue"].replace(0, np.nan) * 100, np.nan)
    return m[cols]


def repeat_customer_rate(df: pd.DataFrame):
    """% of customers with 2+ distinct orders in the selected data."""
    if df.empty:
        return None
    per_customer = df.groupby("customer_id")["order_id"].nunique()
    return float((per_customer >= 2).mean() * 100)


def annual_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Active-customer retention: of customers who ordered in year Y, the % who ordered again in Y+1.

    Only year pairs where both years are present in the data are reported.
    """
    cols = ["year", "next_year", "customers", "retained", "retention_pct"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    by_year = df.groupby("order_year")["customer_id"].apply(set)
    rows = []
    for y in sorted(by_year.index):
        if y + 1 in by_year.index and len(by_year[y]):
            kept = len(by_year[y] & by_year[y + 1])
            rows.append({"year": int(y), "next_year": int(y + 1), "customers": len(by_year[y]),
                         "retained": kept, "retention_pct": kept / len(by_year[y]) * 100})
    return pd.DataFrame(rows, columns=cols)
