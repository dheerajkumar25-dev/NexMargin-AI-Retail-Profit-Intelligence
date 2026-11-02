"""End-to-end UI tests using Streamlit's AppTest against the real processed dataset."""
import pytest

from nexmargin import config, metrics as M
from nexmargin.formatting import fmt_money

if not (config.PROCESSED_FILE.exists() or config.RAW_FILE.exists()):
    pytest.skip("dataset not available; run scripts/build_data.py", allow_module_level=True)

from streamlit.testing.v1 import AppTest

from nexmargin.data_loader import load_processed

APP = str(config.ROOT / "app.py")
PAGES = ["Overview", "Explore", "AI Copilot", "Reports"]


def _app(page="Overview"):
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["page"] = page
    return at.run()


def _text(at):
    return " ".join(m.value for m in at.markdown)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_without_error(page):
    at = _app(page)
    assert not at.exception, [e.value for e in at.exception]


def test_overview_kpis_are_correct_and_react_to_region_filter():
    df = load_processed()
    at = _app("Overview")
    assert fmt_money(M.revenue(df)) in _text(at) and fmt_money(M.profit(df)) in _text(at)
    at.multiselect(key="ov_region").select("West").run()
    west = df[df["region"] == "West"]
    t = _text(at)
    assert not at.exception
    assert fmt_money(M.revenue(west)) in t and fmt_money(M.profit(west)) in t


def test_overview_shows_no_fake_comparison_for_full_range():
    assert "No prior-period comparison" in " ".join(c.value for c in _app("Overview").caption)


def test_explore_filters_update_kpis():
    df = load_processed()
    at = _app("Explore")
    at.multiselect(key="ex_cat").select("Furniture").run()
    assert not at.exception
    assert fmt_money(M.revenue(df[df["category"] == "Furniture"])) in _text(at)


def test_filters_with_no_matching_rows_show_empty_state():
    import datetime as dt
    import pandas as pd
    df = load_processed()
    days = pd.date_range(df["order_date"].min(), df["order_date"].max(), freq="D")
    empty_day = next(d for d in days if d not in set(df["order_date"])).date()   # a day inside the data range with no orders
    at = _app("Overview")
    at.date_input(key="ov_date").set_value((empty_day, empty_day)).run()
    assert not at.exception and any("No orders match" in i.value for i in at.info)


def test_copilot_suggested_question_flow_in_demo_mode(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    at = _app("AI Copilot")
    at.button(key="sq_4").click().run()
    assert not at.exception
    hist = at.session_state["copilot_history"]
    assert len(hist) == 1 and hist[0].intent == "discount_impact" and hist[0].mode == "Demo mode"
    assert "Data used:" in _text(at)


def test_copilot_free_text_and_rejects_empty():
    at = _app("AI Copilot")
    at.chat_input[0].set_value("Which products have the lowest profit margin?").run()
    assert not at.exception and at.session_state["copilot_history"][0].intent == "lowest_margin_products"


def test_reports_page_offers_downloads_and_ai_disabled_without_key(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    at = _app("Reports")
    assert not at.exception
    assert at.button(key="rp_ai").disabled
