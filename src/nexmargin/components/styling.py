"""Global CSS and small HTML helpers that give NexMargin its look."""
from __future__ import annotations

import html

import streamlit as st

NAVY, MUTED, LINE, INDIGO = "#0F172A", "#64748B", "#E6E8F0", "#4F46E5"
GREEN, RED, AMBER = "#16A34A", "#DC2626", "#F59E0B"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --nx-bg: #F6F7FB;
    --nx-text: #0F172A;
    --nx-muted: #64748B;
    --nx-line: #E6E8F0;
    --nx-indigo: #4F46E5;
    --nx-indigo-soft: #EEF2FF;
    --nx-green: #16A34A;
    --nx-green-soft: #DCFCE7;
    --nx-red: #DC2626;
    --nx-red-soft: #FEE2E2;
    --nx-amber: #F59E0B;
    --nx-amber-soft: #FEF3C7;
}

.stApp, .stApp p, .stApp label, .stApp input,
.stApp button, .stApp textarea, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp li, .stApp td, .stApp th {
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
}

.stApp {
    background: var(--nx-bg);
    color: var(--nx-text);
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* IMPORTANT: Preserve Streamlit toolbar and sidebar controls.
   Hide only individual unwanted elements. */
[data-testid="stMainMenu"],
[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],
footer {
    display: none !important;
}

/* Main content */
.block-container {
    padding: 1.6rem 2.2rem 3rem;
    max-width: 1320px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid var(--nx-line);
}

[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarContent"] {
    padding-top: 1.1rem;
}

.nx-brand {
    display: flex;
    align-items: center;
    gap: .65rem;
    padding: .2rem .4rem 1.1rem;
}

.nx-logo {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, #4F46E5, #6366F1);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.05rem;
}

.nx-brand-name {
    font-weight: 700;
    font-size: 1.08rem;
    letter-spacing: -.01em;
    line-height: 1.1;
}

.nx-brand-tag {
    font-size: .7rem;
    color: var(--nx-muted);
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    width: 100%;
    justify-content: flex-start;
    border: none;
    border-radius: 10px;
    padding: .55rem .8rem;
    font-weight: 500;
    box-shadow: none;
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: transparent;
    color: var(--nx-muted);
}

[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: #F3F4F8;
    color: var(--nx-text);
}

[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: var(--nx-indigo-soft);
    color: var(--nx-indigo);
}

[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p {
    font-weight: 600;
}

.nx-side-note {
    font-size: .74rem;
    color: var(--nx-muted);
    line-height: 1.5;
    padding: 0 .5rem;
}

.nx-status {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-size: .74rem;
    font-weight: 500;
    padding: .25rem .6rem;
    border-radius: 999px;
}

.nx-status.on {
    background: var(--nx-green-soft);
    color: #166534;
}

.nx-status.off {
    background: #F1F5F9;
    color: var(--nx-muted);
}

.nx-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}

/* Page header */
.nx-title {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -.02em;
    margin: 0;
    line-height: 1.2;
}

.nx-sub {
    color: var(--nx-muted);
    font-size: .93rem;
    margin: .2rem 0 1.1rem;
}

/* Filters */
.stApp [data-testid="stWidgetLabel"] p {
    font-size: .76rem;
    font-weight: 500;
    color: var(--nx-muted);
}

.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="input"],
.stApp [data-baseweb="base-input"] {
    border-radius: 10px;
    border-color: var(--nx-line);
    background: #FFFFFF;
}

.stApp [data-testid="stDateInput"] div[data-baseweb="input"] {
    border-radius: 10px;
}

/* Cards */
[class*="st-key-card"] {
    background: #FFFFFF;
    border: 1px solid var(--nx-line);
    border-radius: 16px;
    padding: 1.05rem 1.25rem 1rem;
    box-shadow: 0 1px 2px rgba(15,23,42,.04),
                0 6px 16px rgba(15,23,42,.03);
}

.nx-card-title {
    font-weight: 600;
    font-size: .98rem;
    margin: 0;
}

.nx-card-sub {
    color: var(--nx-muted);
    font-size: .8rem;
    margin: .1rem 0 .4rem;
}

.nx-legend {
    display: flex;
    gap: .9rem;
    font-size: .76rem;
    color: var(--nx-muted);
    margin: .1rem 0 .3rem;
}

.nx-legend i {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: .35rem;
}

/* KPI cards */
.nx-kpi {
    position: relative;
    background: #FFFFFF;
    border: 1px solid var(--nx-line);
    border-radius: 16px;
    padding: 1rem 1.15rem .95rem;
    box-shadow: 0 1px 2px rgba(15,23,42,.04),
                0 6px 16px rgba(15,23,42,.03);
    min-height: 128px;
    overflow: hidden;
}

.nx-kpi.compact {
    min-height: 96px;
    padding: .8rem 1rem;
}

.nx-kpi-label {
    font-size: .8rem;
    font-weight: 500;
    color: var(--nx-muted);
}

.nx-kpi-value {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -.025em;
    line-height: 1.15;
    margin: .2rem 0 .45rem;
    font-variant-numeric: tabular-nums;
}

.nx-kpi.compact .nx-kpi-value {
    font-size: 1.5rem;
    margin: .1rem 0 .3rem;
}

.nx-kpi-foot {
    display: flex;
    align-items: center;
    gap: .5rem;
    font-size: .76rem;
    color: var(--nx-muted);
}

.nx-delta {
    font-weight: 600;
    padding: .12rem .5rem;
    border-radius: 999px;
    font-size: .74rem;
    font-variant-numeric: tabular-nums;
}

.nx-delta.up {
    background: var(--nx-green-soft);
    color: #166534;
}

.nx-delta.down {
    background: var(--nx-red-soft);
    color: #991B1B;
}

.nx-delta.flat, .nx-delta.none {
    background: #F1F5F9;
    color: var(--nx-muted);
    font-weight: 500;
}

.nx-spark {
    position: absolute;
    right: 1rem;
    top: 1rem;
    opacity: .95;
}

/* Insights */
.nx-insight {
    padding: .7rem .85rem;
    border-radius: 12px;
    margin: .45rem 0;
    border: 1px solid var(--nx-line);
    background: #FBFBFD;
}

.nx-insight .t {
    font-weight: 600;
    font-size: .86rem;
    margin-bottom: .15rem;
}

.nx-insight .d {
    font-size: .8rem;
    color: #334155;
    line-height: 1.45;
}

.nx-insight.neg {
    border-left: 3px solid var(--nx-red);
}

.nx-insight.pos {
    border-left: 3px solid var(--nx-green);
}

.nx-insight.info {
    border-left: 3px solid var(--nx-indigo);
}

.nx-callout {
    background: var(--nx-red-soft);
    border: 1px solid #FECACA;
    color: #7F1D1D;
    border-radius: 14px;
    padding: .8rem 1rem;
    font-size: .9rem;
    margin-bottom: .8rem;
}

.nx-callout.good {
    background: var(--nx-green-soft);
    border-color: #BBF7D0;
    color: #14532D;
}

.nx-stat-label {
    font-size: .76rem;
    color: var(--nx-muted);
}

.nx-stat-value {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -.02em;
}

.nx-badge {
    display: inline-block;
    font-size: .72rem;
    font-weight: 600;
    padding: .15rem .55rem;
    border-radius: 999px;
    background: var(--nx-indigo-soft);
    color: var(--nx-indigo);
}

.nx-badge.muted {
    background: #F1F5F9;
    color: var(--nx-muted);
}

.nx-badge.warn {
    background: var(--nx-amber-soft);
    color: #92400E;
}

/* Tabs */
.stApp [data-baseweb="tab-list"] {
    gap: .4rem;
    border-bottom: 1px solid var(--nx-line);
}

.stApp button[data-baseweb="tab"] {
    font-weight: 500;
    color: var(--nx-muted);
    padding: .5rem .9rem;
}

.stApp button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--nx-indigo);
}

.stApp [data-baseweb="tab-highlight"] {
    background: var(--nx-indigo);
}

/* Main area buttons */
.stApp [data-testid="stMain"] [data-testid="stBaseButton-primary"],
.stApp [data-testid="stMain"] [data-testid="stDownloadButton"] button[kind="primary"] {
    background: var(--nx-indigo);
    border: 1px solid var(--nx-indigo);
    color: #FFFFFF;
    border-radius: 10px;
    font-weight: 600;
}

.stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"] {
    border-radius: 10px;
    border: 1px solid var(--nx-line);
    background: #FFFFFF;
    font-weight: 500;
}

.stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--nx-indigo);
    color: var(--nx-indigo);
}

/* Chat */
[data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid var(--nx-line);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: .8rem;
}

[data-testid="stChatInput"] {
    border-radius: 14px;
}

.nx-scope {
    font-size: .74rem;
    color: var(--nx-muted);
    margin-top: .5rem;
}

.nx-hero {
    text-align: center;
    padding: 1.6rem 0 .8rem;
}

.nx-hero h2 {
    font-size: 1.35rem;
    font-weight: 700;
    margin: .2rem 0;
}

.nx-hero p {
    color: var(--nx-muted);
    font-size: .9rem;
    margin: 0;
}

/* Tables and expanders */
[data-testid="stDataFrame"] {
    border: 1px solid var(--nx-line);
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stExpander"] {
    border: 1px solid var(--nx-line);
    border-radius: 12px;
    background: #FFFFFF;
}

/* Responsive layout */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 1rem 2rem;
    }

    .nx-title {
        font-size: 1.45rem;
    }

    .nx-kpi-value {
        font-size: 1.55rem;
    }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="nx-title">{html.escape(title)}</div>'
        f'<div class="nx-sub">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def card_header(title: str, subtitle: str = "") -> None:
    sub = (
        f'<div class="nx-card-sub">{html.escape(subtitle)}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div class="nx-card-title">{html.escape(title)}</div>{sub}',
        unsafe_allow_html=True,
    )


def legend(items: list[tuple[str, str]]) -> None:
    dots = "".join(
        f'<span><i style="background:{c}"></i>{html.escape(t)}</span>'
        for t, c in items
    )
    st.markdown(
        f'<div class="nx-legend">{dots}</div>',
        unsafe_allow_html=True,
    )


def card(name: str):
    """A white content card. Use as a context manager."""
    return st.container(key=f"card_{name}")


def stat(label: str, value: str) -> None:
    st.markdown(
        f'<div class="nx-stat-label">{html.escape(label)}</div>'
        f'<div class="nx-stat-value">{html.escape(value)}</div>',
        unsafe_allow_html=True,
    )


def empty_state() -> None:
    st.info(
        "No orders match these filters. Widen the date range "
        "or clear a filter to see results."
    )


def insight_html(ins: dict) -> str:
    return (
        f'<div class="nx-insight {ins["tone"]}">'
        f'<div class="t">{html.escape(ins["title"])}</div>'
        f'<div class="d">{html.escape(ins["text"])}</div></div>'
    )