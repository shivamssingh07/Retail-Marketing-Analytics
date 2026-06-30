-- =============================================================================
-- 03_customer_segmentation_queries.sql
-- RFM segmentation and customer-tier analysis, written entirely in SQL using
-- window functions (NTILE) so the logic is portable to any BI tool that can
-- query the warehouse directly, without needing the Python RFM script.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. RFM BASE METRICS PER CUSTOMER
-- -----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) + INTERVAL '1 day' AS snapshot_date FROM fact_sales
),
rfm_base AS (
    SELECT
        f.customer_id,
        (SELECT snapshot_date FROM snapshot)::DATE - MAX(f.order_date)  AS recency_days,
        COUNT(DISTINCT f.order_id)                                       AS frequency,
        SUM(f.revenue)                                                   AS monetary
    FROM fact_sales f
    GROUP BY f.customer_id
)
SELECT * FROM rfm_base ORDER BY monetary DESC;

-- -----------------------------------------------------------------------------
-- 2. RFM SCORING (QUINTILES 1-5) + COMBINED SEGMENT LABEL
-- -----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) + INTERVAL '1 day' AS snapshot_date FROM fact_sales
),
rfm_base AS (
    SELECT
        f.customer_id,
        (SELECT snapshot_date FROM snapshot)::DATE - MAX(f.order_date)  AS recency_days,
        COUNT(DISTINCT f.order_id)                                       AS frequency,
        SUM(f.revenue)                                                   AS monetary
    FROM fact_sales f
    GROUP BY f.customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        -- Recency: LOWER is better -> reverse the quintile (5 = most recent)
        6 - NTILE(5) OVER (ORDER BY recency_days)   AS r_score,
        NTILE(5) OVER (ORDER BY frequency)          AS f_score,
        NTILE(5) OVER (ORDER BY monetary)           AS m_score
    FROM rfm_base
)
SELECT
    *,
    (r_score + f_score + m_score)                       AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4  THEN 'Cannot Lose Them'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2  THEN 'Lost'
        ELSE 'Need Attention'
    END AS customer_segment
FROM rfm_scored
ORDER BY rfm_total DESC;

-- -----------------------------------------------------------------------------
-- 3. SEGMENT-LEVEL ROLLUP: SIZE, REVENUE SHARE, AVG ENGAGEMENT
-- -----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) + INTERVAL '1 day' AS snapshot_date FROM fact_sales
),
rfm_base AS (
    SELECT
        f.customer_id,
        (SELECT snapshot_date FROM snapshot)::DATE - MAX(f.order_date)  AS recency_days,
        COUNT(DISTINCT f.order_id)                                       AS frequency,
        SUM(f.revenue)                                                   AS monetary
    FROM fact_sales f
    GROUP BY f.customer_id
),
rfm_scored AS (
    SELECT
        customer_id, recency_days, frequency, monetary,
        6 - NTILE(5) OVER (ORDER BY recency_days)   AS r_score,
        NTILE(5) OVER (ORDER BY frequency)          AS f_score,
        NTILE(5) OVER (ORDER BY monetary)           AS m_score
    FROM rfm_base
),
segmented AS (
    SELECT *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score <= 2                  THEN 'New Customers'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3  THEN 'At Risk'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4  THEN 'Cannot Lose Them'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2  THEN 'Lost'
            ELSE 'Need Attention'
        END AS customer_segment
    FROM rfm_scored
)
SELECT
    customer_segment,
    COUNT(*)                                                          AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)                  AS pct_of_customers,
    SUM(monetary)                                                      AS total_revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 2)        AS pct_of_revenue,
    ROUND(AVG(frequency), 2)                                            AS avg_frequency,
    ROUND(AVG(recency_days), 1)                                         AS avg_recency_days
FROM segmented
GROUP BY customer_segment
ORDER BY total_revenue DESC;

-- -----------------------------------------------------------------------------
-- 4. CUSTOMERS AT HIGHEST CHURN RISK (Recency > 90 days, previously high value)
-- -----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) + INTERVAL '1 day' AS snapshot_date FROM fact_sales
),
rfm_base AS (
    SELECT
        f.customer_id,
        c.customer_name,
        (SELECT snapshot_date FROM snapshot)::DATE - MAX(f.order_date)  AS recency_days,
        COUNT(DISTINCT f.order_id)                                       AS frequency,
        SUM(f.revenue)                                                   AS monetary
    FROM fact_sales f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    GROUP BY f.customer_id, c.customer_name
)
SELECT customer_id, customer_name, recency_days, frequency, monetary
FROM rfm_base
WHERE recency_days > 90
  AND monetary > (SELECT AVG(monetary) FROM rfm_base)
ORDER BY monetary DESC
LIMIT 50;

-- -----------------------------------------------------------------------------
-- 5. CUSTOMER SEGMENT BY ACQUISITION SEGMENT (Consumer/Corporate/Home Office)
-- Cross-tab of the dataset's native "Segment" dimension against RFM tier
-- -----------------------------------------------------------------------------
WITH snapshot AS (
    SELECT MAX(order_date) + INTERVAL '1 day' AS snapshot_date FROM fact_sales
),
rfm_base AS (
    SELECT
        f.customer_id,
        c.segment,
        (SELECT snapshot_date FROM snapshot)::DATE - MAX(f.order_date)  AS recency_days,
        COUNT(DISTINCT f.order_id)                                       AS frequency,
        SUM(f.revenue)                                                   AS monetary
    FROM fact_sales f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    GROUP BY f.customer_id, c.segment
),
rfm_scored AS (
    SELECT *,
        6 - NTILE(5) OVER (ORDER BY recency_days)   AS r_score,
        NTILE(5) OVER (ORDER BY frequency)          AS f_score,
        NTILE(5) OVER (ORDER BY monetary)           AS m_score
    FROM rfm_base
)
SELECT
    segment,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3  THEN 'At Risk'
        ELSE 'Other'
    END AS rfm_tier,
    COUNT(*) AS customer_count,
    SUM(monetary) AS total_revenue
FROM rfm_scored
GROUP BY 1, 2
ORDER BY 1, total_revenue DESC;
