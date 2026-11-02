"""RFM customer segmentation (rule-based, deterministic).

Recency   = days from the customer's last order to (latest order date in the data + 1 day)
Frequency = number of distinct orders
Monetary  = total sales
Each is scored 1-5 by percentile rank (ties share a score; 5 = best, so LOW recency days = 5).
Segments from R and FM = (F score + M score) / 2, evaluated in this order:
    Champions           R >= 4 and FM >= 4
    Loyal Customers     R >= 3 and FM >= 3
    Potential Loyalists R >= 3 (lower FM: recent but low frequency/spend)
    At Risk             R <= 2 and FM >= 3 (valuable but lapsing)
    Lost Customers      R <= 2 and FM < 3
This is a descriptive grouping, not a predictive model, so no accuracy is claimed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEGMENTS = ["Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost Customers"]
COLUMNS = ["customer_id", "customer_name", "recency_days", "frequency", "monetary", "profit",
           "r_score", "f_score", "m_score", "segment"]


def _score(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """1-5 score from percentile rank; ties get the same score."""
    ranks = values.rank(method="average", ascending=higher_is_better)
    return np.ceil(ranks / len(values) * 5).clip(1, 5).astype(int)


def assign_segment(r: int, fm: float) -> str:
    if r >= 4 and fm >= 4:
        return "Champions"
    if r >= 3 and fm >= 3:
        return "Loyal Customers"
    if r >= 3:
        return "Potential Loyalists"
    if fm >= 3:
        return "At Risk"
    return "Lost Customers"


def rfm_table(df: pd.DataFrame, as_of=None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    ref = pd.Timestamp(as_of) if as_of is not None else df["order_date"].max() + pd.Timedelta(days=1)
    g = df.groupby("customer_id").agg(
        customer_name=("customer_name", "first"), last_order=("order_date", "max"),
        frequency=("order_id", "nunique"), monetary=("sales", "sum"), profit=("profit", "sum"),
    ).reset_index()
    g["recency_days"] = (ref - g["last_order"]).dt.days
    g["r_score"] = _score(g["recency_days"], higher_is_better=False)
    g["f_score"] = _score(g["frequency"])
    g["m_score"] = _score(g["monetary"])
    fm = (g["f_score"] + g["m_score"]) / 2
    g["segment"] = [assign_segment(r, x) for r, x in zip(g["r_score"], fm)]
    return g[COLUMNS].sort_values("monetary", ascending=False).reset_index(drop=True)


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    cols = ["segment", "customers", "customers_pct", "revenue", "profit", "avg_recency_days", "avg_orders"]
    if rfm.empty:
        return pd.DataFrame(columns=cols)
    g = rfm.groupby("segment").agg(customers=("customer_id", "count"), revenue=("monetary", "sum"),
                                   profit=("profit", "sum"), avg_recency_days=("recency_days", "mean"),
                                   avg_orders=("frequency", "mean")).reindex(SEGMENTS).dropna(subset=["customers"])
    g["customers_pct"] = g["customers"] / g["customers"].sum() * 100
    return g.reset_index()[cols]
