"""Analytical building blocks used by the UI, the AI Copilot and reports.

SQL-backed functions call named queries in sql/business_queries.sql; everything else uses metrics.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics
from .database import run_query
from .formatting import fmt_money, fmt_pct

DISCOUNT_LEAKAGE_THRESHOLD_PCT = 30.0


# ---------------------------------------------------------------- filtering & comparison
def apply_filters(df: pd.DataFrame, start=None, end=None, regions=None, categories=None, segments=None) -> pd.DataFrame:
    """Filter by inclusive date range and optional lists. An empty/None list means 'all'."""
    out = df
    if start is not None:
        out = out[out["order_date"] >= pd.Timestamp(start)]
    if end is not None:
        out = out[out["order_date"] <= pd.Timestamp(end)]
    for col, values in (("region", regions), ("category", categories), ("segment", segments)):
        if values:
            out = out[out[col].isin(list(values))]
    return out


def previous_period(start, end, data_min):
    """The equal-length window immediately before [start, end], or None if the data doesn't cover it.

    The dataset is treated as continuous from the first day of its first month, so a comparison is only
    offered when the whole previous window lies inside the data. No comparison is ever estimated.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    days = (end - start).days + 1
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=days - 1)
    coverage_start = pd.Timestamp(data_min).replace(day=1)
    return (prev_start, prev_end) if prev_start >= coverage_start else None


def compare_kpis(df_scope: pd.DataFrame, start, end, data_min) -> dict:
    """KPIs for [start, end] plus the previous period and changes (None where not valid).

    `df_scope` must already carry the non-date filters (region, category, segment).
    """
    current = metrics.kpis(apply_filters(df_scope, start, end))
    prev_range = previous_period(start, end, data_min)
    if prev_range is None:
        return {"current": current, "previous": None, "changes": {}, "previous_range": None}
    previous = metrics.kpis(apply_filters(df_scope, *prev_range))
    changes = {k: metrics.growth_pct(current[k], previous[k]) for k in ("revenue", "profit", "orders", "aov")}
    cm, pm = current["margin_pct"], previous["margin_pct"]
    changes["margin_pp"] = None if cm is None or pm is None else cm - pm  # margin change in percentage points
    return {"current": current, "previous": previous, "changes": changes, "previous_range": prev_range}


# ---------------------------------------------------------------- SQL-backed queries
def monthly_trend(df): return run_query("revenue_by_month", df)
def monthly_growth(df): return run_query("monthly_growth", df)
def category_margin(df): return run_query("margin_by_category", df)
def subcategory_margin(df): return run_query("margin_by_subcategory", df)
def region_performance(df): return run_query("region_performance", df)
def purchase_frequency(df): return run_query("customer_purchase_frequency", df)
def segment_profitability(df): return run_query("segment_profitability", df)
def top_products_by_profit(df, n=10): return run_query("top_products_by_profit", df, {"limit": n})
def top_customers(df, n=10): return run_query("top_customers_by_revenue", df, {"limit": n})
def high_revenue_low_profit(df, max_margin_pct=5.0, n=10):
    return run_query("high_revenue_low_profit", df, {"max_margin_pct": max_margin_pct, "limit": n})


def discount_bands(df: pd.DataFrame) -> pd.DataFrame:
    return run_query("discount_impact", df)


# ---------------------------------------------------------------- products & customers (pandas)
def product_summary(df: pd.DataFrame) -> pd.DataFrame:
    return metrics.group_summary(df, ["product_id", "product_name", "category"])


def top_products_by_revenue(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return product_summary(df).nlargest(n, "revenue").reset_index(drop=True)


def lowest_margin_products(df: pd.DataFrame, n: int = 10, min_revenue: float = 0.0) -> pd.DataFrame:
    p = product_summary(df)
    p = p[(p["revenue"] >= min_revenue) & p["margin_pct"].notna()]
    return p.nsmallest(n, "margin_pct").reset_index(drop=True)


def contribution_curve(df: pd.DataFrame, value: str = "sales") -> pd.DataFrame:
    """Cumulative share of `value` (sales or profit) across products ranked high to low."""
    col = "sales" if value == "sales" else "profit"
    s = df.groupby("product_id")[col].sum().sort_values(ascending=False)
    if s.empty or s.sum() <= 0:
        return pd.DataFrame(columns=["product_rank", "pct_of_products", "cum_share_pct"])
    cum = s.clip(lower=0).cumsum() / s.clip(lower=0).sum() * 100
    return pd.DataFrame({"product_rank": np.arange(1, len(s) + 1),
                         "pct_of_products": np.arange(1, len(s) + 1) / len(s) * 100,
                         "cum_share_pct": cum.values})


def products_for_share(curve: pd.DataFrame, share: float = 80.0):
    """(number of products, % of products) needed to reach `share`% of the value."""
    if curve.empty:
        return None
    hit = curve[curve["cum_share_pct"] >= share].iloc[0]
    return int(hit["product_rank"]), float(hit["pct_of_products"])


def customer_concentration(df: pd.DataFrame, top_pct: float = 10.0):
    """Share of revenue from the top `top_pct`% of customers."""
    s = df.groupby("customer_id")["sales"].sum().sort_values(ascending=False)
    if s.empty or s.sum() <= 0:
        return None
    k = max(1, int(np.ceil(len(s) * top_pct / 100)))
    return float(s.head(k).sum() / s.sum() * 100)


def customer_orders_summary(df: pd.DataFrame) -> dict:
    return {
        "customers": int(df["customer_id"].nunique()),
        "repeat_rate_pct": metrics.repeat_customer_rate(df),
        "aov": metrics.average_order_value(df),
        "orders_per_customer": metrics.safe_div(metrics.order_count(df), df["customer_id"].nunique()) if len(df) else None,
    }


# ---------------------------------------------------------------- discounts
def discount_leakage(df: pd.DataFrame, threshold_pct: float = DISCOUNT_LEAKAGE_THRESHOLD_PCT) -> dict:
    """Profit/revenue on lines discounted at or above `threshold_pct`."""
    deep = df[df["discount_pct"] >= threshold_pct]
    total_rev = metrics.revenue(df)
    return {
        "threshold_pct": threshold_pct,
        "lines": int(len(deep)),
        "lines_share_pct": float(len(deep) / len(df) * 100) if len(df) else None,
        "revenue": metrics.revenue(deep),
        "revenue_share_pct": (metrics.revenue(deep) / total_rev * 100) if total_rev else None,
        "profit": metrics.profit(deep),
        "margin_pct": metrics.profit_margin(deep),
        "loss_line_pct": float((deep["profit"] < 0).mean() * 100) if len(deep) else None,
    }


def leakage_by_subcategory(df: pd.DataFrame, threshold_pct: float = DISCOUNT_LEAKAGE_THRESHOLD_PCT) -> pd.DataFrame:
    deep = df[df["discount_pct"] >= threshold_pct]
    if deep.empty:
        return pd.DataFrame(columns=["subcategory", "revenue", "profit", "margin_pct"])
    g = metrics.group_summary(deep, "subcategory")[["subcategory", "revenue", "profit", "margin_pct"]]
    return g.sort_values("profit").reset_index(drop=True)


# ---------------------------------------------------------------- insights
def business_insights(df: pd.DataFrame, limit: int = 3) -> list[dict]:
    """Up to `limit` concise, data-driven observations. Each: {title, text, tone: 'neg'|'pos'|'info'}."""
    if df.empty:
        return []
    out: list[dict] = []

    leak = discount_leakage(df)
    if leak["lines"] and leak["profit"] < 0:
        out.append({"title": "Heavy discounts are destroying profit", "tone": "neg",
                    "text": f"Lines discounted {leak['threshold_pct']:.0f}%+ made {fmt_pct(leak['revenue_share_pct'])} of revenue "
                            f"but lost {fmt_money(abs(leak['profit']))} (margin {fmt_pct(leak['margin_pct'])})."})

    sub = metrics.group_summary(df, ["category", "subcategory"])
    losers = sub[sub["profit"] < 0].sort_values("profit")
    if len(losers):
        names = ", ".join(losers["subcategory"].head(3))
        out.append({"title": "Loss-making sub-categories", "tone": "neg",
                    "text": f"{names} lose {fmt_money(abs(losers['profit'].sum()))} combined despite "
                            f"{fmt_money(losers['revenue'].sum())} of revenue."})
    elif len(sub):
        low = sub.nsmallest(1, "margin_pct").iloc[0]
        out.append({"title": "Lowest-margin sub-category", "tone": "info",
                    "text": f"{low['subcategory']} earns just {fmt_pct(low['margin_pct'])} on {fmt_money(low['revenue'])} of revenue."})

    reg = metrics.group_summary(df, "region").dropna(subset=["margin_pct"])
    if len(reg) >= 2:
        best, worst = reg.loc[reg["margin_pct"].idxmax()], reg.loc[reg["margin_pct"].idxmin()]
        out.append({"title": "Regional margin gap", "tone": "info",
                    "text": f"{best['region']} earns {fmt_pct(best['margin_pct'])} versus {fmt_pct(worst['margin_pct'])} in "
                            f"{worst['region']} - a {best['margin_pct'] - worst['margin_pct']:.1f} point gap."})

    years = sorted(df["order_year"].unique())
    if len(years) >= 2:
        cur, prev = df[df["order_year"] == years[-1]], df[df["order_year"] == years[-2]]
        rg = metrics.growth_pct(metrics.revenue(cur), metrics.revenue(prev))
        pg = metrics.growth_pct(metrics.profit(cur), metrics.profit(prev))
        if rg is not None and pg is not None and pg < rg - 5:
            out.append({"title": "Profit is lagging revenue", "tone": "neg",
                        "text": f"{years[-1]} revenue grew {rg:+.1f}% but profit only {pg:+.1f}% vs {years[-2]}."})
    return out[:limit]
