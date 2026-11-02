# 20 likely interview questions about THIS implementation (with answers)

**1. Why DuckDB instead of just Pandas?** The brief asked for SQL analytics, and DuckDB runs analytical SQL (CTEs, window functions) in-process on a DataFrame with no server. Pandas handles generic grouping in `metrics.group_summary`; tests assert both give identical numbers.

**2. How do you make sure SQL and Python metrics agree?** One definition file (`metrics.py`); SQL queries mirror it; `test_sql_matches_python_metrics` and a real-data test compare region and category results.

**3. The dataset has no cost column. What did you do?** Derived `cost = sales − profit` and labelled it derived everywhere. I did not invent cost or profit.

**4. How did you clean the data? What did you find?** Pure `clean()` function: type coercion, duplicate detection ignoring the surrogate Row ID, invalid dates/discounts/quantities, canonical product names. Found one true duplicate and 32 Product IDs with multiple names; outliers are flagged, not removed, because large orders are real.

**5. Why not drop profit outliers?** They are real big orders/returns; removing them would misstate profit. They are flagged (3×IQR) for investigation.

**6. Explain the headline discount insight.** Lines discounted 30%+ are ~14% of lines, ~15.8% of revenue, but lose ~$135K (margin ≈ −37%); ~97% of them lose money, versus ~29.5% margin at 0% discount. Caveat: it's correlation in observational data (e.g., discounts may be given on already weak products).

**7. How is growth calculated and what if previous is zero or negative?** (cur−prev)/|prev|×100; zero/missing previous returns `None`, shown as "n/a". |prev| keeps a loss→profit move positive.

**8. How do you avoid fabricating period comparisons?** `previous_period` returns a window only if it lies fully inside the data; otherwise cards show "No prior period".

**9. How is AOV computed and why distinct orders?** Revenue ÷ distinct `order_id`; an order has several lines, so counting rows would inflate orders and understate AOV.

**10. How does the forecast work and how is it evaluated?** OLS: trend + month dummies on monthly revenue. Holdout: last 6 months, MAE/RMSE against a seasonal-naive baseline. It beat the baseline here (~$14.3K vs ~$20.5K MAE) on one split — indicative, not proof.

**11. What are the forecast's limits?** About 48 points for 13 parameters; additive seasonality; interval ignores parameter uncertainty; no external drivers.

**12. Why not ARIMA/Prophet?** Explainability and no extra dependencies for a short series; noted as a future improvement with proper time-series cross-validation.

**13. Explain RFM segmentation.** Scores 1–5 by percentile rank (ties share scores); rules on R and mean(F,M) assign five segments, evaluated in order so every customer gets exactly one (tested exhaustively). Descriptive, not predictive; no accuracy claimed.

**14. Define retention in your app.** Of customers active in year Y, % who ordered again in Y+1 (73% → 79% → 88% across years). Not a first-purchase cohort method — stated in the docs.

**15. How does the AI Copilot avoid hallucinated numbers?** Calculations happen in allowlisted Python/SQL; the LLM receives pre-formatted facts and its reply is rejected if it contains any number absent from those facts (falls back to a deterministic answer).

**16. What can't that guard catch?** Wrong reasoning or misleading wording using correct numbers. It's a number check, not a truth check.

**17. How do you prevent SQL/code injection or prompt injection?** No SQL or code from users or the LLM ever executes. Queries are selected by name from a file, parameters are type/range-validated and `?`-bound; LLM intent output must equal an allowlist key. Tests cover injection strings.

**18. What happens without an API key or when Groq fails?** Demo mode: deterministic, verified answers; API errors produce "Verified fallback". The rest of the app never depends on the key.

**19. How is performance handled?** `st.cache_data` for the dataset, RFM and forecast; DuckDB over ~10k rows is milliseconds; filters run once per page in pandas.

**20. What would you do next / what are the weaknesses?** Real cost data, cohort retention, proper forecast cross-validation, authentication/multi-dataset upload, CI on Windows, and browser-based UI regression tests (current UI tests use Streamlit AppTest, not screenshots).
