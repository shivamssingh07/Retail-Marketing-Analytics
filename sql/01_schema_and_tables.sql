-- =============================================================================
-- 01_schema_and_tables.sql
-- Retail & Marketing Analytics — Database Schema (Star Schema)
-- =============================================================================
-- Dialect: PostgreSQL (also valid on Snowflake / Redshift with trivial edits;
-- for MySQL/SQL Server, swap SERIAL -> AUTO_INCREMENT/IDENTITY and adjust
-- DATE/TIMESTAMP types as noted inline).
--
-- Design notes:
--   - fact_sales is grain = one row per order line (Order_ID + Product_ID).
--   - Dimensions are deliberately denormalized where useful for BI tools
--     (Power BI / Tableau) that expect a clean star schema.
--   - dim_date is pre-built (not derived at query time) so date filtering
--     and YoY/MoM logic in the BI layer is fast and consistent.
-- =============================================================================

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_date;

-- -----------------------------------------------------------------------------
-- DIM_DATE
-- -----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_id            DATE PRIMARY KEY,
    year               INT NOT NULL,
    month              INT NOT NULL,
    month_name         VARCHAR(15) NOT NULL,
    quarter            INT NOT NULL,
    day                INT NOT NULL,
    day_of_week        INT NOT NULL,        -- 0 = Monday
    day_name           VARCHAR(15) NOT NULL,
    week_of_year       INT NOT NULL,
    is_weekend         BOOLEAN NOT NULL,
    is_month_start     BOOLEAN NOT NULL,
    is_month_end       BOOLEAN NOT NULL,
    season             VARCHAR(10) NOT NULL
);

-- -----------------------------------------------------------------------------
-- DIM_CUSTOMER
-- -----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_id        VARCHAR(20) PRIMARY KEY,
    customer_name       VARCHAR(100),
    segment            VARCHAR(30) NOT NULL,    -- Consumer / Corporate / Home Office
    region             VARCHAR(20) NOT NULL,
    first_purchase_date DATE,
    last_purchase_date  DATE
);

-- -----------------------------------------------------------------------------
-- DIM_PRODUCT
-- -----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_id          VARCHAR(20) PRIMARY KEY,
    product_name         VARCHAR(150),
    product_category      VARCHAR(50) NOT NULL,
    product_sub_category   VARCHAR(50) NOT NULL,
    unit_price            NUMERIC(12, 2)
);

-- -----------------------------------------------------------------------------
-- DIM_REGION  (kept as a small lookup table; region also denormalized onto
-- dim_customer / fact_sales for query convenience in the BI layer)
-- -----------------------------------------------------------------------------
CREATE TABLE dim_region (
    region              VARCHAR(20) PRIMARY KEY,
    region_group        VARCHAR(20)   -- e.g. could roll up to a larger territory
);

-- -----------------------------------------------------------------------------
-- FACT_SALES  (grain: one row per order line)
-- -----------------------------------------------------------------------------
CREATE TABLE fact_sales (
    order_line_id       SERIAL PRIMARY KEY,        -- surrogate key
    order_id            VARCHAR(20) NOT NULL,
    order_date          DATE NOT NULL,
    ship_date           DATE NOT NULL,
    customer_id         VARCHAR(20) NOT NULL REFERENCES dim_customer(customer_id),
    product_id          VARCHAR(20) NOT NULL REFERENCES dim_product(product_id),
    region              VARCHAR(20) NOT NULL REFERENCES dim_region(region),
    order_priority       VARCHAR(20),
    quantity            INT NOT NULL CHECK (quantity > 0),
    discount            NUMERIC(5, 4) NOT NULL CHECK (discount BETWEEN 0 AND 1),
    unit_price           NUMERIC(12, 2) NOT NULL,
    sales               NUMERIC(12, 2) NOT NULL CHECK (sales >= 0),
    revenue             NUMERIC(12, 2) NOT NULL CHECK (revenue >= 0),
    profit              NUMERIC(12, 2) NOT NULL,
    shipping_cost        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    delivery_days        INT
);

CREATE INDEX idx_fact_sales_order_date   ON fact_sales (order_date);
CREATE INDEX idx_fact_sales_customer_id  ON fact_sales (customer_id);
CREATE INDEX idx_fact_sales_product_id   ON fact_sales (product_id);
CREATE INDEX idx_fact_sales_region       ON fact_sales (region);

-- -----------------------------------------------------------------------------
-- LOAD EXAMPLE (PostgreSQL \copy / COPY)
-- -----------------------------------------------------------------------------
-- Adjust paths to your local checkout of /data/processed/cleaned_retail_sales.csv
-- before running. dim_* tables should be loaded first (derived via the
-- staging query below), then fact_sales.
--
-- \copy stg_retail_sales FROM 'data/processed/cleaned_retail_sales.csv' WITH (FORMAT csv, HEADER true);
--
-- INSERT INTO dim_region SELECT DISTINCT region, region FROM stg_retail_sales;
--
-- INSERT INTO dim_customer (customer_id, customer_name, segment, region, first_purchase_date, last_purchase_date)
-- SELECT customer_id, MAX(customer_name), MAX(segment), MAX(region),
--        MIN(order_date), MAX(order_date)
-- FROM stg_retail_sales
-- GROUP BY customer_id;
--
-- INSERT INTO dim_product (product_id, product_name, product_category, product_sub_category, unit_price)
-- SELECT DISTINCT product_id, product_name, product_category, product_sub_category, unit_price
-- FROM stg_retail_sales;
--
-- INSERT INTO fact_sales (order_id, order_date, ship_date, customer_id, product_id, region,
--                          order_priority, quantity, discount, unit_price, sales, revenue,
--                          profit, shipping_cost, delivery_days)
-- SELECT order_id, order_date, ship_date, customer_id, product_id, region,
--        order_priority, quantity, discount, unit_price, sales, revenue,
--        profit, shipping_cost, delivery_days
-- FROM stg_retail_sales;

-- -----------------------------------------------------------------------------
-- A staging table matching the raw CSV 1:1, used purely to bulk-load before
-- fanning data out into the star schema above.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stg_retail_sales (
    order_id              VARCHAR(20),
    order_date            DATE,
    ship_date             DATE,
    customer_id           VARCHAR(20),
    customer_name          VARCHAR(100),
    segment               VARCHAR(30),
    region                VARCHAR(20),
    product_id            VARCHAR(20),
    product_category       VARCHAR(50),
    product_sub_category    VARCHAR(50),
    product_name           VARCHAR(150),
    sales                 NUMERIC(12, 2),
    quantity              INT,
    discount              NUMERIC(5, 4),
    profit                NUMERIC(12, 2),
    shipping_cost          NUMERIC(12, 2),
    order_priority         VARCHAR(20),
    unit_price             NUMERIC(12, 2),
    revenue               NUMERIC(12, 2),
    delivery_days          INT
);
