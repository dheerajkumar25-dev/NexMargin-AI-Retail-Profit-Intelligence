"""Column formatting for st.dataframe tables (values stay numeric so columns remain sortable)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import config

MONEY = {"revenue", "profit", "sales", "cost", "aov", "monetary", "current", "previous", "change"}
PCT = {"margin_pct", "revenue_share_pct", "profit_share_pct", "customers_pct", "avg_discount_pct", "discount_pct", "loss_line_pct", "retention_pct"}


def column_config(df: pd.DataFrame) -> dict:
    sym = config.CURRENCY_SYMBOL
    money_fmt = "dollar" if sym == "$" else f"{sym}%.0f"
    cfg = {}
    for c in df.columns:
        label = c.replace("_pct", " %").replace("_", " ").capitalize()
        if c in MONEY:
            cfg[c] = st.column_config.NumberColumn(label, format=money_fmt)
        elif c in PCT:
            cfg[c] = st.column_config.NumberColumn(label, format="%.1f%%")
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            cfg[c] = st.column_config.DateColumn(label, format="YYYY-MM-DD")
        elif pd.api.types.is_float_dtype(df[c]):
            cfg[c] = st.column_config.NumberColumn(label, format="%.1f")
        else:
            cfg[c] = st.column_config.Column(label)
    return cfg


def show(df: pd.DataFrame, height: int | None = None) -> None:
    """Sortable table. Fixed pixel height when given, otherwise sized to its content (capped by Streamlit)."""
    kwargs = {"height": height} if height else {}
    st.dataframe(df, column_config=column_config(df), hide_index=True, width="stretch", **kwargs)
