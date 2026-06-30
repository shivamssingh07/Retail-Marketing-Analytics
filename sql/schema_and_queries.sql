-- ============================================================================
-- SQL DDL & Analytics Queries for Retail & Marketing Analytics
-- ============================================================================
-- This script creates a normalized star schema suitable for a data warehouse,
-- then demonstrates typical KPI queries used in dashboards / reports.
--
-- Database: PostgreSQL (adaptable to SQL Server, Snowflake, etc.)
-- Usage:
--   psql -U postgres -d retail_analytics < sql/schema_and_queries.sql


-- ============================================================================
-- 1. DIMENSION TABLES (slowly changing dimensions)
-- ============================================================================

-- Customers Dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(255),
    segment VARCHAR(50),
    region VARCHAR(50),
    first_purchase_date TIMESTAMP,
    last_purchase_date TIMESTAMP,
    lifetime_value DECIMAL(12,2),
    clv_category VARCHAR(20),
    customer_segment VARCHAR(50),  -- RFM segment
    cluster_name VARCHAR(50),       -- KMeans cluster
    churn_risk DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(255),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    unit_price DECIMAL(10,2),
    total_sales DECIMAL(12,2),
    avg_order_value DECIMAL(10,2),
    order_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE UNIQUE,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day_of_month INT,
    day_of_week INT,
    day_name VARCHAR(20),
    week_of_year INT,
    is_weekend INT,
    is_month_start INT,
    is_month_end INT,
    season VARCHAR(20)
);

-- Geography Dimension
CREATE TABLE IF NOT EXISTS dim_geography (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(50) UNIQUE
);

-- ============================================================================
-- 2. FACT TABLE (transactional facts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_sales (
    order_id VARCHAR(20) PRIMARY KEY,
    date_id INT REFERENCES dim_date(date_id),
    customer_id VARCHAR(20) REFERENCES dim_customer(customer_id),
    product_id VARCHAR(20) REFERENCES dim_product(product_id),
    region_id INT REFERENCES dim_geography(region_id),
    order_priority VARCHAR(20),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount DECIMAL(5,3),
    sales DECIMAL(12,2),
    profit DECIMAL(12,2),
    shipping_cost DECIMAL(10,2),
    net_revenue DECIMAL(12,2),
    profit_margin DECIMAL(5,2),
    delivery_days INT,
    is_repeat_customer INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast query performance
CREATE INDEX idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_region ON fact_sales(region_id);
CREATE INDEX idx_dim_customer_segment ON dim_customer(customer_segment);
CREATE INDEX idx_dim_customer_churn_risk ON dim_customer(churn_risk);

-- ============================================================================
-- 3. KPI VIEWS & MATERIALIZED TABLES (for dashboard performance)
-- ============================================================================

-- Monthly KPIs View
CREATE OR REPLACE VIEW v_monthly_kpis AS
SELECT
    EXTRACT(YEAR FROM d.full_date)::INT AS year,
    EXTRACT(MONTH FROM d.full_date)::INT AS month,
    d.month_name,
    COUNT(DISTINCT f.order_id) AS order_count,
    COUNT(DISTINCT f.customer_id) AS customer_count,
    SUM(f.quantity) AS units_sold,
    COUNT(DISTINCT f.product_id) AS sku_count,
    SUM(f.sales) AS revenue,
    SUM(f.profit) AS profit,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.customer_id), 0) AS revenue_per_customer,
    SUM(f.quantity) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS items_per_order
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY EXTRACT(YEAR FROM d.full_date), EXTRACT(MONTH FROM d.full_date), d.month_name
ORDER BY year DESC, month DESC;

-- Category KPIs View
CREATE OR REPLACE VIEW v_category_kpis AS
SELECT
    p.category,
    COUNT(DISTINCT f.order_id) AS order_count,
    COUNT(DISTINCT f.customer_id) AS customer_count,
    SUM(f.quantity) AS units_sold,
    COUNT(DISTINCT p.product_id) AS sku_count,
    SUM(f.sales) AS total_revenue,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value,
    SUM(f.sales) / NULLIF(SUM(f.sales) OVER (), 0) * 100 AS revenue_share_pct
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Regional KPIs View
CREATE OR REPLACE VIEW v_regional_kpis AS
SELECT
    g.region_name,
    COUNT(DISTINCT f.order_id) AS order_count,
    COUNT(DISTINCT f.customer_id) AS customer_count,
    SUM(f.quantity) AS units_sold,
    SUM(f.sales) AS total_revenue,
    SUM(f.profit) AS total_profit,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value,
    SUM(f.sales) / NULLIF(SUM(f.sales) OVER (), 0) * 100 AS revenue_share_pct
FROM fact_sales f
JOIN dim_geography g ON f.region_id = g.region_id
GROUP BY g.region_name
ORDER BY total_revenue DESC;

-- Customer Segment KPIs View
CREATE OR REPLACE VIEW v_segment_kpis AS
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(DISTINCT f.order_id) AS order_count,
    SUM(f.sales) AS total_revenue,
    SUM(f.profit) AS total_profit,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT c.customer_id), 0) AS revenue_per_customer,
    AVG(c.lifetime_value) AS avg_clv,
    AVG(c.churn_risk) AS avg_churn_risk
FROM dim_customer c
LEFT JOIN fact_sales f ON c.customer_id = f.customer_id
GROUP BY c.customer_segment
ORDER BY total_revenue DESC;

-- Top Products by Revenue
CREATE OR REPLACE VIEW v_top_products AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT f.order_id) AS order_count,
    SUM(f.quantity) AS units_sold,
    SUM(f.sales) AS total_revenue,
    SUM(f.profit) AS total_profit,
    SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 20;

-- ============================================================================
-- 4. SAMPLE ANALYTICAL QUERIES
-- ============================================================================

-- Query 1: Customer Lifetime Value by Segment (Executive Dashboard)
-- Purpose: Show revenue contribution by customer segment
-- Frequency: Daily / weekly refresh
/*
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS num_customers,
    SUM(c.lifetime_value) AS total_clv,
    AVG(c.lifetime_value) AS avg_clv,
    ROUND(SUM(c.lifetime_value) / SUM(SUM(c.lifetime_value)) OVER () * 100, 2) AS pct_of_total_clv,
    AVG(c.churn_risk) AS avg_churn_risk,
    COUNT(DISTINCT CASE WHEN c.churn_risk > 0.5 THEN c.customer_id END) AS high_risk_count
FROM dim_customer c
GROUP BY c.customer_segment
ORDER BY total_clv DESC;
*/

-- Query 2: Monthly Revenue Trend with YoY Comparison
-- Purpose: Track revenue momentum and seasonality
-- Frequency: Daily
/*
SELECT
    d.year,
    d.month,
    d.month_name,
    SUM(f.sales) AS revenue,
    LAG(SUM(f.sales)) OVER (PARTITION BY d.month ORDER BY d.year) AS prior_year_revenue,
    ROUND((SUM(f.sales) - LAG(SUM(f.sales)) OVER (PARTITION BY d.month ORDER BY d.year)) 
        / LAG(SUM(f.sales)) OVER (PARTITION BY d.month ORDER BY d.year) * 100, 2) AS yoy_growth_pct
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.year IN (EXTRACT(YEAR FROM CURRENT_DATE), EXTRACT(YEAR FROM CURRENT_DATE) - 1)
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year DESC, d.month DESC;
*/

-- Query 3: Cohort Retention (Customer Acquisition Cohort)
-- Purpose: Understand customer lifecycle and engagement patterns
-- Frequency: Monthly
/*
WITH customer_cohort AS (
    SELECT
        c.customer_id,
        EXTRACT(YEAR FROM c.first_purchase_date)::INT || '-' || 
        LPAD(EXTRACT(MONTH FROM c.first_purchase_date)::TEXT, 2, '0') AS cohort_month,
        MIN(d.full_date) AS cohort_date
    FROM dim_customer c
    JOIN fact_sales f ON c.customer_id = f.customer_id
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY c.customer_id, cohort_month
)
SELECT
    cc.cohort_month,
    EXTRACT(YEAR FROM d.full_date)::INT || '-' || 
    LPAD(EXTRACT(MONTH FROM d.full_date)::TEXT, 2, '0') AS activity_month,
    COUNT(DISTINCT cc.customer_id) AS active_customers,
    ROUND(COUNT(DISTINCT cc.customer_id) * 100.0 / 
        (SELECT COUNT(DISTINCT customer_id) FROM customer_cohort WHERE cohort_month = cc.cohort_month), 2) AS retention_pct
FROM customer_cohort cc
JOIN fact_sales f ON cc.customer_id = f.customer_id
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY cc.cohort_month, activity_month
ORDER BY cc.cohort_month, activity_month;
*/

-- Query 4: Discount Impact Analysis
-- Purpose: Measure how discounts affect profitability
-- Frequency: Weekly
/*
SELECT
    CASE 
        WHEN discount = 0 THEN 'No Discount'
        WHEN discount BETWEEN 0.01 AND 0.1 THEN '1-10%'
        WHEN discount BETWEEN 0.11 AND 0.2 THEN '11-20%'
        ELSE '20%+'
    END AS discount_band,
    COUNT(DISTINCT f.order_id) AS order_count,
    COUNT(DISTINCT f.customer_id) AS customer_count,
    SUM(f.sales) AS total_revenue,
    SUM(f.profit) AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales), 0) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(f.sales) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value
FROM fact_sales f
GROUP BY discount_band
ORDER BY discount_band;
*/

-- Query 5: At-Risk Customer Identification
-- Purpose: Identify churned / at-risk customers for retention campaigns
-- Frequency: Weekly (real-time scoring)
/*
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.cluster_name,
    c.lifetime_value,
    c.churn_risk,
    c.last_purchase_date,
    CURRENT_DATE - c.last_purchase_date::DATE AS days_since_purchase,
    COUNT(DISTINCT f.order_id) AS recent_orders_last_30d
FROM dim_customer c
LEFT JOIN fact_sales f ON c.customer_id = f.customer_id
    AND f.date_id >= (SELECT EXTRACT(YEAR FROM CURRENT_DATE)::INT * 10000 + 
                             EXTRACT(MONTH FROM CURRENT_DATE)::INT * 100 + 1 
                      FROM dim_date 
                      WHERE full_date >= CURRENT_DATE - INTERVAL '30 days')
WHERE c.churn_risk > 0.5
   OR (CURRENT_DATE - c.last_purchase_date::DATE) > 90
GROUP BY c.customer_id, c.customer_name, c.customer_segment, c.cluster_name, 
         c.lifetime_value, c.churn_risk, c.last_purchase_date
ORDER BY c.churn_risk DESC, c.lifetime_value DESC
LIMIT 100;
*/

-- ============================================================================
-- 5. DATA QUALITY / AUDIT QUERIES
-- ============================================================================

-- Query 6: Data Freshness Check
-- Purpose: Ensure data pipeline is running
/*
SELECT
    'Fact Sales' AS table_name,
    COUNT(*) AS row_count,
    MAX(created_at) AS last_update,
    CURRENT_TIMESTAMP - MAX(created_at) AS hours_since_update
FROM fact_sales
UNION ALL
SELECT
    'Dim Customer',
    COUNT(*),
    MAX(updated_at),
    CURRENT_TIMESTAMP - MAX(updated_at)
FROM dim_customer;
*/

-- Query 7: Missing Value Detection
-- Purpose: Monitor data quality issues
/*
SELECT
    'fact_sales' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(CASE WHEN order_id IS NULL THEN 1 END) AS null_order_id,
    COUNT(CASE WHEN customer_id IS NULL THEN 1 END) AS null_customer_id,
    COUNT(CASE WHEN product_id IS NULL THEN 1 END) AS null_product_id,
    COUNT(CASE WHEN sales IS NULL THEN 1 END) AS null_sales
FROM fact_sales
UNION ALL
SELECT
    'dim_customer',
    COUNT(*),
    COUNT(CASE WHEN customer_id IS NULL THEN 1 END),
    COUNT(CASE WHEN customer_name IS NULL THEN 1 END),
    COUNT(CASE WHEN lifetime_value IS NULL THEN 1 END),
    0
FROM dim_customer;
*/
