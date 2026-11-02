import io
import zipfile

import pandas as pd
import pytest

from nexmargin import config
from nexmargin import report_generator as R


def test_pdf_is_valid_and_contains_content(orders):
    pdf = R.build_pdf(orders, "All data", "Revenue was $800.", "Demo mode")
    assert pdf[:5] == b"%PDF-" and len(pdf) > 3000
    from pypdf import PdfReader
    text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    for s in ("NexMargin", "Profit Intelligence Report", "$800", "Auto-generated", "Furniture", "East"):
        assert s in text


def test_pdf_labels_ai_summary(orders):
    from pypdf import PdfReader
    pdf = R.build_pdf(orders, "x", "Summary text.", "AI explanation")
    assert "AI-generated summary" in " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)


def test_pdf_handles_empty_selection_and_rupee_symbol(orders, monkeypatch):
    assert R.build_pdf(orders.iloc[0:0], "none")[:5] == b"%PDF-"
    monkeypatch.setattr(config, "CURRENCY_SYMBOL", "₹")
    assert R.build_pdf(orders, "rupee test")[:5] == b"%PDF-"


def test_csv_export_matches_filtered_data(orders):
    west = orders[orders["region"] == "West"]
    out = pd.read_csv(io.BytesIO(R.filtered_csv(west)))
    assert len(out) == len(west) and list(out.columns) == R.EXPORT_COLUMNS
    assert out["sales"].sum() == pytest.approx(west["sales"].sum())


def test_summary_zip_contents(orders):
    z = zipfile.ZipFile(io.BytesIO(R.summary_zip(orders)))
    assert {"kpis.csv", "by_region.csv", "by_category.csv", "monthly_trend.csv", "discount_bands.csv"} <= set(z.namelist())
    kpis = pd.read_csv(io.BytesIO(z.read("kpis.csv")))
    assert kpis.loc[0, "revenue"] == pytest.approx(800)
    assert R.summary_zip(orders.iloc[0:0])  # empty selection still produces a zip
