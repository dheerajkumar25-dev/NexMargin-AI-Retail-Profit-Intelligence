
import pandas as pd
import pytest

from nexmargin import analytics as A
from nexmargin import database as D
from nexmargin import metrics as M


def test_apply_filters(orders):
    assert len(A.apply_filters(orders, regions=["West"])) == 2
    assert len(A.apply_filters(orders, start="2017-01-01")) == 2
    assert len(A.apply_filters(orders, end="2016-01-31")) == 2
    assert len(A.apply_filters(orders, regions=[])) == len(orders)
    assert A.apply_filters(orders, categories=["Nothing"]).empty


def test_previous_period_requires_full_coverage():
    data_min = pd.Timestamp("2016-01-10")
    p = A.previous_period("2017-01-01", "2017-06-30", data_min)
    assert p is not None and p[1] == pd.Timestamp("2016-12-31")
    assert A.previous_period("2016-01-01", "2016-12-31", data_min) is None


def test_compare_kpis_without_prior_period_has_no_deltas(orders):
    c = A.compare_kpis(
        orders, "2016-01-01", "2017-12-31",
        orders["order_date"].min()
    )
    assert c["previous"] is None and c["changes"] == {}


def test_compare_kpis_with_prior_period(orders):
    c = A.compare_kpis(
        orders, "2017-01-01", "2017-12-31",
        orders["order_date"].min()
    )
    assert c["current"]["revenue"] == pytest.approx(450)
    assert c["previous"]["revenue"] == pytest.approx(350)
    assert c["changes"]["revenue"] == pytest.approx((450 - 350) / 350 * 100)
    assert c["changes"]["margin_pp"] == pytest.approx(
        20.0 - (10 / 350 * 100)
    )


# SQL layer
def test_sql_matches_python_metrics(orders):
    m = D.run_query("revenue_by_month", orders)
    assert m["revenue"].sum() == pytest.approx(M.revenue(orders))
    assert m["profit"].sum() == pytest.approx(M.profit(orders))
    assert m["running_revenue"].iloc[-1] == pytest.approx(800)

    reg_sql = D.run_query("region_performance", orders).set_index("region")
    reg_py = M.group_summary(orders, "region").set_index("region")

    for r in reg_py.index:
        assert reg_sql.loc[r, "revenue"] == pytest.approx(reg_py.loc[r, "revenue"])
        assert reg_sql.loc[r, "margin_pct"] == pytest.approx(reg_py.loc[r, "margin_pct"])
        assert reg_sql.loc[r, "orders"] == reg_py.loc[r, "orders"]


def test_sql_matches_python_on_real_data():
    from nexmargin import config

    if not config.PROCESSED_FILE.exists():
        pytest.skip("processed data not built")

    from nexmargin.data_loader import load_processed

    df = load_processed()
    cat_sql = D.run_query("margin_by_category", df).set_index("category")
    cat_py = M.group_summary(df, "category").set_index("category")

    for c in cat_py.index:
        assert cat_sql.loc[c, "profit"] == pytest.approx(cat_py.loc[c, "profit"])
        assert cat_sql.loc[c, "margin_pct"] == pytest.approx(cat_py.loc[c, "margin_pct"])

    assert D.run_query("revenue_by_month", df)["revenue"].sum() == pytest.approx(
        M.revenue(df)
    )


def test_month_over_month_growth_uses_lag(orders):
    g = D.run_query("monthly_growth", orders).sort_values("month").reset_index(drop=True)

    assert pd.isna(g.loc[0, "revenue_mom_pct"])
    assert g.loc[1, "revenue_mom_pct"] == pytest.approx(M.growth_pct(200, 150))
    assert g.loc[1, "revenue_mom_pct"] == pytest.approx(33.3333, rel=1e-3)


def test_top_products_and_limit_param(orders):
    top = D.run_query("top_products_by_profit", orders, {"limit": 2})

    assert len(top) == 2
    assert top.iloc[0]["profit"] >= top.iloc[1]["profit"]
    assert top.iloc[0]["rank"] == 1
    assert len(D.run_query("top_products_by_profit", orders)) == 4


def test_discount_bands_and_leakage(orders):
    b = D.run_query("discount_impact", orders).set_index("discount_band")

    assert b.loc["0%", "revenue"] == pytest.approx(600)
    assert b.loc["30-49%", "profit"] == pytest.approx(-20)

    leak = A.discount_leakage(orders)
    assert leak["lines"] == 1
    assert leak["profit"] == pytest.approx(-20)
    assert leak["loss_line_pct"] == 100


def test_customer_frequency_and_segments_queries(orders):
    f = D.run_query("customer_purchase_frequency", orders).set_index("frequency_band")

    assert f.loc["1 order", "customers"] == 2
    assert f.loc["2-3 orders", "customers"] == 1

    s = D.run_query("segment_profitability", orders)
    assert set(s["flag"]) >= {"Highest", "Lowest"}


def test_top_customers_and_high_revenue_low_profit(orders):
    t = D.run_query("top_customers_by_revenue", orders, {"limit": 1})

    assert t.loc[0, "customer_name"] in {"Ann", "Bob"}
    assert t.loc[0, "revenue"] == pytest.approx(350)

    D.run_query(
        "high_revenue_low_profit",
        orders,
        {"max_margin_pct": 50.0, "limit": 5}
    )


def test_all_queries_run_on_empty_data(orders):
    empty = orders.iloc[0:0]

    for name in D.available_queries():
        assert isinstance(D.run_query(name, empty), pd.DataFrame)


def test_only_allowlisted_queries_and_valid_params(orders):
    with pytest.raises(ValueError, match="not an approved query"):
        D.run_query("revenue_by_month; DROP TABLE orders", orders)

    with pytest.raises(ValueError, match="not an approved query"):
        D.run_query("SELECT * FROM orders", orders)

    with pytest.raises(ValueError, match="between"):
        D.run_query("top_products_by_profit", orders, {"limit": 100000})

    with pytest.raises(ValueError, match="must be int"):
        D.run_query(
            "top_products_by_profit",
            orders,
            {"limit": "5; DROP TABLE orders"}
        )

    with pytest.raises(ValueError, match="Unknown parameter"):
        D.run_query("top_products_by_profit", orders, {"limit": 5, "evil": 1})

    with pytest.raises(ValueError):
        D.run_query("revenue_by_month", orders, {"limit": 5})


def test_business_insights_are_bounded_and_data_driven(orders):
    ins = A.business_insights(orders, limit=3)

    assert 1 <= len(ins) <= 3
    assert all({"title", "text", "tone"} <= set(i) for i in ins)
    assert A.business_insights(orders.iloc[0:0]) == []


def test_contribution_and_concentration(orders):
    curve = A.contribution_curve(orders)

    assert curve["cum_share_pct"].iloc[-1] == pytest.approx(100)
    assert A.products_for_share(curve, 80)[0] >= 1
    assert A.customer_concentration(orders, 33) == pytest.approx(350 / 800 * 100)
    assert A.customer_concentration(orders, 34) == pytest.approx(650 / 800 * 100)


def test_customer_concentration_validates_percentage(orders):
    with pytest.raises(ValueError, match="between 0 and 100"):
        A.customer_concentration(orders, -5)

    with pytest.raises(ValueError, match="between 0 and 100"):
        A.customer_concentration(orders, 101)


def test_contribution_curve_validates_value(orders):
    with pytest.raises(ValueError, match="sales or profit"):
        A.contribution_curve(orders, value="revenue")
