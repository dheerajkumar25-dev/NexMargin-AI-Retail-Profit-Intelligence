"""Plotly figure builders. One consistent look: indigo = revenue, green = profit/positive, red = negative."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .. import config
from ..formatting import fmt_count, fmt_money, fmt_pct

NAVY, MUTED, GRID, LINE = "#0F172A", "#64748B", "#EEF0F6", "#E6E8F0"
INDIGO, GREEN, RED, AMBER, SLATE = "#4F46E5", "#16A34A", "#DC2626", "#F59E0B", "#94A3B8"
FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"
SEGMENT_COLORS = {"Champions": "#4F46E5", "Loyal Customers": "#818CF8", "Potential Loyalists": "#38BDF8",
                  "At Risk": "#F59E0B", "Lost Customers": "#94A3B8"}
PLOT_CONFIG = {"displayModeBar": False}


def _base(fig: go.Figure, height: int = 320, legend: bool = True, hovermode: str = "closest") -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=4, r=8, t=6, b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=NAVY), hovermode=hovermode, showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=12, color=MUTED), title_text=""),
        hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family=FONT, size=12, color=NAVY)), bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED, size=11), title_text="")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED, size=11), title_text="")
    return fig


def _money_axis(fig: go.Figure, axis: str = "y") -> None:
    upd = fig.update_yaxes if axis == "y" else fig.update_xaxes
    upd(tickprefix=config.CURRENCY_SYMBOL, tickformat="~s")


def _short(s: str, n: int = 34) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def trend_chart(monthly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, name, color in (("revenue", "Revenue", INDIGO), ("profit", "Profit", GREEN)):
        fig.add_trace(go.Scatter(x=monthly["month"], y=monthly[col], name=name, mode="lines", line=dict(color=color, width=2.6, shape="spline", smoothing=0.5),
                                 customdata=[fmt_money(v) for v in monthly[col]], hovertemplate=f"{name}: %{{customdata}}<extra></extra>"))
    _base(fig, 330, hovermode="x unified")
    _money_axis(fig)
    fig.update_xaxes(tickformat="%b %Y", hoverformat="%B %Y")
    return fig


def category_bar(sub: pd.DataFrame, overall_margin: float | None) -> go.Figure:
    d = sub.sort_values("margin_pct").copy()
    low_cut = (overall_margin or 0) * 0.5
    colors = [RED if m < 0 else AMBER if m < low_cut else GREEN for m in d["margin_pct"]]
    fig = go.Figure(go.Bar(
        x=d["margin_pct"], y=d["subcategory"], orientation="h", marker=dict(color=colors, cornerradius=4),
        text=[fmt_pct(m) for m in d["margin_pct"]], textposition="outside", cliponaxis=False, textfont=dict(size=11, color=MUTED),
        customdata=list(zip(d["category"], [fmt_money(v) for v in d["revenue"]], [fmt_money(v) for v in d["profit"]])),
        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Margin: %{x:.1f}%<br>Revenue: %{customdata[1]}<br>Profit: %{customdata[2]}<extra></extra>"))
    if overall_margin is not None:
        fig.add_vline(x=overall_margin, line_dash="dot", line_color=MUTED, line_width=1)
    _base(fig, 440, legend=False)
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(showgrid=False)
    return fig


def region_chart(reg: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, name, color in (("revenue", "Revenue", INDIGO), ("profit", "Profit", GREEN)):
        fig.add_trace(go.Bar(x=reg["region"], y=reg[col], name=name, marker=dict(color=color, cornerradius=4),
                             text=[fmt_money(v) for v in reg[col]], textposition="outside", cliponaxis=False, textfont=dict(size=11, color=MUTED),
                             customdata=[fmt_pct(m) for m in reg["margin_pct"]],
                             hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{text}}<br>Margin: %{{customdata}}<extra></extra>"))
    _base(fig, 330)
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    _money_axis(fig)
    return fig


def hbar(df: pd.DataFrame, label: str, value: str, kind: str = "money", color: str = INDIGO, height: int | None = None,
         hover_cols: list[str] | None = None) -> go.Figure:
    """Horizontal ranked bars; negative values are red. kind: 'money' | 'pct' | 'count'."""
    d = df.iloc[::-1].copy()  # largest at the top
    fmt = {"money": fmt_money, "pct": fmt_pct, "count": fmt_count}[kind]
    colors = [RED if v < 0 else color for v in d[value]]
    full = d[label].astype(str)
    fig = go.Figure(go.Bar(
        x=d[value], y=[_short(s) for s in full], orientation="h", marker=dict(color=colors, cornerradius=4),
        text=[fmt(v) for v in d[value]], textposition="outside", cliponaxis=False, textfont=dict(size=11, color=MUTED),
        customdata=full, hovertemplate="<b>%{customdata}</b><br>%{text}<extra></extra>"))
    _base(fig, height or max(180, 34 * len(d) + 40), legend=False)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, visible=False)
    fig.update_yaxes(showgrid=False, automargin=True)
    return fig


def pareto_chart(curve: pd.DataFrame, share: float = 80.0) -> go.Figure:
    fig = go.Figure(go.Scatter(x=curve["pct_of_products"], y=curve["cum_share_pct"], mode="lines", line=dict(color=INDIGO, width=2.6),
                               fill="tozeroy", fillcolor="rgba(79,70,229,.08)",
                               hovertemplate="Top %{x:.0f}% of products<br>= %{y:.0f}% of total<extra></extra>"))
    fig.add_hline(y=share, line_dash="dot", line_color=MUTED, line_width=1)
    _base(fig, 280, legend=False)
    fig.update_xaxes(ticksuffix="%", title_text="Share of products (ranked high to low)")
    fig.update_yaxes(ticksuffix="%", range=[0, 102])
    return fig


def discount_margin_chart(bands: pd.DataFrame) -> go.Figure:
    colors = [RED if m < 0 else GREEN for m in bands["margin_pct"]]
    fig = go.Figure(go.Bar(x=bands["discount_band"], y=bands["margin_pct"], marker=dict(color=colors, cornerradius=4),
                           text=[fmt_pct(m, 0) for m in bands["margin_pct"]], textposition="outside", cliponaxis=False,
                           textfont=dict(size=11, color=MUTED), customdata=[fmt_int_(v) for v in bands["order_lines"]],
                           hovertemplate="<b>Discount %{x}</b><br>Margin: %{y:.1f}%<br>Order lines: %{customdata}<extra></extra>"))
    _base(fig, 300, legend=False)
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(title_text="Discount given")
    return fig


def fmt_int_(v) -> str:
    return f"{int(v):,}"


def discount_revenue_profit_chart(bands: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, name, color in (("revenue", "Revenue", INDIGO), ("profit", "Profit", GREEN)):
        fig.add_trace(go.Bar(x=bands["discount_band"], y=bands[col], name=name, marker=dict(color=color, cornerradius=4),
                             customdata=[fmt_money(v) for v in bands[col]], hovertemplate=f"{name}: %{{customdata}}<extra></extra>"))
    _base(fig, 300, hovermode="x unified")
    fig.update_layout(barmode="group", bargroupgap=0.08)
    _money_axis(fig)
    fig.update_xaxes(title_text="Discount given")
    return fig


def donut(labels, values, height: int = 280) -> go.Figure:
    palette = [INDIGO, "#818CF8", "#38BDF8", "#A5B4FC", "#C7D2FE", "#94A3B8"]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False, marker=dict(colors=palette[: len(labels)], line=dict(color="white", width=2)),
                           textinfo="percent", textfont=dict(size=12, color="white"), hovertemplate="<b>%{label}</b><br>%{value:,} orders<extra></extra>"))
    _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    return fig


def forecast_chart(res) -> go.Figure:
    h, f, b = res.history, res.forecast, res.backtest
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f["month"], y=f["upper"], mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=f["month"], y=f["lower"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(22,163,74,.12)",
                             name="95% range (approx.)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=h["month"], y=h["revenue"], name="Actual revenue", mode="lines", line=dict(color=INDIGO, width=2.6),
                             customdata=[fmt_money(v) for v in h["revenue"]], hovertemplate="Actual: %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(x=b["month"], y=b["model"], name="Model on held-out months", mode="markers",
                             marker=dict(color=AMBER, size=7), customdata=[fmt_money(v) for v in b["model"]],
                             hovertemplate="Model (held-out): %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(x=f["month"], y=f["forecast"], name="Forecast", mode="lines+markers", line=dict(color=GREEN, width=2.6, dash="dash"),
                             marker=dict(size=6), customdata=[fmt_money(v) for v in f["forecast"]], hovertemplate="Forecast: %{customdata}<extra></extra>"))
    _base(fig, 340, hovermode="x unified")
    _money_axis(fig)
    fig.update_xaxes(tickformat="%b %Y")
    return fig


def rfm_chart(summary: pd.DataFrame) -> go.Figure:
    d = summary.iloc[::-1]
    fig = go.Figure(go.Bar(x=d["customers"], y=d["segment"], orientation="h",
                           marker=dict(color=[SEGMENT_COLORS.get(s, SLATE) for s in d["segment"]], cornerradius=4),
                           text=[f"{int(c):,}  ({p:.0f}%)" for c, p in zip(d["customers"], d["customers_pct"])], textposition="outside", cliponaxis=False,
                           textfont=dict(size=11, color=MUTED), hovertemplate="<b>%{y}</b><br>%{x:,} customers<extra></extra>"))
    _base(fig, 280, legend=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=False)
    return fig


def count_bar(df: pd.DataFrame, x: str, y: str, hover_label: str = "customers", height: int = 280) -> go.Figure:
    fig = go.Figure(go.Bar(x=df[x], y=df[y], marker=dict(color=INDIGO, cornerradius=4), text=[f"{int(v):,}" for v in df[y]],
                           textposition="outside", cliponaxis=False, textfont=dict(size=11, color=MUTED),
                           hovertemplate=f"<b>%{{x}}</b><br>%{{y:,}} {hover_label}<extra></extra>"))
    _base(fig, height, legend=False)
    return fig


def retention_chart(ret: pd.DataFrame) -> go.Figure:
    labels = [f"{a} to {b}" for a, b in zip(ret["year"], ret["next_year"])]
    fig = go.Figure(go.Bar(x=labels, y=ret["retention_pct"], marker=dict(color=GREEN, cornerradius=4),
                           text=[fmt_pct(v, 0) for v in ret["retention_pct"]], textposition="outside", cliponaxis=False,
                           textfont=dict(size=11, color=MUTED),
                           customdata=list(zip(ret["retained"], ret["customers"])),
                           hovertemplate="<b>%{x}</b><br>%{customdata[0]} of %{customdata[1]} customers returned<extra></extra>"))
    _base(fig, 280, legend=False)
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    return fig
