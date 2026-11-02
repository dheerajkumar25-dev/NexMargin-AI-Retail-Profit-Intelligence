import numpy as np
import pandas as pd
import pytest

from helpers import build_orders
from nexmargin import metrics as M


def test_core_metrics(orders):
    assert M.revenue(orders) == pytest.approx(800)
    assert M.profit(orders) == pytest.approx(100)
    assert M.profit_margin(orders) == pytest.approx(12.5)
    assert M.order_count(orders) == 4          # O1 has two lines but is one order
    assert M.average_order_value(orders) == pytest.approx(200)


def test_empty_data_is_safe(orders):
    empty = orders.iloc[0:0]
    assert M.revenue(empty) == 0 and M.profit(empty) == 0 and M.order_count(empty) == 0
    assert M.profit_margin(empty) is None and M.average_order_value(empty) is None
    assert M.group_summary(empty, "region").empty and M.monthly_series(empty).empty
    assert M.repeat_customer_rate(empty) is None and M.annual_retention(empty).empty


def test_zero_revenue_margin_is_none():
    df = build_orders([{"Sales": 0.0, "Profit": 0.0}])
    assert M.profit_margin(df) is None                 # margin on zero revenue is undefined, not 0
    assert M.average_order_value(df) == 0              # one order worth zero is a real value
    assert M.average_order_value(df.iloc[0:0]) is None  # no orders: undefined


def test_null_profit_rows_never_reach_metrics():
    df = build_orders([{"Profit": None}, {"Order ID": "O2"}])
    assert len(df) == 1 and M.profit(df) == pytest.approx(20)


def test_duplicate_orders_not_double_counted():
    df = build_orders([{"Order ID": "O1"}, {"Order ID": "O1", "Product ID": "P9", "Product Name": "Other"}])
    assert M.order_count(df) == 1 and M.revenue(df) == pytest.approx(200)


@pytest.mark.parametrize("cur,prev,expected", [
    (120, 100, 20.0), (80, 100, -20.0), (100, 100, 0.0),
    (10, 0, None), (10, None, None), (None, 10, None), (10, float("nan"), None),
    (10, -10, 200.0),        # loss -> profit reads as a positive move (|previous| denominator)
    (-20, -10, -100.0),
])
def test_growth_pct(cur, prev, expected):
    got = M.growth_pct(cur, prev)
    assert (got is None) if expected is None else got == pytest.approx(expected)


def test_group_summary_shares_and_margin(orders):
    g = M.group_summary(orders, "region")
    assert g["revenue_share_pct"].sum() == pytest.approx(100)
    assert g["profit_share_pct"].sum() == pytest.approx(100)
    east = g[g["region"] == "East"].iloc[0]
    assert east["revenue"] == pytest.approx(450) and east["profit"] == pytest.approx(90) and east["margin_pct"] == pytest.approx(20)


def test_monthly_series_fills_gaps(orders):
    m = M.monthly_series(orders)
    assert len(m) == 14                         # Jan 2016 .. Feb 2017
    assert m["revenue"].sum() == pytest.approx(800)
    assert m.loc[m["month"] == "2016-06-01", "revenue"].iloc[0] == 0


def test_repeat_rate_and_retention(orders):
    assert M.repeat_customer_rate(orders) == pytest.approx(100 / 3)   # only C1 ordered twice
    r = M.annual_retention(orders)
    assert len(r) == 1 and r.loc[0, "customers"] == 1 and r.loc[0, "retained"] == 0 and r.loc[0, "retention_pct"] == 0


def test_retention_counts_returning_customers():
    df = build_orders([{"Order ID": "A", "Order Date": "3/1/2015", "Customer ID": "C1"},
                       {"Order ID": "B", "Order Date": "3/1/2015", "Customer ID": "C2"},
                       {"Order ID": "C", "Order Date": "3/1/2016", "Customer ID": "C1"}])
    r = M.annual_retention(df).iloc[0]
    assert r["customers"] == 2 and r["retained"] == 1 and r["retention_pct"] == pytest.approx(50)


def test_safe_div():
    assert M.safe_div(1, 0) is None and M.safe_div(None, 2) is None and M.safe_div(np.nan, 2) is None
    assert M.safe_div(6, 3) == 2
