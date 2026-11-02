# Architecture
```
data/raw CSV --preprocessing.clean()--> data/processed/orders_clean.csv + data_quality_report.json
                         |
              data_loader.load_processed()   (st.cache_data in app.py)
                         |
   filters (analytics.apply_filters, in pandas)  --> filtered DataFrame
        |                         |                              |
  metrics.py (definitions)   database.py: DuckDB + named SQL   forecasting / segmentation
        \_____________________ analytics.py ____________________/
             |                 |                    |                  |
        pages/overview    pages/explore      ai_copilot.py     report_generator.py
                                              (intent -> allowlisted tool -> verified facts -> LLM text -> number check)
```
Principles: raw data immutable; cleaning is a pure tested function; every number on screen comes from `metrics.py`/`analytics.py`/approved SQL; the LLM only phrases verified results; the app works with no API key. UI = `components/` (CSS, charts, KPI cards, sidebar + shared filter bar, tables) + one module per page.
