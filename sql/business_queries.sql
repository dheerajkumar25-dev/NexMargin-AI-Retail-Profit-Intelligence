-- NexMargin business queries (DuckDB). Each block starts with "-- name: <query_name>".
-- Tables/views available: orders (cleaned order lines), dim_customers, dim_products.
-- Values are bound with ? placeholders; queries are never built from user text.

-- name: top_products_by_profit
-- Q1. Top products by profit, with RANK. Params: limit
SELECT RANK() OVER (ORDER BY SUM(o.profit) DESC) AS rank,
       p.product_id, p.product_name, p.category, p.subcategory,
       SUM(o.sales) AS revenue, SUM(o.profit) AS profit,
       SUM(o.profit) / NULLIF(SUM(o.sales), 0) * 100 AS margin_pct
FROM orders o
INNER JOIN dim_products p ON o.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.subcategory
ORDER BY profit DESC
LIMIT ?;

-- name: revenue_by_month
-- Q2. Monthly revenue and profit with running totals (window functions).
WITH monthly AS (
    SELECT order_month AS month, SUM(sales) AS revenue, SUM(profit) AS profit,
           COUNT(DISTINCT order_id) AS orders
    FROM orders GROUP BY order_month
)
SELECT month, revenue, profit,
       profit / NULLIF(revenue, 0) * 100 AS margin_pct, orders,
       SUM(revenue) OVER (ORDER BY month) AS running_revenue,
       SUM(profit)  OVER (ORDER BY month) AS running_profit
FROM monthly
ORDER BY month;

-- name: margin_by_category
-- Q3. Profit margin by category. HAVING drops categories with no revenue.
SELECT category, SUM(sales) AS revenue, SUM(profit) AS profit,
       SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct,
       COUNT(DISTINCT order_id) AS orders
FROM orders
GROUP BY category
HAVING SUM(sales) > 0
ORDER BY margin_pct DESC;

-- name: margin_by_subcategory
-- Q3b. Sub-category margin with DENSE_RANK (1 = best margin).
SELECT category, subcategory, SUM(sales) AS revenue, SUM(profit) AS profit,
       SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct,
       DENSE_RANK() OVER (ORDER BY SUM(profit) / NULLIF(SUM(sales), 0) DESC) AS margin_rank
FROM orders
GROUP BY category, subcategory
HAVING SUM(sales) > 0
ORDER BY margin_pct DESC;

-- name: region_performance
-- Q4. Region performance with share of total revenue (window over aggregates).
SELECT region, SUM(sales) AS revenue, SUM(profit) AS profit,
       SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct,
       COUNT(DISTINCT order_id) AS orders,
       SUM(sales) / NULLIF(SUM(SUM(sales)) OVER (), 0) * 100 AS revenue_share_pct
FROM orders
GROUP BY region
ORDER BY revenue DESC;

-- name: customer_purchase_frequency
-- Q5. How many customers fall in each order-frequency band (LEFT JOIN + CTE + CASE WHEN).
WITH freq AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS n_orders, SUM(sales) AS revenue
    FROM orders GROUP BY customer_id
), counted AS (
    SELECT c.customer_id, COALESCE(f.n_orders, 0) AS n_orders, COALESCE(f.revenue, 0) AS revenue
    FROM dim_customers c LEFT JOIN freq f ON c.customer_id = f.customer_id
)
SELECT CASE WHEN n_orders <= 1 THEN '1 order'
            WHEN n_orders <= 3 THEN '2-3 orders'
            WHEN n_orders <= 6 THEN '4-6 orders'
            ELSE '7+ orders' END AS frequency_band,
       COUNT(*) AS customers, SUM(revenue) AS revenue, AVG(n_orders) AS avg_orders
FROM counted
GROUP BY 1
HAVING COUNT(*) > 0
ORDER BY MIN(n_orders);

-- name: discount_impact
-- Q6. Revenue, profit and margin by discount band.
SELECT CASE WHEN discount_pct = 0 THEN '0%'
            WHEN discount_pct <= 10 THEN '1-10%'
            WHEN discount_pct <= 20 THEN '11-20%'
            WHEN discount_pct < 30 THEN '21-29%'
            WHEN discount_pct < 50 THEN '30-49%'
            ELSE '50%+' END AS discount_band,
       MIN(discount_pct) AS band_order,
       COUNT(*) AS order_lines, SUM(sales) AS revenue, SUM(profit) AS profit,
       SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct,
       AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END) * 100 AS loss_line_pct
FROM orders
GROUP BY 1
ORDER BY band_order;

-- name: monthly_growth
-- Q7. Month-over-month growth using LAG. Same |previous| rule as metrics.growth_pct.
WITH monthly AS (
    SELECT order_month AS month, SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY order_month
)
SELECT month, revenue, profit,
       LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
       (revenue - LAG(revenue) OVER (ORDER BY month))
           / NULLIF(ABS(LAG(revenue) OVER (ORDER BY month)), 0) * 100 AS revenue_mom_pct,
       (profit - LAG(profit) OVER (ORDER BY month))
           / NULLIF(ABS(LAG(profit) OVER (ORDER BY month)), 0) * 100 AS profit_mom_pct
FROM monthly
ORDER BY month;

-- name: segment_profitability
-- Q8. Highest and lowest profitability category x customer-segment cells (RANK + flags).
WITH cells AS (
    SELECT category, segment, SUM(sales) AS revenue, SUM(profit) AS profit,
           SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct
    FROM orders GROUP BY category, segment
)
SELECT category, segment, revenue, profit, margin_pct,
       RANK() OVER (ORDER BY margin_pct DESC) AS margin_rank,
       CASE WHEN margin_pct = MAX(margin_pct) OVER () THEN 'Highest'
            WHEN margin_pct = MIN(margin_pct) OVER () THEN 'Lowest'
            ELSE '' END AS flag
FROM cells
ORDER BY margin_rank;

-- name: top_customers_by_revenue
-- Q9. Top customers by lifetime revenue (INNER JOIN to customer dimension). Params: limit
SELECT DENSE_RANK() OVER (ORDER BY SUM(o.sales) DESC) AS rank,
       c.customer_id, c.customer_name, c.segment,
       SUM(o.sales) AS revenue, SUM(o.profit) AS profit,
       COUNT(DISTINCT o.order_id) AS orders, c.first_order_date
FROM orders o
INNER JOIN dim_customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment, c.first_order_date
ORDER BY revenue DESC
LIMIT ?;

-- name: high_revenue_low_profit
-- Q10. Top-quartile revenue products whose margin is below a threshold. Params: max_margin_pct, limit
WITH prod AS (
    SELECT product_id, SUM(sales) AS revenue, SUM(profit) AS profit,
           SUM(profit) / NULLIF(SUM(sales), 0) * 100 AS margin_pct
    FROM orders GROUP BY product_id
), ranked AS (
    SELECT *, PERCENT_RANK() OVER (ORDER BY revenue) AS revenue_pctile FROM prod
)
SELECT p.product_name, p.category, p.subcategory, r.revenue, r.profit, r.margin_pct
FROM ranked r
INNER JOIN dim_products p ON r.product_id = p.product_id
WHERE r.revenue_pctile >= 0.75 AND r.margin_pct < ?
ORDER BY r.revenue DESC
LIMIT ?;
