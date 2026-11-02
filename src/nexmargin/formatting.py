"""Number formatting shared by the UI, charts, AI answers and PDF reports."""
from __future__ import annotations

import math

from . import config


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def fmt_money(v, symbol: str | None = None) -> str:
    """Compact money: $2.30M, $286.4K, $842."""
    if _missing(v):
        return "n/a"
    s = config.CURRENCY_SYMBOL if symbol is None else symbol
    a, sign = abs(float(v)), "-" if v < 0 else ""
    if a >= 1e6:
        return f"{sign}{s}{a / 1e6:.2f}M"
    if a >= 1e3:
        return f"{sign}{s}{a / 1e3:.1f}K"
    return f"{sign}{s}{a:,.0f}"


def fmt_money_full(v, symbol: str | None = None) -> str:
    if _missing(v):
        return "n/a"
    s = config.CURRENCY_SYMBOL if symbol is None else symbol
    return f"{'-' if v < 0 else ''}{s}{abs(float(v)):,.0f}"


def fmt_pct(v, decimals: int = 1) -> str:
    return "n/a" if _missing(v) else f"{float(v):.{decimals}f}%"


def fmt_int(v) -> str:
    return "n/a" if _missing(v) else f"{int(round(float(v))):,}"


def fmt_count(v) -> str:
    """Compact count: 5,009 or 12.4K."""
    if _missing(v):
        return "n/a"
    return f"{float(v) / 1e3:.1f}K" if abs(v) >= 10_000 else fmt_int(v)


def fmt_delta_pct(v) -> str:
    return "n/a" if _missing(v) else f"{float(v):+.1f}%"
