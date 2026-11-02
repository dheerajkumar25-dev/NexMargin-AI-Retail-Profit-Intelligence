"""Tests for the cleaning pipeline: validation, edge cases, and derived fields."""
import pandas as pd
import pytest

from nexmargin import config
from nexmargin.preprocessing import RENAME, clean


def make_raw(rows: list[dict] | None = None) -> pd.DataFrame:
    base = {
        "Row ID": 1, "Order ID": "CA-1", "Order Date": "11/8/2016", "Ship Date": "11/11/2016",
        "Ship Mode": "Second Class", "Customer ID": "C-1", "Customer Name": "Ann", "Segment": "Consumer",
        "Country": "United States", "City": "X", "State": "Y", "Postal Code": 1, "Region": "West",
        "Product ID": "P-1", "Category": "Furniture", "Sub-Category": "Chairs", "Product Name": "Chair",
        "Sales": 100.0, "Quantity": 2, "Discount": 0.1, "Profit": 20.0,
    }
    rows = rows or [{}]
    out = []
    for i, r in enumerate(rows, start=1):
        out.append({**base, "Row ID": i, "Order ID": f"CA-{i}", **r})
    return pd.DataFrame(out)


def test_clean_valid_row_and_derived_fields():
    df, rep = clean(make_raw())
    assert len(df) == 1 and rep["rows_clean"] == 1
    assert df.loc[0, "cost"] == pytest.approx(80.0)  # sales - profit
    assert df.loc[0, "discount_pct"] == pytest.approx(10.0)
    assert df.loc[0, "order_month"] == pd.Timestamp("2016-11-01")
    assert not df.loc[0, "is_loss"]


def test_loss_flag():
    df, _ = clean(make_raw([{"Profit": -5.0}]))
    assert bool(df.loc[0, "is_loss"]) and df.loc[0, "cost"] == pytest.approx(105.0)


def test_duplicates_removed_ignoring_row_id():
    raw = make_raw([{}, {}])
    raw["Order ID"] = "CA-1"  # identical records, different Row ID
    df, rep = clean(raw)
    assert len(df) == 1 and rep["rows_removed"]["duplicate_records"] == 1


def test_invalid_dates_are_dropped_and_counted():
    df, rep = clean(make_raw([{"Order Date": "not-a-date"}, {}]))
    assert len(df) == 1 and rep["rows_removed"]["invalid_order_date"] == 1


def test_null_sales_and_missing_keys_removed():
    raw = make_raw([{"Sales": None}, {"Customer ID": None}, {}])
    df, rep = clean(raw)
    assert len(df) == 1
    assert rep["rows_removed"]["missing_sales_or_profit"] == 1
    assert rep["rows_removed"]["missing_key_field"] == 1


@pytest.mark.parametrize("col,val,reason", [
    ("Discount", 1.5, "invalid_discount"),
    ("Discount", -0.1, "invalid_discount"),
    ("Quantity", 0, "invalid_quantity"),
    ("Sales", -1.0, "negative_sales"),
])
def test_invalid_values_removed(col, val, reason):
    df, rep = clean(make_raw([{col: val}]))
    assert len(df) == 0 and rep["rows_removed"][reason] == 1


def test_zero_sales_row_is_kept():
    df, _ = clean(make_raw([{"Sales": 0.0, "Profit": 0.0}]))
    assert len(df) == 1


def test_empty_input_does_not_crash():
    df, rep = clean(make_raw().iloc[0:0])
    assert df.empty and rep["rows_clean"] == 0 and rep["date_range"] is None


def test_missing_column_raises():
    with pytest.raises(ValueError, match="missing required columns"):
        clean(make_raw().drop(columns=["Profit"]))


def test_product_name_is_canonicalised_per_product_id():
    raw = make_raw([{"Product Name": "Chair"}, {"Product Name": "Chair"}, {"Product Name": "Chair (v2)"}])
    df, rep = clean(raw)
    assert df["product_name"].nunique() == 1 and df["product_name"].iloc[0] == "Chair"
    assert rep["product_ids_with_multiple_names"] == 1


def test_whitespace_is_trimmed():
    df, _ = clean(make_raw([{"Region": "  West "}]))
    assert df.loc[0, "region"] == "West"


@pytest.mark.skipif(not config.RAW_FILE.exists(), reason="raw dataset not downloaded")
def test_real_dataset_reconciles():
    raw = pd.read_csv(config.RAW_FILE, encoding="latin1")
    df, rep = clean(raw)
    assert rep["rows_raw"] == len(raw)
    assert rep["rows_clean"] + sum(rep["rows_removed"].values()) == rep["rows_raw"]
    # Totals reconcile exactly once the removed duplicate lines are excluded from the raw data.
    dup = raw.duplicated(subset=[c for c in raw.columns if c != "Row ID"])
    assert rep["rows_removed"]["duplicate_records"] == int(dup.sum())
    assert df["profit"].sum() == pytest.approx(raw.loc[~dup, "Profit"].sum())
    assert df["sales"].sum() == pytest.approx(raw.loc[~dup, "Sales"].sum())
    assert set(RENAME.values()) <= set(df.columns)

def test_duplicate_columns_raise_error():
    raw = make_raw()
    raw.columns = list(raw.columns[:-1]) + [raw.columns[0]]

    with pytest.raises(ValueError, match="duplicate columns"):
        clean(raw)