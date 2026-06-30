# Power BI Dashboard Design Guide & DAX Formulas
## Retail & Marketing Analytics

---

## 📊 Dashboard Architecture

**File:** `retail_analytics_dashboard.pbix`  
**Refresh Frequency:** Daily (via Airflow / Power Automate)  
**Data Sources:** SQL Server fact/dim tables OR CSV imports from `reports/` directory

### Page Structure (6 Pages)

```
1. EXECUTIVE DASHBOARD
   ├── KPI Cards (Revenue, Orders, Customers, AOV, Profit Margin)
   ├── Revenue Trend (Line chart, YTD + Prior Year comparison)
   ├── Customer Lifecycle (Donut: New, Repeat, At-Risk, Lost)
   └── Regional Revenue & Profit (Clustered bar + map visual)

2. REVENUE & PRODUCT ANALYTICS
   ├── Category Revenue Breakdown (Stacked bar, % of total)
   ├── Top 10 Products (Table: SKU, Revenue, Units, Margin%)
   ├── AOV Trend by Category (Line chart with forecast)
   └── Margin Analysis (Scatter: Volume vs Profitability)

3. CUSTOMER SEGMENTATION
   ├── RFM Segment Distribution (Pie: Champions, Loyal, At-Risk, Lost)
   ├── Segment Profiling (Matrix: Avg R/F/M by segment)
   ├── CLV Distribution (Histogram: Low/Medium/High breakdown)
   └── Customer Count by Segment (KPI cards)

4. COHORT & RETENTION
   ├── Monthly Cohort Retention Heatmap (Interactive)
   ├── Retention Curve by Cohort (Line, avg Month 0–N)
   ├── Churn Rate Trend (Line chart, YTD)
   └── At-Risk Customer Count (KPI + table of top 20)

5. FORECASTING & PREDICTIONS
   ├── 3-Month Revenue Forecast (Area chart: Actual + Forecast)
   ├── Forecast Accuracy (Table: Model comparison MAE/RMSE)
   ├── Churn Probability Distribution (Histogram: Low/Med/High Risk)
   └── Sales Prediction by Category (Projected AOV)

6. OPERATIONAL INSIGHTS
   ├── Orders Over Time (Line: Daily/Weekly aggregation toggle)
   ├── Discount Impact on Profit (Scatter: Discount % vs Margin%)
   ├── Shipping Cost Trend (Line + Target benchmark)
   └── Order Priority Distribution (Pie)
```

---

## 🎨 Design Guidelines

### Color Palette
```
Primary:    #1F77B4 (Dark Blue)   — Revenue, main metrics
Success:    #2CA02C (Green)       — Profit, positive trends
Warning:    #FF7F0E (Orange)      — At-Risk, attention needed
Danger:     #D62728 (Red)         — Lost, churn, negative
Neutral:    #7F7F7F (Gray)        — Axes, labels, background

Accent:     #17BECF (Cyan)        — Highlights
Subtle:     #BCBD22 (Yellow)      — Secondary data
```

### Layout Best Practices
- **Executive Dashboard:** 4–6 visuals max; 1-min understanding time
- **Detail Pages:** 8–12 visuals; grouped by business question
- **KPI Cards:** Large font (28pt); compare YoY or vs target
- **Tables:** Conditional formatting (data bars); top-10 products only
- **Maps:** Regional revenue heatmap (if geography data available)

### Interactivity
- **Slicers:** Date range (default: last 12 months), Region, Category, Segment
- **Cross-filtering:** Click a region to filter all downstream visuals
- **Drill-through:** Segment card → detail page showing all customers in that segment
- **Tooltips:** Custom format with context (e.g., "↑ 12% vs last month")

---

## 📐 DAX Formulas

### Core Measures (Revenue & Profit)

```dax
-- 1. Total Revenue (Explicit)
Total Revenue = SUM('fact_orders'[sales_amount])

-- 2. Total Profit
Total Profit = SUM('fact_orders'[profit_amount])

-- 3. Profit Margin %
Profit Margin % = 
  IFERROR(
    [Total Profit] / [Total Revenue] * 100,
    0
  )

-- 4. Total Orders (Count Distinct)
Total Orders = 
  DISTINCTCOUNT('fact_orders'[order_id])

-- 5. Total Customers (Count Distinct)
Total Customers = 
  DISTINCTCOUNT('fact_orders'[customer_id])

-- 6. Average Order Value (AOV)
AOV = 
  IFERROR(
    [Total Revenue] / [Total Orders],
    0
  )

-- 7. Revenue per Customer
Revenue per Customer = 
  IFERROR(
    [Total Revenue] / [Total Customers],
    0
  )
```

### Year-over-Year Comparisons

```dax
-- 8. Revenue (Current Year)
Revenue CY = 
  CALCULATE(
    [Total Revenue],
    YEAR('dim_calendar'[full_date]) = YEAR(TODAY())
  )

-- 9. Revenue (Prior Year)
Revenue PY = 
  CALCULATE(
    [Total Revenue],
    YEAR('dim_calendar'[full_date]) = YEAR(TODAY()) - 1
  )

-- 10. Revenue YoY Growth %
Revenue YoY Growth % = 
  IFERROR(
    ([Revenue CY] - [Revenue PY]) / [Revenue PY] * 100,
    BLANK()
  )

-- 11. YTD Revenue
Revenue YTD = 
  CALCULATE(
    [Total Revenue],
    DATESYTD('dim_calendar'[full_date])
  )

-- 12. PY YTD Revenue
Revenue PY YTD = 
  CALCULATE(
    [Total Revenue],
    DATESYTD(
      DATEADD('dim_calendar'[full_date], -1, YEAR)
    )
  )
```

### Customer Segment Metrics

```dax
-- 13. RFM Segment Name (via relationship to dim_customer)
RFM Segment = 
  RELATED('dim_customer'[rfm_segment])

-- 14. Cluster Name (Customer Segmentation)
Cluster = 
  RELATED('dim_customer'[cluster_name])

-- 15. Average CLV by Customer
Avg CLV = 
  CALCULATE(
    AVERAGE('dim_customer'[customer_lifetime_value]),
    'dim_customer'[is_active] = 1
  )

-- 16. CLV Category
CLV Category = 
  RELATED('dim_customer'[clv_category])

-- 17. Churn Probability (Average for segment)
Avg Churn Probability = 
  CALCULATE(
    AVERAGE('dim_customer'[churn_probability]),
    'dim_customer'[is_active] = 1
  )

-- 18. Churn Risk Tier
Churn Risk Tier = 
  RELATED('dim_customer'[churn_risk_tier])

-- 19. Customer Count by Churn Risk
High Risk Customers = 
  CALCULATE(
    [Total Customers],
    'dim_customer'[churn_risk_tier] = "High Risk"
  )

-- 20. Churn Rate %
Churn Rate % = 
  IFERROR(
    [High Risk Customers] / [Total Customers] * 100,
    0
  )
```

### Operational Metrics

```dax
-- 21. Units Sold
Units Sold = 
  SUM('fact_orders'[quantity])

-- 22. Discount Amount (Total)
Total Discount Amount = 
  SUM('fact_orders'[discount_pct] * 'fact_orders'[sales_amount])

-- 23. Average Discount %
Avg Discount % = 
  IFERROR(
    AVERAGE('fact_orders'[discount_pct]) * 100,
    0
  )

-- 24. Shipping Cost (Total)
Total Shipping Cost = 
  SUM('fact_orders'[shipping_cost])

-- 25. Average Shipping Cost per Order
Avg Shipping Cost = 
  IFERROR(
    [Total Shipping Cost] / [Total Orders],
    0
  )

-- 26. Net Revenue (Revenue - Discount)
Net Revenue = 
  [Total Revenue] - [Total Discount Amount]

-- 27. Order Count (by Region / Category via relationship)
Orders by Region = 
  CALCULATE(
    [Total Orders],
    ALLEXCEPT('fact_orders', 'dim_region'[region_name])
  )
```

### Retention & Cohort Metrics

```dax
-- 28. Repeat Customer Rate %
Repeat Customer Rate % = 
  IFERROR(
    CALCULATE(
      DISTINCTCOUNT('fact_orders'[customer_id]),
      FILTER('fact_orders', COUNTROWS('fact_orders') > 1)
    ) / [Total Customers] * 100,
    0
  )

-- 29. One-Time Customer Count
One Time Customers = 
  [Total Customers] - 
  CALCULATE(
    DISTINCTCOUNT('fact_orders'[customer_id]),
    FILTER('fact_orders', COUNTROWS('fact_orders') > 1)
  )

-- 30. Average Days Since Last Purchase
Avg Days Since Purchase = 
  IFERROR(
    AVERAGE('dim_customer'[recency_days]),
    0
  )

-- 31. Retention Rate %
Retention Rate % = 
  100 - [Churn Rate %]
```

### Forecasting Metrics

```dax
-- 32. Forecast Revenue (Load from imported forecast table)
Forecast Revenue = 
  SUM('forecast_table'[forecasted_revenue])

-- 33. Forecast vs Actual
Forecast Variance = 
  [Forecast Revenue] - [Total Revenue]

-- 34. Forecast Variance %
Forecast Variance % = 
  IFERROR(
    [Forecast Variance] / [Total Revenue] * 100,
    BLANK()
  )

-- 35. Forecast Accuracy (RMSE proxy)
Forecast Confidence = 
  IF(
    [Forecast Variance %] < 5, 
    "High ✓", 
    IF([Forecast Variance %] < 10, "Medium ~", "Low ✗")
  )
```

### Benchmarking & Targets

```dax
-- 36. Revenue vs Target
Revenue Target = 500000  -- Example: Q1 target

-- 37. Revenue Variance to Target
Revenue Variance to Target = 
  [Total Revenue] - [Revenue Target]

-- 38. Target Achievement %
Target Achievement % = 
  IFERROR(
    [Total Revenue] / [Revenue Target] * 100,
    0
  )

-- 39. Profit Margin Target
Profit Margin Target = 0.25  -- 25% target

-- 40. Margin Variance to Target
Margin Variance to Target = 
  [Profit Margin %] - [Profit Margin Target] * 100
```

### Calculated Columns (for row-level context)

```dax
-- These are added to tables for filtering/grouping

-- 1. Revenue Bracket (in dim_customer)
Revenue Bracket = 
  IF('dim_customer'[customer_lifetime_value] >= 5000, "High",
    IF('dim_customer'[customer_lifetime_value] >= 1000, "Medium", "Low"))

-- 2. Recency Category (in dim_customer)
Recency Status = 
  IF('dim_customer'[recency_days] <= 30, "Active",
    IF('dim_customer'[recency_days] <= 90, "At Risk", "Dormant"))

-- 3. Age of Customer (in dim_customer)
Customer Tenure Months = 
  INT(('dim_customer'[last_purchase_date] - 'dim_customer'[first_purchase_date]) / 30.44)

-- 4. Month-Year (in dim_calendar, for slicer)
Month Year = 
  TEXT('dim_calendar'[full_date], "MMM YYYY")

-- 5. Profit Indicator (in fact_orders, for conditional formatting)
Profit Status = 
  IF('fact_orders'[profit_amount] > 0, "Profitable", "Loss")
```

---

## 📈 Key Visualizations (Step-by-Step Setup)

### 1. Executive KPI Cards

**Visual Type:** KPI Card (or Multi-Row Card)

| Metric | DAX Measure | Format |
|--------|------------|--------|
| Revenue | `[Total Revenue]` | $M.2K |
| Orders | `[Total Orders]` | 0,0 |
| Customers | `[Total Customers]` | 0,0 |
| AOV | `[AOV]` | $0.00 |

**Trend Indicator:** Set "Trend Axis" to `[Revenue YoY Growth %]`  
**Color Coding:** Green if >0%, Red if <0%

---

### 2. Revenue Trend (Line Chart)

**X-Axis:** `dim_calendar[Month Year]`  
**Y-Axis:** `[Total Revenue]` (main), `[Revenue PY]` (comparison)  
**Legend:** Current Year / Prior Year  
**Interactivity:** Hover for exact values; click legend to toggle series

---

### 3. Cohort Retention Heatmap

**Visual Type:** Matrix (Table visual with conditional formatting)

**Rows:** Cohort Month (e.g., "2023-01", "2023-02")  
**Columns:** Cohort Index (0, 1, 2, ..., 12 months post-acquisition)  
**Values:** `[Retention %]` (0–100, text format: "38%")

**Conditional Formatting:**
- **Color Scale:** Yellow (low: 0%) → Blue (high: 100%)
- **Font Color:** Invert (light on dark) for readability
- **Data Bars:** Disabled (too noisy with color scale)

---

### 4. Customer Segmentation Pie

**Legend:** RFM Segment or Cluster Name  
**Values:** Count of Customers (or Revenue if wanting revenue-weighted view)  
**Data Labels:** Both % and count; positioned outside

---

### 5. Churn Risk Donut

**Legend:** High Risk, Medium Risk, Low Risk  
**Color Mapping:**
  - High Risk: #D62728 (Red)
  - Medium Risk: #FF7F0E (Orange)
  - Low Risk: #2CA02C (Green)

**Center Text:** `[Churn Rate %]` + label "Churn %"

---

### 6. Forecast vs Actual Area Chart

**X-Axis:** Date (monthly granularity)  
**Y-Axis (Primary):** Revenue (TL)  
**Area Series 1:** Historical revenue (solid, blue)  
**Area Series 2:** Forecast revenue (dashed, orange)  
**Difference:** Shaded ribbon between actual and forecast

---

## 🔗 Data Model (Relationships)

```
fact_orders [customer_id] ──→ dim_customer [customer_id]
fact_orders [product_id] ──→ dim_product [product_id]
fact_orders [region_id] ──→ dim_region [region_id]
fact_orders [order_date] ──→ dim_calendar [full_date]
fact_orders [ship_date] ──→ dim_calendar [full_date]  (inactive by default)

dim_customer [region_id] ──→ dim_region [region_id]
```

**Star Schema:** fact_orders is the fact table with 4 active dim relationships.

---

## 🔄 Refresh Strategy

**Power Automate Flow** (runs daily at 2 AM):
1. Python script updates CSV files in `reports/`
2. Power BI Desktop refreshes data sources
3. Cloud Service publishes to Power BI Service
4. Email alert if refresh fails (to BI admin)

**Alternative (Direct SQL):**
- Point Power BI directly to SQL Server fact/dim tables
- Incremental refresh: only refresh last 7 days of `fact_orders`
- Scheduled refresh in Power BI Service Admin portal

---

## 🎯 Common Report Views (Filters)

### "Last 12 Months"
- Slicer: Date Range set to `DATERANGE(TODAY()-365, TODAY())`

### "By Region"
- Slicer: Multi-select Region; cross-filter all charts

### "By RFM Segment"
- Slicer: Multi-select RFM_Segment; focus analysis on subset

### "Excluding Outliers"
- Calculated column flag for outliers; slicer to hide them

---

## 📱 Mobile Optimization

**Target:** iPad & iPhone (Responsive design)

- **Landscape (Tablet):** 2-column layout (KPI + chart)
- **Portrait (Phone):** 1-column layout, stacked visuals
- **Font Size:** Min 12pt for readability on small screens
- **Interactive Elements:** Keep slicers above charts (thumb-accessible)

---

## 🚀 Deployment Checklist

- [ ] Data sources connected (SQL or CSV imports)
- [ ] All DAX measures created & tested
- [ ] Relationships validated (no circular logic)
- [ ] All visuals have meaningful titles & axis labels
- [ ] Formatting applied (colors, fonts, conditional formatting)
- [ ] Slicers configured & cross-filtering working
- [ ] Drill-through pages set up (optional)
- [ ] Performance optimized (no slow-loading tables; aggregations pre-computed)
- [ ] Published to Power BI Service
- [ ] Access granted to stakeholders
- [ ] Refresh schedule configured
- [ ] Documentation (this file) shared with team

---

## 🎓 Tips for Interview Success

**"How would you structure this Power BI dashboard?"**
- Explain star schema (fact_orders + 4 dimensions)
- Mention the 6-page layout (Executive → Details → Forecasting)
- Highlight DAX: SUM measures, CALCULATE filters, YoY growth
- Discuss slicers for interactivity

**"Can you walk through a DAX formula?"**
- Pick an example, e.g., `Avg Churn Probability`:
  - "AVERAGE looks at all active customers in the filter context"
  - "CALCULATE changes the context to match selected segment"
  - "IFERROR prevents divide-by-zero errors"

**"How would you optimize this for 100M rows?"**
- Aggregation tables (pre-computed by month/region)
- Incremental refresh (only new data)
- Columnar compression (built-in to PBIX format)
- Avoid calculated columns on large tables; use measures instead

---

## 📚 Further Resources

- [DAX Function Reference](https://dax.guide/) — searchable index
- [Power BI Best Practices](https://docs.microsoft.com/en-us/power-bi/fundamentals/) — Microsoft docs
- [Color Theory for Data Viz](https://www.interaction-design.org/literature/article/color-psychology-in-data-visualisation)

---

**Author:** Data Analytics Team  
**Last Updated:** January 2024  
**Version:** 1.0
