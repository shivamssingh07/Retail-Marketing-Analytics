-- =============================================================================
-- 05_cohort_retention_queries.sql
-- Monthly acquisition-cohort retention analysis, written in pure SQL.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ASSIGN EACH CUSTOMER TO THEIR ACQUISITION COHORT (month of first order)
-- -----------------------------------------------------------------------------
WITH first_order AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
)
SELECT customer_id, cohort_month FROM first_order ORDER BY cohort_month;

-- -----------------------------------------------------------------------------
-- 2. COHORT INDEX PER ORDER (how many months after acquisition was this order?)
-- -----------------------------------------------------------------------------
WITH first_order AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        f.customer_id,
        fo.cohort_month,
        DATE_TRUNC('month', f.order_date) AS order_month,
        (
            (EXTRACT(YEAR FROM f.order_date) - EXTRACT(YEAR FROM fo.cohort_month)) * 12
            + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM fo.cohort_month))
        )::INT AS cohort_index
    FROM fact_sales f
    JOIN first_order fo ON fo.customer_id = f.customer_id
)
SELECT * FROM orders_with_cohort ORDER BY cohort_month, cohort_index;

-- -----------------------------------------------------------------------------
-- 3. RETENTION TABLE: active customers per (cohort_month, cohort_index)
-- -----------------------------------------------------------------------------
WITH first_order AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        f.customer_id,
        fo.cohort_month,
        (
            (EXTRACT(YEAR FROM f.order_date) - EXTRACT(YEAR FROM fo.cohort_month)) * 12
            + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM fo.cohort_month))
        )::INT AS cohort_index
    FROM fact_sales f
    JOIN first_order fo ON fo.customer_id = f.customer_id
),
cohort_counts AS (
    SELECT cohort_month, cohort_index, COUNT(DISTINCT customer_id) AS active_customers
    FROM orders_with_cohort
    GROUP BY cohort_month, cohort_index
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM cohort_counts
    WHERE cohort_index = 0
)
SELECT
    cc.cohort_month,
    cc.cohort_index,
    cc.active_customers,
    cs.cohort_size,
    ROUND(100.0 * cc.active_customers / cs.cohort_size, 2) AS retention_pct
FROM cohort_counts cc
JOIN cohort_sizes cs ON cs.cohort_month = cc.cohort_month
ORDER BY cc.cohort_month, cc.cohort_index;

-- -----------------------------------------------------------------------------
-- 4. PIVOTED RETENTION HEATMAP (Postgres crosstab-style using conditional MAX)
-- For a true PIVOT, use the `tablefunc` extension's CROSSTAB(), or pivot in
-- the BI tool / pandas layer. This version returns a wide table for months 0-6.
-- -----------------------------------------------------------------------------
WITH first_order AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        f.customer_id,
        fo.cohort_month,
        (
            (EXTRACT(YEAR FROM f.order_date) - EXTRACT(YEAR FROM fo.cohort_month)) * 12
            + (EXTRACT(MONTH FROM f.order_date) - EXTRACT(MONTH FROM fo.cohort_month))
        )::INT AS cohort_index
    FROM fact_sales f
    JOIN first_order fo ON fo.customer_id = f.customer_id
),
cohort_counts AS (
    SELECT cohort_month, cohort_index, COUNT(DISTINCT customer_id) AS active_customers
    FROM orders_with_cohort
    GROUP BY cohort_month, cohort_index
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM cohort_counts WHERE cohort_index = 0
)
SELECT
    cc.cohort_month,
    cs.cohort_size,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 0 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_0,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 1 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_1,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 2 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_2,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 3 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_3,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 4 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_4,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 5 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_5,
    ROUND(100.0 * MAX(CASE WHEN cc.cohort_index = 6 THEN cc.active_customers END) / cs.cohort_size, 1) AS month_6
FROM cohort_counts cc
JOIN cohort_sizes cs ON cs.cohort_month = cc.cohort_month
GROUP BY cc.cohort_month, cs.cohort_size
ORDER BY cc.cohort_month;

-- -----------------------------------------------------------------------------
-- 5. CUSTOMER STATUS THIS MONTH: New / Active / Churned / Reactivated
-- A common "customer movement" report for marketing teams.
-- -----------------------------------------------------------------------------
WITH monthly_activity AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS active_month
    FROM fact_sales
),
flagged AS (
    SELECT
        customer_id,
        active_month,
        LAG(active_month) OVER (PARTITION BY customer_id ORDER BY active_month) AS prev_active_month
    FROM monthly_activity
)
SELECT
    active_month,
    CASE
        WHEN prev_active_month IS NULL THEN 'New'
        WHEN active_month - prev_active_month = INTERVAL '1 month' THEN 'Active (Consecutive)'
        ELSE 'Reactivated'
    END AS customer_status,
    COUNT(*) AS customer_count
FROM flagged
GROUP BY 1, 2
ORDER BY 1, 2;
