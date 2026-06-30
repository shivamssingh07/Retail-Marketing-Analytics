-- =============================================================================
-- 02_kpi_queries.sql
-- Core business KPI queries against the fact_sales / dim_* star schema.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. HEADLINE KPI SUMMARY (single-row scorecard)
-- -----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT f.order_id)                              AS total_orders,
    COUNT(DISTINCT f.customer_id)                            AS total_customers,
    SUM(f.revenue)                                           AS total_revenue,
    SUM(f.profit)                                            AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.revenue), 0) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 2)     AS avg_order_value,
    SUM(f.quantity)                                          AS total_units_sold,
    ROUND(SUM(f.revenue) / COUNT(DISTINCT f.customer_id), 2)  AS revenue_per_customer
FROM fact_sales f;

-- -----------------------------------------------------------------------------
-- 2. MONTHLY REVENUE & ORDER TREND (with MoM growth via window function)
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', f.order_date)::DATE AS month,
        SUM(f.revenue)                          AS revenue,
        COUNT(DISTINCT f.order_id)              AS orders,
        COUNT(DISTINCT f.customer_id)           AS customers
    FROM fact_sales f
    GROUP BY 1
)
SELECT
    month,
    revenue,
    orders,
    customers,
    ROUND(revenue / NULLIF(orders, 0), 2)                                AS avg_order_value,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2
    )                                                                     AS revenue_growth_pct_mom,
    ROUND(
        (customers - LAG(customers) OVER (ORDER BY month))
        / NULLIF(LAG(customers) OVER (ORDER BY month), 0) * 100, 2
    )                                                                     AS customer_growth_pct_mom
FROM monthly
ORDER BY month;

-- -----------------------------------------------------------------------------
-- 3. KPIs BY PRODUCT CATEGORY (with revenue share of total)
-- -----------------------------------------------------------------------------
SELECT
    p.product_category,
    COUNT(DISTINCT f.order_id)                              AS order_count,
    COUNT(DISTINCT f.customer_id)                            AS customer_count,
    SUM(f.quantity)                                          AS units_sold,
    SUM(f.revenue)                                           AS total_revenue,
    ROUND(AVG(f.revenue), 2)                                  AS avg_order_value,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.revenue), 0) * 100, 2)  AS profit_margin_pct,
    ROUND(
        100.0 * SUM(f.revenue) / SUM(SUM(f.revenue)) OVER (), 2
    )                                                          AS revenue_share_pct
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_category
ORDER BY total_revenue DESC;

-- -----------------------------------------------------------------------------
-- 4. KPIs BY REGION
-- -----------------------------------------------------------------------------
SELECT
    f.region,
    COUNT(DISTINCT f.order_id)                          AS order_count,
    COUNT(DISTINCT f.customer_id)                        AS customer_count,
    SUM(f.revenue)                                       AS total_revenue,
    ROUND(AVG(f.revenue), 2)                              AS avg_order_value,
    ROUND(
        100.0 * COUNT(DISTINCT f.customer_id)
        / (SELECT COUNT(DISTINCT customer_id) FROM fact_sales), 2
    )                                                      AS customer_penetration_pct
FROM fact_sales f
GROUP BY f.region
ORDER BY total_revenue DESC;

-- -----------------------------------------------------------------------------
-- 5. TOP 10 PRODUCTS BY REVENUE
-- -----------------------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.product_category,
    SUM(f.revenue)              AS total_revenue,
    SUM(f.quantity)             AS units_sold,
    COUNT(DISTINCT f.order_id)  AS order_count,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_id, p.product_name, p.product_category
ORDER BY total_revenue DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- 6. ORDER PRIORITY MIX & AVERAGE DELIVERY PERFORMANCE
-- -----------------------------------------------------------------------------
SELECT
    f.order_priority,
    COUNT(DISTINCT f.order_id)         AS order_count,
    ROUND(AVG(f.delivery_days), 2)      AS avg_delivery_days,
    SUM(f.revenue)                      AS total_revenue
FROM fact_sales f
GROUP BY f.order_priority
ORDER BY order_count DESC;

-- -----------------------------------------------------------------------------
-- 7. DISCOUNT IMPACT ON PROFIT MARGIN (bucketed)
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN f.discount = 0           THEN 'No Discount'
        WHEN f.discount <= 0.10       THEN '1-10%'
        WHEN f.discount <= 0.20       THEN '11-20%'
        ELSE '21%+'
    END                                                       AS discount_bucket,
    COUNT(*)                                                  AS line_count,
    ROUND(AVG(f.profit / NULLIF(f.revenue, 0)) * 100, 2)       AS avg_profit_margin_pct,
    SUM(f.revenue)                                            AS total_revenue
FROM fact_sales f
GROUP BY 1
ORDER BY MIN(f.discount);

-- -----------------------------------------------------------------------------
-- 8. CUSTOMER ACQUISITION TREND (new customers per month)
-- -----------------------------------------------------------------------------
WITH first_orders AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM fact_sales
    GROUP BY customer_id
)
SELECT
    DATE_TRUNC('month', first_order_date)::DATE AS acquisition_month,
    COUNT(*)                                    AS new_customers
FROM first_orders
GROUP BY 1
ORDER BY 1;
