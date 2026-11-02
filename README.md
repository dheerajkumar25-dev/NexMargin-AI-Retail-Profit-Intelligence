# NexMargin — AI-Powered Retail Profit Intelligence

> Revenue tells you how much you sell. NexMargin tells you how much you actually earn — and why.

A Streamlit analytics app on the Superstore retail dataset (9,993 order lines, 2014–2017). It combines Pandas, DuckDB SQL, simple ML (forecasting, RFM) and a guard-railed GenAI copilot.

**Headline finding the app surfaces:** order lines discounted 30%+ produce ~15.8% of revenue but a **-$135K profit** (margin -37%); 97% of them lose money.

## Pages
| Page | What it does |
|---|---|
| **Overview** | 4 KPI cards (with honest prior-period deltas and sparklines), revenue-vs-profit trend, 3 auto-generated insights, sub-category margins, regional performance |
| **Explore** | Date / region / category / segment filters driving: products (top 10, lowest margin, Pareto), customers (concentration, frequency, RFM, retention, AOV), discount leakage, regions, revenue forecast, sortable order table + CSV |
| **AI Copilot** | Chat over the filtered data. Question → allowlisted calculation → verified numbers → explanation. Works fully **without an API key** (demo mode) |
| **Reports** | Executive summary, tables, observations; download PDF report, filtered CSV, summary ZIP |

## Quick start (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/build_data.py        # downloads + cleans the dataset (once)
streamlit run app.py
python -m pytest                    # run the tests
```
macOS/Linux: `source .venv/bin/activate` instead of the Activate line.

**Optional AI:** copy `.env.example` to `.env`, set `GROQ_API_KEY` (and optionally `GROQ_MODEL`; check Groq's current model list). Without it the Copilot and reports use deterministic answers.

## Project layout
```
app.py                      entry point (routing, caching, error handling)
src/nexmargin/
  config.py                 paths, env settings        preprocessing.py  cleaning + validation (pure function)
  data_loader.py            raw -> processed           metrics.py        ALL metric definitions
  database.py               DuckDB, allowlisted SQL    analytics.py      filters, comparisons, insights
  forecasting.py            trend + seasonality model  segmentation.py   RFM
  ai_copilot.py             intent -> tool -> LLM      report_generator.py  PDF / CSV / ZIP
  components/               styling, charts, kpi_cards, sidebar(+filters), tables
  pages/                    overview, explore, copilot, reports
sql/business_queries.sql    11 documented queries (CTE, window, JOIN, HAVING, CASE...)
tests/                      100 tests          docs/  methodology, architecture, data dictionary, interview prep
```

## Design decisions worth knowing
- **One source of truth for metrics** (`metrics.py`); SQL results are tested to match it.
- **Cost is derived** (sales − profit); the source has no cost column. Currency is **US dollars** — no fake rupee conversion.
- **No invented comparisons:** a delta is shown only when the whole previous period exists in the data.
- **The LLM never computes or executes anything.** See `docs/methodology.md` → GenAI workflow.

## Data & licence
Kaggle "Superstore Dataset" (vivek468) — a commonly used sample dataset, not data from an identifiable real company. Its licence is **not verified**; the raw CSV is git-ignored and fetched by script. Check the Kaggle page before redistributing.

## Known limitations
- Four years of history: forecasts and seasonality are approximate (see `docs/methodology.md`).
- RFM segments are descriptive rules, not a predictive model.
- Built and tested on Linux; written with `pathlib` for Windows compatibility but not run on Windows by the author of this scaffold.
- UI was verified with Streamlit's AppTest and a live server health check, not by browser screenshots — review the visuals yourself and tweak `components/styling.py` as needed.

## Future improvements
Authentication and multi-dataset upload; cohort-based retention; Prophet/ETS forecasting with proper cross-validation; cost data to replace the derived cost; scheduled report emails.
