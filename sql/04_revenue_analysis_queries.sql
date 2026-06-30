-- =============================================================================
-- 04_revenue_analysis_queries.sql
-- Revenue trend, growth, and profitability analysis queries.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. YEAR-OVER-YEAR REVENUE COMPARISON BY MONTH
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        EXTRACT(YEAR FROM order_date)::INT   AS yr,
        EXTRACT(MONTH FROM order_date)::INT  AS mo,
        SUM(revenue)                          AS revenue
    FROM fact_sales
    GROUP BY 1, 2
)
SELECT
    mo AS month,
    MAX(CASE WHEN yr = 2022 THEN revenue END) AS revenue_2022,
    MAX(CASE WHEN yr = 2023 THEN revenue END) AS revenue_2023,
    ROUND(
        100.0 * (MAX(CASE WHEN yr = 2023 THEN revenue END) - MAX(CASE WHEN yr = 2022 THEN revenue END))
        / NULLIF(MAX(CASE WHEN yr = 2022 THEN revenue END), 0), 2
    ) AS yoy_growth_pct
FROM monthly
GROUP BY mo
ORDER BY mo;

-- -----------------------------------------------------------------------------
-- 2. RUNNING (CUMULATIVE) REVENUE TOTAL — useful for YTD progress charts
-- -----------------------------------------------------------------------------
SELECT
    DATE_TRUNC('month', order_date)::DATE                                      AS month,
    SUM(revenue)                                                                 AS monthly_revenue,
    SUM(SUM(revenue)) OVER (ORDER BY DATE_TRUNC('month', order_date))            AS cumulative_revenue
FROM fact_sales
GROUP BY 1
ORDER BY 1;

-- -----------------------------------------------------------------------------
-- 3. QUARTERLY REVENUE & PROFIT COMPARISON
-- -----------------------------------------------------------------------------
SELECT
    EXTRACT(YEAR FROM order_date)::INT      AS year,
    EXTRACT(QUARTER FROM order_date)::INT   AS quarter,
    SUM(revenue)                             AS total_revenue,
    SUM(profit)                              AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS profit_margin_pct,
    COUNT(DISTINCT order_id)                 AS order_count
FROM fact_sales
GROUP BY 1, 2
ORDER BY 1, 2;

-- -----------------------------------------------------------------------------
-- 4. TOP 20 CUSTOMERS BY LIFETIME REVENUE (with rank and revenue share)
-- -----------------------------------------------------------------------------
SELECT
    f.customer_id,
    c.customer_name,
    c.segment,
    SUM(f.revenue)                                              AS lifetime_revenue,
    COUNT(DISTINCT f.order_id)                                  AS order_count,
    ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 2)        AS avg_order_value,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC)                  AS revenue_rank,
    ROUND(100.0 * SUM(f.revenue) / SUM(SUM(f.revenue)) OVER (), 3) AS pct_of_total_revenue
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY f.customer_id, c.customer_name, c.segment
ORDER BY lifetime_revenue DESC
LIMIT 20;

-- -----------------------------------------------------------------------------
-- 5. REVENUE CONCENTRATION (PARETO / 80-20 CHECK)
-- What % of customers generate what % of revenue?
-- -----------------------------------------------------------------------------
WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM fact_sales
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        PERCENT_RANK() OVER (ORDER BY revenue DESC) AS pct_rank_by_revenue
    FROM customer_revenue
)
SELECT
    CASE
        WHEN pct_rank_by_revenue <= 0.10 THEN 'Top 10% of customers'
        WHEN pct_rank_by_revenue <= 0.20 THEN 'Next 10-20%'
        ELSE 'Remaining 80%'
    END AS customer_decile,
    COUNT(*)        AS customer_count,
    SUM(revenue)    AS total_revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS pct_of_total_revenue
FROM ranked
GROUP BY 1
ORDER BY total_revenue DESC;

-- -----------------------------------------------------------------------------
-- 6. PROFIT MARGIN BY CATEGORY x REGION (matrix-style report)
-- -----------------------------------------------------------------------------
SELECT
    p.product_category,
    f.region,
    SUM(f.revenue)                                            AS revenue,
    SUM(f.profit)                                             AS profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.revenue), 0) * 100, 2)  AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_category, f.region
ORDER BY p.product_category, profit_margin_pct DESC;

-- -----------------------------------------------------------------------------
-- 7. DAY-OF-WEEK SEASONALITY
-- -----------------------------------------------------------------------------
SELECT
    TRIM(TO_CHAR(order_date, 'Day'))     AS day_name,
    EXTRACT(ISODOW FROM order_date)::INT AS day_of_week,
    COUNT(DISTINCT order_id)             AS order_count,
    SUM(revenue)                          AS total_revenue,
    ROUND(AVG(revenue), 2)                AS avg_order_value
FROM fact_sales
GROUP BY 1, 2
ORDER BY day_of_week;
