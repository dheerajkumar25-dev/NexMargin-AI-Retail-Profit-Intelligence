# Methodology

## 1. Business problem & objectives
Revenue can grow while profit shrinks (discounts, low-margin products, weak regions). Dashboards show *what* happened; NexMargin helps explain *why* and lets users ask questions in plain English. Objectives: correct KPIs, discover profit leakage, segment customers, forecast revenue, answer questions with verifiable numbers.

## 2. Data cleaning (`preprocessing.clean`)
Raw → snake_case schema → trim text → coerce numbers/dates (month-first) → drop (each counted in `data_quality_report.json`): duplicate records (ignoring surrogate Row ID), invalid dates, missing keys, missing sales/profit, negative sales, non-positive quantity, discount outside 0–1. Flags (not drops): ship-before-order, loss-making lines, profit outliers (3×IQR). Product names canonicalised per Product ID (32 IDs had 2+ names). Result on this dataset: 9,994 → 9,993 rows (one true duplicate).
Derived: `cost = sales − profit`, `discount_pct`, `order_month`, `order_year`, `is_loss`.

## 3. KPI definitions (`metrics.py`)
Revenue = Σ sales · Profit = Σ profit · Margin = profit/revenue×100 · Orders = distinct order_id · AOV = revenue/orders · Avg discount = mean discount_pct over lines · Growth % = (cur − prev)/|prev|×100 (undefined if prev is 0/missing → shown "n/a"). Margin deltas are percentage points.
**Prior period:** the equal-length window immediately before the selection; offered only if fully inside the data (treated as continuous from the first day of its first month). Otherwise the UI says no comparison exists.
**Retention:** of customers who ordered in year Y, % who ordered again in Y+1 (active-customer retention, not first-purchase cohorts). **Repeat rate:** % of customers with ≥2 distinct orders.

## 4. SQL (`sql/business_queries.sql`, `database.py`)
11 named queries run on an in-memory DuckDB with `orders`, `dim_customers`, `dim_products`. Features: CTEs, INNER/LEFT JOIN, GROUP BY/HAVING, CASE WHEN, RANK, DENSE_RANK, LAG (MoM growth), running totals (SUM OVER), PERCENT_RANK. Filters are applied in pandas first; SQL only receives validated, `?`-bound parameters.

## 5. Forecasting (`forecasting.py`)
OLS on monthly revenue: intercept + linear trend + month-of-year dummies. Evaluation: fit on all but the last 6 months, predict them, report MAE and RMSE next to a seasonal-naive baseline (same month last year). Interval: ±1.96σ of in-sample residuals (approximate; ignores parameter uncertainty). On the full dataset the 6-month holdout MAE was ≈ $14.3K vs ≈ $20.5K for the naive baseline (one split, so treat as indicative). **Limitations:** ~4 years of data; additive seasonality; no external drivers; needs ≥ 24 months.

## 6. Customer segmentation (`segmentation.py`)
RFM: recency (days since last order to latest date + 1), frequency (distinct orders), monetary (sales). Each scored 1–5 by percentile rank (ties share scores). With FM = (F+M)/2, rules in order: Champions R≥4 & FM≥4 · Loyal R≥3 & FM≥3 · Potential Loyalists R≥3 · At Risk FM≥3 · Lost otherwise. Descriptive and deterministic; no accuracy claim.

## 7. GenAI workflow (`ai_copilot.py`)
1. Validate question (non-empty, ≤500 chars).
2. Intent = keyword-scored match against a fixed allowlist of 9 intents (optional LLM classification, whose answer must be an allowlist key).
3. Parameters (top-N 1–20, region, category, segment, year) are extracted and validated against the loaded data.
4. An allowlisted Python function computes results via `metrics`/`analytics`/named SQL.
5. Results are formatted into strings and sent as JSON "verified facts" — never raw rows.
6. The LLM writes a short explanation; **every number in its reply must appear in the facts** or the reply is discarded for the deterministic answer ("Verified fallback").
7. UI shows the answer, mode badge, evidence tables and the exact filters/period used.
Not allowed anywhere: LLM-written SQL/Python, free-form queries. No key / API error → demo mode. *The number check catches invented figures; it cannot judge whether the prose reasoning is sound.*

## 8. Testing
100 pytest tests: cleaning edge cases, metric definitions (empty, null, zero revenue, duplicates, growth), SQL vs pandas agreement (including real data), parameter/allowlist enforcement, RFM rules, forecast recovery of a known series, Copilot guardrails (invented numbers, prompt injection, API failure), PDF/CSV/ZIP, and end-to-end UI via Streamlit AppTest (filters change KPIs, copilot flow, empty state).
