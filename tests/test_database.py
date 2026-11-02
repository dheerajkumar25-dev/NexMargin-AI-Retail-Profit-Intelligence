import pytest

from nexmargin import database as D


def test_connection_creates_required_views(orders):
    con = D.connect(orders)

    try:
        order_count = con.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        customer_count = con.execute(
            "SELECT COUNT(*) FROM dim_customers"
        ).fetchone()[0]

        product_count = con.execute(
            "SELECT COUNT(*) FROM dim_products"
        ).fetchone()[0]

        assert order_count == len(orders)
        assert customer_count == orders["customer_id"].nunique()
        assert product_count == orders["product_id"].nunique()
    finally:
        con.close()


def test_available_queries_returns_expected_queries():
    queries = D.available_queries()

    expected = {
        "top_products_by_profit",
        "revenue_by_month",
        "margin_by_category",
        "margin_by_subcategory",
        "region_performance",
        "customer_purchase_frequency",
        "discount_impact",
        "monthly_growth",
        "segment_profitability",
        "top_customers_by_revenue",
        "high_revenue_low_profit",
    }

    assert expected.issubset(set(queries))
    assert queries == sorted(queries)


def test_query_loader_reads_custom_sql_file(tmp_path):
    sql_file = tmp_path / "queries.sql"
    sql_file.write_text(
        "-- name: sample_query\nSELECT 1;\n",
        encoding="utf-8",
    )

    queries = D.load_queries(str(sql_file))

    assert queries == {"sample_query": "SELECT 1;"}


def test_boolean_parameter_is_rejected(orders):
    with pytest.raises(ValueError, match="between"):
        D.run_query("top_products_by_profit", orders, {"limit": True})


def test_parameter_outside_allowed_range_is_rejected(orders):
    with pytest.raises(ValueError, match="between"):
        D.run_query("top_products_by_profit", orders, {"limit": 101})


def test_database_connection_closes_after_query_failure(monkeypatch, orders):
    class FakeConnection:
        closed = False

        def execute(self, query, params):
            raise RuntimeError("Simulated query failure")

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()
    monkeypatch.setattr(D, "connect", lambda df: fake_connection)

    with pytest.raises(RuntimeError, match="Simulated query failure"):
        D.run_query("revenue_by_month", orders)

    assert fake_connection.closed