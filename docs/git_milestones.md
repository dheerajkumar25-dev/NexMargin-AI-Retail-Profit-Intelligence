# Git milestones — commit these yourself, as you actually complete and review each
The work is delivered as one folder, so split your commits by area (use `git add -p` or add paths in this order). Do not backdate commits.
1. `chore: initialise project structure and configuration` — requirements, .gitignore, .env.example, config, CLAUDE.md, docs skeleton
2. `feat(data): add dataset loader, cleaning pipeline and validation tests` — preprocessing, data_loader, scripts/build_data.py, tests/test_data.py, data_dictionary
3. `feat(metrics): add centralised business metrics` — metrics.py, formatting.py, tests/test_metrics.py
4. `feat(sql): add DuckDB analytics layer and business queries` — sql/, database.py, analytics.py, tests/test_analytics.py
5. `feat(ui): build Overview dashboard` — components/, pages/overview.py, app.py
6. `feat(ui): build Explore analytics` — pages/explore.py
7. `feat(ai): add safe tool-based AI Copilot with demo mode` — ai_copilot.py, pages/copilot.py, tests/test_copilot.py
8. `feat(ml): add forecasting and RFM segmentation` — forecasting.py, segmentation.py, tests
9. `feat(reports): add PDF and CSV exports` — report_generator.py, pages/reports.py, tests/test_reports.py
10. `docs: add methodology, architecture and interview prep` — README, docs/
11. `style: final UI refinement` — your own polish after viewing the app in a browser
Before pushing: confirm `.env` is not tracked (`git status`) and run `python -m pytest`.
