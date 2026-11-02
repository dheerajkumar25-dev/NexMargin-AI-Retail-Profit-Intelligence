# Data dictionary

**Source:** Kaggle "Superstore Dataset" (vivek468), the widely used Sample Superstore export: 9,994 raw order lines (9,993 after removing one duplicate), 2014-01-03 to 2017-12-30, US retail.
**Licence:** not verified. Check the Kaggle dataset page before redistributing. For that reason the raw CSV is git-ignored and fetched by `scripts/build_data.py`.
**Currency:** US dollars. No conversion to INR is applied.
**Nature:** a commonly used sample dataset, not data from a real company that you can attribute to a named business.

| Column | Type | Notes |
|---|---|---|
| order_id, customer_id, product_id | text | keys; Customer ID maps to one name; 32 Product IDs have 2+ names, canonicalised to the most frequent |
| order_date, ship_date | date | source format is month-first (M/D/YYYY) |
| segment, region, category, subcategory | text | Consumer/Corporate/Home Office; East/West/Central/South; 3 categories, 17 sub-categories |
| sales, quantity, discount, profit | number | from source; discount is a fraction (0.2 = 20%) |
| **cost** | number | **derived**: sales - profit. Source has no cost column |
| discount_pct | number | derived: discount x 100 |
| order_month, order_year | date/int | derived from order_date |
| is_loss | bool | profit < 0 |
| is_profit_outlier | bool | profit beyond 3 x IQR; flagged, not removed |
