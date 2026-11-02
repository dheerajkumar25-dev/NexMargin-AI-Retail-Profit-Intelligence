"""AI Copilot: question -> intent -> allowlisted calculation -> verified numbers -> explanation.

Safety design
-------------
* The LLM never sees raw data, never writes SQL/Python, and never computes anything.
* Intents map to a fixed allowlist of Python functions (see INTENTS). Unknown questions are not executed.
* Extracted parameters (top-N, region, category, segment, year) are validated against the loaded data.
* All numbers come from metrics.py / analytics.py and are passed to the LLM as pre-formatted strings.
* The LLM's reply is checked: any number not present in the supplied facts causes a fallback to the
  deterministic (demo-mode) answer. This guard catches invented figures; it cannot judge reasoning quality.
* Without an API key (or on any API error) the app answers with deterministic, fully verified text.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from . import analytics as A
from . import config, metrics
from .formatting import fmt_int, fmt_money, fmt_pct

LLM = Callable[[str, str], str]  # (system_prompt, user_prompt) -> text
MAX_QUESTION_CHARS = 500

SUGGESTED_QUESTIONS = [
    "Why did profit decrease?",
    "Which category generates the highest profit?",
    "Which products have the lowest profit margin?",
    "Compare revenue across regions.",
    "What is the impact of discounts?",
    "Which customer segment contributes the most profit?",
]


@dataclass
class ToolResult:
    title: str
    facts: dict
    tables: dict = field(default_factory=dict)
    narrative: str = ""


@dataclass
class CopilotAnswer:
    question: str
    intent: str | None
    intent_label: str
    answer: str
    mode: str                      # "AI explanation" | "Demo mode" | "Verified fallback"
    facts: dict = field(default_factory=dict)
    tables: dict = field(default_factory=dict)
    scope: str = ""
    notes: list = field(default_factory=list)


# ------------------------------------------------------------------ parameter extraction
def extract_params(question: str, df: pd.DataFrame) -> tuple[dict, list[str]]:
    """Validated parameters mentioned in the question. Returns (params, notes)."""
    q, params, notes = question.lower(), {}, []
    m = re.search(r"\b(?:top|best|worst|lowest|highest|bottom)\s+(\d{1,3})\b", q) or \
        re.search(r"\b(\d{1,3})\s+(?:products|customers|items|categories)\b", q)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 20:
            params["n"] = n
        else:
            notes.append(f"Ignored requested count {n}; allowed range is 1-20.")
    for key, col in (("region", "region"), ("category", "category"), ("segment", "segment")):
        for value in sorted(df[col].dropna().unique()) if len(df) else []:
            if re.search(rf"\b{re.escape(str(value).lower())}\b", q):
                params[key] = str(value)
                break
    y = re.search(r"\b((?:19|20)\d{2})\b", q)
    if y:
        year = int(y.group(1))
        if len(df) and year in set(df["order_year"].unique()):
            params["year"] = year
        else:
            notes.append(f"Ignored year {year}: no data for it in the current selection.")
    return params, notes


# ------------------------------------------------------------------ calculation tools
def _tool_overview(df, params) -> ToolResult:
    k = metrics.kpis(df)
    reg = metrics.group_summary(df, "region")
    cat = metrics.group_summary(df, "category")
    facts = {"revenue": fmt_money(k["revenue"]), "profit": fmt_money(k["profit"]), "profit_margin": fmt_pct(k["margin_pct"]),
             "orders": fmt_int(k["orders"]), "average_order_value": fmt_money(k["aov"]),
             "average_discount": fmt_pct(k["avg_discount_pct"]),
             "highest_profit_region": f"{reg.loc[reg['profit'].idxmax(), 'region']} ({fmt_money(reg['profit'].max())})",
             "highest_profit_category": f"{cat.loc[cat['profit'].idxmax(), 'category']} ({fmt_money(cat['profit'].max())})"}
    text = (f"Revenue is **{facts['revenue']}** and profit **{facts['profit']}**, a margin of **{facts['profit_margin']}** "
            f"across **{facts['orders']}** orders (average order value {facts['average_order_value']}). "
            f"{facts['highest_profit_region']} is the most profitable region and {facts['highest_profit_category']} the most profitable category.")
    return ToolResult("Business overview", facts, {"By region": reg, "By category": cat}, text)


def _period_pair(df, year=None):
    """Like-for-like comparison periods: (previous_df, current_df, prev_label, cur_label, note) or None."""
    years = sorted(df["order_year"].unique())
    if year is not None:
        cy, py = year, year - 1
        if cy not in years or py not in years:
            return None
    elif len(years) >= 2:
        cy, py = years[-1], years[-2]
    else:
        months = sorted(df["order_month"].unique())
        if len(months) < 6:
            return None
        cut = months[-3:]
        prev_m = months[-6:-3]
        return (df[df["order_month"].isin(prev_m)], df[df["order_month"].isin(cut)],
                "the previous 3 months", "the latest 3 months", "")
    cur, prev = df[df["order_year"] == cy], df[df["order_year"] == py]
    common = set(cur["order_date"].dt.month) & set(prev["order_date"].dt.month)
    if not common:
        return None
    cur, prev = cur[cur["order_date"].dt.month.isin(common)], prev[prev["order_date"].dt.month.isin(common)]
    note = "" if len(common) == 12 else f"Compared on the {len(common)} calendar months present in both years."
    return prev, cur, str(py), str(cy), note


def _tool_profit_change(df, params) -> ToolResult:
    pair = _period_pair(df, params.get("year"))
    if pair is None:
        return ToolResult("Profit change", {"result": "Not enough history in the current selection to compare two periods."},
                          narrative="There isn't enough history in the current selection to compare two periods. Widen the date range and ask again.")
    prev, cur, pl, cl, note = pair
    p_cur, p_prev = metrics.profit(cur), metrics.profit(prev)
    chg = metrics.growth_pct(p_cur, p_prev)
    m_cur, m_prev = metrics.profit_margin(cur), metrics.profit_margin(prev)
    rev_chg = metrics.growth_pct(metrics.revenue(cur), metrics.revenue(prev))

    sub = pd.concat([cur.groupby("subcategory")["profit"].sum().rename("current"),
                     prev.groupby("subcategory")["profit"].sum().rename("previous")], axis=1).fillna(0)
    sub["change"] = sub["current"] - sub["previous"]
    sub = sub.sort_values("change").reset_index()
    down = sub[sub["change"] < 0].head(3)
    up = sub[sub["change"] > 0].tail(3).iloc[::-1]
    leak_c, leak_p = A.discount_leakage(cur), A.discount_leakage(prev)

    def item(r):
        return f"{r['subcategory']}: {fmt_money(r['change'])} ({fmt_money(r['previous'])} to {fmt_money(r['current'])})"

    direction = "decreased" if (chg is not None and chg < -0.05) else "increased" if (chg is not None and chg > 0.05) else "was flat"
    facts = {
        "comparison": f"{cl} vs {pl}", "profit_current": fmt_money(p_cur), "profit_previous": fmt_money(p_prev),
        "profit_change": f"{fmt_money(p_cur - p_prev)}, {chg:+.1f}%" if chg is not None else "n/a",
        "revenue_change": f"{rev_chg:+.1f}%" if rev_chg is not None else "n/a",
        "margin_current": fmt_pct(m_cur), "margin_previous": fmt_pct(m_prev),
        "average_discount_current": fmt_pct(metrics.average_discount(cur)), "average_discount_previous": fmt_pct(metrics.average_discount(prev)),
        "deep_discount_profit_current": fmt_money(leak_c["profit"]), "deep_discount_profit_previous": fmt_money(leak_p["profit"]),
        "largest_declines": [item(r) for _, r in down.iterrows()] or ["none"],
        "largest_gains": [item(r) for _, r in up.iterrows()] or ["none"],
    }
    lead = (f"Profit {direction} from **{facts['profit_previous']}** in {pl} to **{facts['profit_current']}** in {cl} "
            f"({facts['profit_change']}), while revenue changed {facts['revenue_change']}; margin moved from "
            f"{facts['margin_previous']} to {facts['margin_current']}.")
    if direction != "decreased":
        lead = "Profit did not decrease in this comparison. " + lead
    parts = [lead]
    if len(down):
        parts.append("Weakest areas: " + "; ".join(facts["largest_declines"]) + ".")
    parts.append(f"Lines discounted {A.DISCOUNT_LEAKAGE_THRESHOLD_PCT:.0f}%+ earned {facts['deep_discount_profit_current']} in {cl} "
                 f"versus {facts['deep_discount_profit_previous']} in {pl}.")
    if note:
        parts.append(note)
    return ToolResult("Profit change drivers", facts, {"Profit change by sub-category": sub}, " ".join(parts))


def _tool_top_category(df, params) -> ToolResult:
    cat = metrics.group_summary(df, "category").sort_values("profit", ascending=False).reset_index(drop=True)
    top, low = cat.iloc[0], cat.loc[cat["margin_pct"].idxmin()]
    facts = {"top_category": top["category"], "top_category_profit": fmt_money(top["profit"]),
             "top_category_margin": fmt_pct(top["margin_pct"]), "top_category_share_of_profit": fmt_pct(top["profit_share_pct"]),
             "lowest_margin_category": f"{low['category']} ({fmt_pct(low['margin_pct'])})",
             "ranking": [f"{r.category}: profit {fmt_money(r.profit)}, margin {fmt_pct(r.margin_pct)}" for r in cat.itertuples()]}
    text = (f"**{top['category']}** generates the most profit: **{facts['top_category_profit']}** at a "
            f"**{facts['top_category_margin']}** margin ({facts['top_category_share_of_profit']} of total profit). "
            f"The lowest margin belongs to {facts['lowest_margin_category']}.")
    return ToolResult("Profit by category", facts, {"Category performance": cat}, text)


def _tool_lowest_margin_products(df, params) -> ToolResult:
    n = params.get("n", 5)
    prods = A.lowest_margin_products(df, n=n, min_revenue=500.0)
    min_rev = 500.0
    if prods.empty:
        prods, min_rev = A.lowest_margin_products(df, n=n, min_revenue=0.0), 0.0
    allp = A.product_summary(df)
    neg = int((allp["profit"] < 0).sum())
    facts = {"minimum_product_revenue_considered": fmt_money(min_rev), "products_with_negative_profit": f"{fmt_int(neg)} of {fmt_int(len(allp))}",
             "lowest_margin_products": [f"{r.product_name} ({r.category}): margin {fmt_pct(r.margin_pct)}, profit {fmt_money(r.profit)}, revenue {fmt_money(r.revenue)}"
                                        for r in prods.itertuples()] or ["none"]}
    text = (f"The {len(prods)} lowest-margin products (with at least {fmt_money(min_rev)} revenue) are: " +
            "; ".join(facts["lowest_margin_products"]) +
            f". Overall, {facts['products_with_negative_profit']} products lose money.")
    return ToolResult("Lowest-margin products", facts, {"Lowest-margin products": prods}, text)


def _tool_region_compare(df, params) -> ToolResult:
    reg = metrics.group_summary(df, "region")
    best, worst = reg.loc[reg["margin_pct"].idxmax()], reg.loc[reg["margin_pct"].idxmin()]
    top_rev = reg.iloc[0]
    facts = {"highest_revenue_region": f"{top_rev['region']} ({fmt_money(top_rev['revenue'])})",
             "best_margin_region": f"{best['region']} ({fmt_pct(best['margin_pct'])})",
             "worst_margin_region": f"{worst['region']} ({fmt_pct(worst['margin_pct'])})",
             "regions": [f"{r.region}: revenue {fmt_money(r.revenue)}, profit {fmt_money(r.profit)}, margin {fmt_pct(r.margin_pct)}" for r in reg.itertuples()]}
    text = (f"{facts['highest_revenue_region']} leads on revenue. Margin is best in {facts['best_margin_region']} and weakest in "
            f"{facts['worst_margin_region']}. " + "; ".join(facts["regions"]) + ".")
    return ToolResult("Regional comparison", facts, {"Regions": reg}, text)


def _tool_discount_impact(df, params) -> ToolResult:
    bands = A.discount_bands(df)
    leak = A.discount_leakage(df)
    zero = bands[bands["discount_band"] == "0%"]
    facts = {"leakage_threshold": f"{leak['threshold_pct']:.0f}%+",
             "deep_discount_lines": f"{fmt_int(leak['lines'])} ({fmt_pct(leak['lines_share_pct'])} of lines)",
             "deep_discount_revenue": f"{fmt_money(leak['revenue'])} ({fmt_pct(leak['revenue_share_pct'])} of revenue)",
             "deep_discount_profit": fmt_money(leak["profit"]), "deep_discount_margin": fmt_pct(leak["margin_pct"]),
             "deep_discount_lines_losing_money": fmt_pct(leak["loss_line_pct"]),
             "margin_with_no_discount": fmt_pct(zero["margin_pct"].iloc[0]) if len(zero) else "n/a",
             "margin_by_discount_band": [f"{r.discount_band}: {fmt_pct(r.margin_pct)} margin on {fmt_money(r.revenue)}" for r in bands.itertuples()]}
    text = (f"Lines discounted {facts['leakage_threshold']} produced {facts['deep_discount_revenue']} but a profit of "
            f"**{facts['deep_discount_profit']}** (margin {facts['deep_discount_margin']}); {facts['deep_discount_lines_losing_money']} of them lose money. "
            f"Undiscounted sales earn a {facts['margin_with_no_discount']} margin. By band: " + "; ".join(facts["margin_by_discount_band"]) + ".")
    return ToolResult("Discount impact", facts, {"Discount bands": bands, "Deep-discount leakage by sub-category": A.leakage_by_subcategory(df)}, text)


def _tool_segment_profit(df, params) -> ToolResult:
    seg = metrics.group_summary(df, "segment").sort_values("profit", ascending=False).reset_index(drop=True)
    top = seg.iloc[0]
    facts = {"top_segment": top["segment"], "top_segment_profit": fmt_money(top["profit"]),
             "top_segment_share_of_profit": fmt_pct(top["profit_share_pct"]), "top_segment_margin": fmt_pct(top["margin_pct"]),
             "segments": [f"{r.segment}: profit {fmt_money(r.profit)}, revenue {fmt_money(r.revenue)}, margin {fmt_pct(r.margin_pct)}" for r in seg.itertuples()]}
    text = (f"**{top['segment']}** contributes the most profit: **{facts['top_segment_profit']}** "
            f"({facts['top_segment_share_of_profit']} of the total, margin {facts['top_segment_margin']}). " + "; ".join(facts["segments"]) + ".")
    return ToolResult("Customer segment profit", facts, {"Segments": seg}, text)


def _tool_top_products(df, params) -> ToolResult:
    n = params.get("n", 5)
    prods = A.top_products_by_profit(df, n)
    facts = {"top_products_by_profit": [f"{r.product_name} ({r.category}): profit {fmt_money(r.profit)}, margin {fmt_pct(r.margin_pct)}" for r in prods.itertuples()] or ["none"]}
    return ToolResult("Top products by profit", facts, {"Top products": prods},
                      f"The top {len(prods)} products by profit are: " + "; ".join(facts["top_products_by_profit"]) + ".")


def _tool_top_customers(df, params) -> ToolResult:
    n = params.get("n", 5)
    cust = A.top_customers(df, n)
    share = A.customer_concentration(df)
    facts = {"top_customers_by_revenue": [f"{r.customer_name} ({r.segment}): revenue {fmt_money(r.revenue)}, profit {fmt_money(r.profit)}" for r in cust.itertuples()] or ["none"],
             "revenue_share_of_top_10_percent_of_customers": fmt_pct(share)}
    return ToolResult("Top customers", facts, {"Top customers": cust},
                      f"The top {len(cust)} customers by revenue are: " + "; ".join(facts["top_customers_by_revenue"]) +
                      f". The top 10% of customers account for {facts['revenue_share_of_top_10_percent_of_customers']} of revenue.")


@dataclass(frozen=True)
class Intent:
    key: str
    label: str
    primary: str                 # regex that must match for the intent to be a candidate (weight 3)
    secondary: tuple             # extra regexes, +1 each
    tool: Callable


_PROFIT_CHANGE = r"(why|decreas|declin|drop|fell|fall|dip|down|reduc|lower).*profit|profit.*(why|decreas|declin|drop|fell|fall|dip|down|reduc|lower)"
INTENTS: tuple[Intent, ...] = (
    Intent("profit_change", "Profit change", _PROFIT_CHANGE, (r"year|period|month",), _tool_profit_change),
    Intent("lowest_margin_products", "Lowest-margin products",
           r"(low|least|worst|poor|bad).*(margin|profitab)|(margin|profitab).*(low|least|worst|poor)|unprofitable|loss.?making",
           (r"product|item",), _tool_lowest_margin_products),
    Intent("top_category_profit", "Category profit", r"categor", (r"profit", r"high|most|best|top|large"), _tool_top_category),
    Intent("region_compare", "Regional comparison", r"region|geograph|territor", (r"compar|across|versus|vs",), _tool_region_compare),
    Intent("discount_impact", "Discount impact", r"discount|promo", (r"impact|effect|profit",), _tool_discount_impact),
    Intent("segment_profit", "Customer segments", r"segment|consumer|corporate|home office", (r"profit|contribut|most",), _tool_segment_profit),
    Intent("top_customers", "Top customers", r"(top|best|biggest|largest|valuable).*customer|customer.*(lifetime|top|best)", (r"revenue",), _tool_top_customers),
    Intent("top_products", "Top products", r"(top|best|highest|most|biggest|largest).*(product|item)|product.*(top|best|highest)", (r"profit|revenue|sell",), _tool_top_products),
    Intent("overview", "Business overview", r"overview|summar|kpi|snapshot|how (are|is)|performance|doing", (), _tool_overview),
)
INTENT_BY_KEY = {i.key: i for i in INTENTS}


def detect_intent(question: str) -> str | None:
    """Keyword-scored intent from the allowlist, or None."""
    q = question.lower()
    best, best_score = None, 0
    for intent in INTENTS:
        if re.search(intent.primary, q):
            score = 3 + sum(1 for s in intent.secondary if re.search(s, q))
            if score > best_score:
                best, best_score = intent.key, score
    return best


def classify_with_llm(question: str, llm: LLM) -> str | None:
    """Ask the LLM to pick an intent. The reply is validated against the allowlist, nothing else is trusted."""
    keys = ", ".join(INTENT_BY_KEY)
    system = ("Classify the user's analytics question into exactly one intent key from this list: "
              f"{keys}. Reply with only the key, or 'none' if no intent fits.")
    try:
        reply = llm(system, question).strip().lower().strip("`'\". ")
    except Exception:  # noqa: BLE001 - any API failure just means no classification
        return None
    return reply if reply in INTENT_BY_KEY else None


# ------------------------------------------------------------------ LLM explanation + guardrail
SYSTEM_PROMPT = (
    "You are NexMargin's retail profit analyst. Answer the user's question using ONLY the verified facts provided. "
    "Rules: copy numbers exactly as written in the facts; never calculate, round, estimate or introduce any number, "
    "percentage or date that is not in the facts; do not mention data you were not given. "
    "Write 3-5 plain-English sentences for a business decision-maker, mention the scope (period/filters), "
    "and end with one practical recommendation that does not contain new numbers. Output text only."
)
_NUM = re.compile(r"\d[\d,]*\.?\d*")


def _numbers(text: str) -> set[float]:
    out = set()
    for tok in _NUM.findall(text):
        try:
            out.add(round(float(tok.rstrip(".,").replace(",", "")), 2))
        except ValueError:
            continue
    return out


def unverified_numbers(response: str, supplied_text: str) -> list[float]:
    """Numbers in `response` that do not appear in the supplied facts (small whole numbers are ignored)."""
    allowed = _numbers(supplied_text)
    return sorted(n for n in _numbers(response) if n not in allowed and not (n == int(n) and n <= 10))


def _build_user_prompt(question: str, scope: str, facts: dict) -> str:
    return f"Question: {question}\nScope: {scope}\nVerified facts (JSON):\n{json.dumps(facts, indent=2)}"


def _explain(question: str, scope: str, result: ToolResult, llm: LLM | None) -> tuple[str, str, list[str]]:
    """Returns (answer_text, mode, notes)."""
    if llm is None:
        return result.narrative, "Demo mode", []
    try:
        reply = llm(SYSTEM_PROMPT, _build_user_prompt(question, scope, result.facts)).strip()
    except Exception as exc:  # noqa: BLE001
        return result.narrative, "Verified fallback", [f"AI service unavailable ({type(exc).__name__}); showing the calculated summary."]
    bad = unverified_numbers(reply, json.dumps(result.facts) + " " + scope)
    if not reply or bad:
        return result.narrative, "Verified fallback", [
            "The AI reply contained numbers that are not in the calculated results, so it was discarded."]
    return reply, "AI explanation", []


# ------------------------------------------------------------------ public entry points
def make_groq_llm() -> LLM | None:
    """A Groq-backed callable, or None when no key/package is available."""
    if not config.GROQ_API_KEY:
        return None
    try:
        from groq import Groq
    except ImportError:
        return None
    client = Groq(api_key=config.GROQ_API_KEY, timeout=20.0, max_retries=1)

    def call(system: str, user: str) -> str:
        resp = client.chat.completions.create(
            model=config.GROQ_MODEL, temperature=0.2, max_tokens=400,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return resp.choices[0].message.content or ""
    return call


HELP_TEXT = ("I can answer questions about profit and revenue drivers, categories, products, regions, discounts, customer "
             "segments and top customers. Try one of the suggested questions.")


def answer_question(question: str, df: pd.DataFrame, scope: str, llm: LLM | None = None) -> CopilotAnswer:
    """Answer a question about `df` (already filtered by the UI). `scope` describes filters and period."""
    question = (question or "").strip()
    if not question:
        raise ValueError("Please enter a question.")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"Questions are limited to {MAX_QUESTION_CHARS} characters.")
    if df.empty:
        return CopilotAnswer(question, None, "No data", "There is no data in the current selection. Widen the filters and try again.",
                             "Demo mode", scope=scope)

    intent_key = detect_intent(question)
    notes: list[str] = []
    if intent_key is None and llm is not None:
        intent_key = classify_with_llm(question, llm)
    if intent_key is None:
        return CopilotAnswer(question, None, "Not recognised", HELP_TEXT, "Demo mode", scope=scope)

    params, pnotes = extract_params(question, df)
    notes += pnotes
    work, applied = df, []
    for key, col in (("region", "region"), ("category", "category"), ("segment", "segment"), ("year", "order_year")):
        if key in params:
            work = work[work[col] == params[key]]
            applied.append(f"{key}={params[key]}")
    full_scope = scope + (f" | Question filters: {', '.join(applied)}" if applied else "")
    if work.empty:
        return CopilotAnswer(question, intent_key, INTENT_BY_KEY[intent_key].label,
                             "No data matches those filters.", "Demo mode", scope=full_scope, notes=notes)

    intent = INTENT_BY_KEY[intent_key]
    result = intent.tool(work, params)
    text, mode, enotes = _explain(question, full_scope, result, llm)
    return CopilotAnswer(question, intent_key, intent.label, text, mode, result.facts, result.tables, full_scope, notes + enotes)


def executive_summary(df: pd.DataFrame, scope: str, llm: LLM | None = None) -> tuple[str, str]:
    """(summary_text, mode). Deterministic when no LLM; LLM text is number-verified."""
    if df.empty:
        return "No data in the current selection.", "Demo mode"
    ov = _tool_overview(df, {})
    insights = A.business_insights(df)
    facts = dict(ov.facts)
    facts["key_observations"] = [f"{i['title']}: {i['text']}" for i in insights]
    narrative = ov.narrative + (" " + " ".join(i["text"] for i in insights) if insights else "")
    result = ToolResult("Executive summary", facts, narrative=narrative)
    text, mode, _ = _explain("Write a short executive summary of business performance and the main profit risks.", scope, result, llm)
    return text, mode
