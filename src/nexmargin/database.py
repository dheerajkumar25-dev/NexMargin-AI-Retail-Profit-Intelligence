"""DuckDB access layer.

Safety model: only queries stored in sql/business_queries.sql can run, selected by NAME.
Parameters are type- and range-validated and bound with ? placeholders. No SQL text ever
comes from the UI or from an LLM. Filtering happens in pandas before the data is registered.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

from . import config

SQL_FILE = config.ROOT / "sql" / "business_queries.sql"
_NAME_RE = re.compile(r"^--\s*name:\s*(\w+)\s*$", re.M)

# name -> ordered parameter specs: (param, type, min, max, default)
QUERY_PARAMS: dict[str, list[tuple]] = {
    "top_products_by_profit": [("limit", int, 1, 100, 10)],
    "top_customers_by_revenue": [("limit", int, 1, 100, 10)],
    "high_revenue_low_profit": [("max_margin_pct", float, -100.0, 100.0, 5.0), ("limit", int, 1, 100, 10)],
}
ORDER_COLUMNS = [
    "order_id", "order_date", "order_month", "order_year", "customer_id", "customer_name", "segment",
    "region", "product_id", "product_name", "category", "subcategory", "sales", "quantity",
    "discount", "discount_pct", "profit", "cost",
]


@lru_cache(maxsize=1)
def load_queries(path: str = str(SQL_FILE)) -> dict[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    parts = _NAME_RE.split(text)  # ['', name1, body1, name2, body2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def available_queries() -> list[str]:
    return sorted(load_queries())


def connect(df: pd.DataFrame) -> duckdb.DuckDBPyConnection:
    """In-memory connection with `orders` plus customer and product dimension views."""
    con = duckdb.connect(":memory:")
    src = df[ORDER_COLUMNS]
    con.register("orders_src", src)
    con.execute("CREATE VIEW orders AS SELECT * FROM orders_src")
    con.execute("""CREATE VIEW dim_customers AS
        SELECT customer_id, ANY_VALUE(customer_name) AS customer_name, ANY_VALUE(segment) AS segment,
               MIN(order_date) AS first_order_date FROM orders GROUP BY customer_id""")
    con.execute("""CREATE VIEW dim_products AS
        SELECT product_id, ANY_VALUE(product_name) AS product_name, ANY_VALUE(category) AS category,
               ANY_VALUE(subcategory) AS subcategory FROM orders GROUP BY product_id""")
    return con


def _validate_params(name: str, params: dict | None) -> list:
    params = dict(params or {})
    specs = QUERY_PARAMS.get(name, [])
    unknown = set(params) - {s[0] for s in specs}
    if unknown:
        raise ValueError(f"Unknown parameter(s) for {name}: {sorted(unknown)}")
    values = []
    for pname, ptype, lo, hi, default in specs:
        raw = params.get(pname, default)
        try:
            val = ptype(raw)
        except (TypeError, ValueError):
            raise ValueError(f"Parameter '{pname}' must be {ptype.__name__}, got {raw!r}") from None
        if isinstance(raw, bool) or not (lo <= val <= hi):
            raise ValueError(f"Parameter '{pname}' must be between {lo} and {hi}, got {raw!r}")
        values.append(val)
    return values


def run_query(name: str, df: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
    """Run an allowlisted query by name against `df`."""
    queries = load_queries()
    if name not in queries:
        raise ValueError(f"Query '{name}' is not an approved query. Approved: {available_queries()}")
    values = _validate_params(name, params)
    con = connect(df)
    try:
        return con.execute(queries[name], values).df()
    finally:
        con.close()
