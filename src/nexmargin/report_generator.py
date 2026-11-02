"""PDF report, CSV and summary exports. PDF charts use reportlab's own graphics (no browser/kaleido needed)."""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

import pandas as pd
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import analytics as A
from . import metrics
from .formatting import fmt_int, fmt_money, fmt_money_full, fmt_pct

INDIGO, NAVY, GREEN, RED = colors.HexColor("#4F46E5"), colors.HexColor("#0F172A"), colors.HexColor("#16A34A"), colors.HexColor("#DC2626")
MUTED, LINE, SOFT = colors.HexColor("#64748B"), colors.HexColor("#E2E8F0"), colors.HexColor("#F1F5F9")

EXPORT_COLUMNS = ["order_id", "order_date", "customer_id", "customer_name", "segment", "region", "category", "subcategory",
                  "product_id", "product_name", "quantity", "sales", "discount_pct", "cost", "profit"]


def _safe(text: str) -> str:
    """Helvetica has no rupee glyph; keep the PDF readable for any currency symbol."""
    return str(text).replace("₹", "Rs ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def filtered_csv(df: pd.DataFrame) -> bytes:
    return df[EXPORT_COLUMNS].to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")


def summary_zip(df: pd.DataFrame) -> bytes:
    """A zip of analytical summary tables (CSV) for the filtered data."""
    tables = {
        "kpis.csv": pd.DataFrame([metrics.kpis(df)]),
        "monthly_trend.csv": metrics.monthly_series(df),
        "by_category.csv": metrics.group_summary(df, "category"),
        "by_subcategory.csv": metrics.group_summary(df, ["category", "subcategory"]),
        "by_region.csv": metrics.group_summary(df, "region"),
        "by_segment.csv": metrics.group_summary(df, "segment"),
        "discount_bands.csv": A.discount_bands(df) if len(df) else pd.DataFrame(),
        "top_products_by_profit.csv": A.top_products_by_profit(df, 10) if len(df) else pd.DataFrame(),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, t in tables.items():
            z.writestr(name, t.to_csv(index=False))
    return buf.getvalue()


# ------------------------------------------------------------------ PDF
def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=NAVY, alignment=0, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontSize=9, textColor=MUTED, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, textColor=NAVY, spaceBefore=12, spaceAfter=5),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=9.5, leading=14, textColor=NAVY),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=7.5, leading=10, textColor=MUTED),
    }


def _table(rows, col_widths, align_right_from=1, neg_cols=()):
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5), ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
             ("FONT", (0, 1), (-1, -1), "Helvetica", 9), ("TEXTCOLOR", (0, 1), (-1, -1), NAVY),
             ("LINEBELOW", (0, 0), (-1, 0), 0.8, LINE), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
             ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for r, row in enumerate(rows[1:], start=1):
        for c in neg_cols:
            if str(row[c]).startswith("-"):
                style.append(("TEXTCOLOR", (c, r), (c, r), RED))
    t.setStyle(TableStyle(style))
    return t


def _trend_drawing(monthly: pd.DataFrame, width: float, height: float = 150) -> Drawing:
    d = Drawing(width, height)
    if len(monthly) < 2:
        d.add(String(10, height / 2, "Not enough months to draw a trend.", fontSize=9, fillColor=MUTED))
        return d
    lp = LinePlot()
    lp.x, lp.y, lp.width, lp.height = 48, 22, width - 64, height - 38
    lp.data = [[(i, float(v)) for i, v in enumerate(monthly["revenue"])], [(i, float(v)) for i, v in enumerate(monthly["profit"])]]
    lp.lines[0].strokeColor, lp.lines[0].strokeWidth = INDIGO, 1.8
    lp.lines[1].strokeColor, lp.lines[1].strokeWidth = GREEN, 1.8
    lp.xValueAxis.valueMin, lp.xValueAxis.valueMax = 0, len(monthly) - 1
    step = max(1, len(monthly) // 6)
    lp.xValueAxis.valueSteps = list(range(0, len(monthly), step))
    labels = {i: monthly["month"].iloc[i].strftime("%b %y") for i in range(len(monthly))}
    lp.xValueAxis.labelTextFormat = lambda v: labels.get(int(round(v)), "")
    lp.yValueAxis.labelTextFormat = lambda v: fmt_money(v)
    for ax in (lp.xValueAxis, lp.yValueAxis):
        ax.labels.fontSize, ax.labels.fillColor = 7, MUTED
    lp.yValueAxis.gridStrokeColor, lp.yValueAxis.visibleGrid, lp.yValueAxis.gridStrokeWidth = LINE, 1, 0.4
    d.add(lp)
    d.add(String(48, height - 10, "Revenue", fontSize=8, fillColor=INDIGO))
    d.add(String(100, height - 10, "Profit", fontSize=8, fillColor=GREEN))
    return d


def _margin_bars(sub: pd.DataFrame, width: float) -> Drawing:
    sub = sub.sort_values("margin_pct")
    h = 14 * len(sub) + 30
    d = Drawing(width, h)
    bc = HorizontalBarChart()
    bc.x, bc.y, bc.width, bc.height = 95, 12, width - 130, h - 24
    bc.data = [[float(v) for v in sub["margin_pct"]]]
    bc.categoryAxis.categoryNames = list(sub["subcategory"])
    bc.categoryAxis.labels.fontSize = bc.valueAxis.labels.fontSize = 7
    bc.categoryAxis.labels.fillColor = bc.valueAxis.labels.fillColor = MUTED
    bc.valueAxis.labelTextFormat = lambda v: f"{v:.0f}%"
    bc.categoryAxis.labelAxisMode = "low"   # keep labels left of negative bars
    bc.categoryAxis.labels.dx = -4
    bc.categoryAxis.labels.boxAnchor = "e"
    bc.bars.strokeColor = None
    bc.barWidth = 8
    for i, v in enumerate(sub["margin_pct"]):
        bc.bars[(0, i)].fillColor = RED if v < 0 else GREEN
    d.add(bc)
    return d


def build_pdf(df: pd.DataFrame, scope: str, summary_text: str = "", summary_mode: str = "") -> bytes:
    """Executive PDF for the filtered data. `summary_mode` labels how the summary was produced."""
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                            title="NexMargin Profit Intelligence Report", author="NexMargin")
    W = A4[0] - 36 * mm
    story = [Paragraph("NexMargin", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=10, textColor=INDIGO)),
             Paragraph("Profit Intelligence Report", st["title"]),
             Paragraph(_safe(f"{scope}  |  Generated {datetime.now():%d %b %Y}"), st["sub"])]
    if df.empty:
        story.append(Paragraph("No data in the selected filters.", st["body"]))
        doc.build(story)
        return buf.getvalue()

    k = metrics.kpis(df)
    kpi_rows = [["Revenue", "Profit", "Profit margin", "Orders"],
                [fmt_money_full(k["revenue"]), fmt_money_full(k["profit"]), fmt_pct(k["margin_pct"]), fmt_int(k["orders"])]]
    kt = Table(kpi_rows, colWidths=[W / 4] * 4)
    kt.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica", 8.5), ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
                            ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 15), ("TEXTCOLOR", (0, 1), (-1, 1), NAVY),
                            ("BACKGROUND", (0, 0), (-1, -1), SOFT), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white)]))
    story += [kt, Spacer(1, 4)]

    if summary_text:
        label = {"AI explanation": "AI-generated summary", "Demo mode": "Auto-generated summary (rule-based)",
                 "Verified fallback": "Auto-generated summary (rule-based)"}.get(summary_mode, "Summary")
        story += [Paragraph("Executive summary", st["h2"]), Paragraph(_safe(summary_text.replace("**", "")), st["body"]),
                  Paragraph(label, st["small"])]

    story += [Paragraph("Revenue and profit trend", st["h2"]), _trend_drawing(metrics.monthly_series(df), W)]

    cat = metrics.group_summary(df, "category").sort_values("profit", ascending=False)
    rows = [["Category", "Revenue", "Profit", "Margin", "Share of profit"]] + [
        [r.category, fmt_money(r.revenue), fmt_money(r.profit), fmt_pct(r.margin_pct), fmt_pct(r.profit_share_pct)] for r in cat.itertuples()]
    story += [KeepTogether([Paragraph("Top-performing categories", st["h2"]), _table(rows, [W * .32, W * .17, W * .17, W * .16, W * .18], neg_cols=(2, 3))])]

    reg = metrics.group_summary(df, "region").sort_values("profit", ascending=False)
    rows = [["Region", "Revenue", "Profit", "Margin", "Orders"]] + [
        [r.region, fmt_money(r.revenue), fmt_money(r.profit), fmt_pct(r.margin_pct), fmt_int(r.orders)] for r in reg.itertuples()]
    story += [KeepTogether([Paragraph("Regional insights", st["h2"]), _table(rows, [W * .32, W * .17, W * .17, W * .16, W * .18], neg_cols=(2, 3))])]

    sub = metrics.group_summary(df, ["category", "subcategory"])
    story += [KeepTogether([Paragraph("Margin by sub-category", st["h2"]), _margin_bars(sub, W)])]

    insights = A.business_insights(df, limit=3)
    if insights:
        story.append(Paragraph("Important business observations", st["h2"]))
        for i in insights:
            story.append(Paragraph(f"<b>{_safe(i['title'])}.</b> {_safe(i['text'])}", st["body"]))
            story.append(Spacer(1, 3))

    story += [Spacer(1, 10), Paragraph(
        "Data: Superstore sample dataset (US dollars). Cost is derived as sales minus profit. "
        "Figures are computed from the filtered order lines; nothing is estimated.", st["small"])]
    doc.build(story)
    return buf.getvalue()
