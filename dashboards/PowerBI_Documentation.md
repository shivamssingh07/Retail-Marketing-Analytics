# Power BI Documentation
## Retail & Marketing Analytics Dashboard

This document specifies everything needed to rebuild the dashboard in Power
BI Desktop: the data model, calculated columns, DAX measures, page layout,
and visual design strategy. It assumes the star schema produced by
`sql/01_schema_and_tables.sql` (or the equivalent flat file
`data/processed/cleaned_retail_sales.csv` loaded directly and shaped with
Power Query).

---

## 1. Data Model

### Option A — Star schema (recommended)
Import `fact_sales`, `dim_customer`, `dim_product`, `dim_region`, `dim_date`
from the SQL database (or load `cleaned_retail_sales.csv` and split it into
these tables using Power Query `Reference` queries + `Group By`).

```
dim_date ────┐
dim_customer ─┼──< fact_sales (many-to-one, single direction)
dim_product ──┤
dim_region ───┘
```

- All relationships: **1 (dimension) → * (fact)**, single cross-filter
  direction (dimension filters fact).
- Mark `dim_date[date_id]` as the official **Date Table** (Modeling → Mark
  as Date Table) so time-intelligence DAX functions (`DATEADD`,
  `SAMEPERIODLASTYEAR`, etc.) work correctly.

### Option B — Single flat table (quick start)
Load `data/processed/cleaned_retail_sales.csv` directly as one wide table.
Faster to set up; loses some modeling best-practice but every DAX measure
below still works (just swap dimension-table column references for the
flat-table equivalents, e.g. `dim_product[Product_Category]` →
`cleaned_retail_sales[Product_Category]`).

### Supplementary tables to import
- `data/processed/rfm_analysis.csv` → `RFM`
- `data/processed/customer_clv.csv` → `CLV`
- `data/processed/customer_segments.csv` → `Segments`
- `reports/cohort_retention.csv` → `Cohort_Retention`
- `data/processed/churn_predictions.csv` → `Churn_Scores`
- `data/processed/sales_forecast.csv` → `Forecast`

Relate each of these to `dim_customer[customer_id]` (or directly to
`fact_sales[customer_id]` if using the flat-table option) via
`Customer_ID`, single direction, 1-to-1 or 1-to-many as appropriate.

---

## 2. Calculated Columns

Add these in Power Query (preferred, for performance) or as DAX calculated
columns on the relevant table.

```dax
-- On fact_sales: Net Revenue after discount
Net_Revenue = fact_sales[Sales] * (1 - fact_sales[Discount])

-- On fact_sales: Profit Margin %
Profit_Margin_Pct = DIVIDE(fact_sales[Profit], fact_sales[Sales], 0) * 100

-- On fact_sales: Delivery Speed bucket
Delivery_Bucket =
SWITCH(
    TRUE(),
    fact_sales[Delivery_Days] <= 1, "Same/Next Day",
    fact_sales[Delivery_Days] <= 3, "2-3 Days",
    fact_sales[Delivery_Days] <= 7, "4-7 Days",
    "7+ Days"
)

-- On RFM: numeric segment priority for consistent sort order in visuals
Segment_Sort_Order =
SWITCH(
    RFM[Customer_Segment],
    "Champions", 1, "Loyal Customers", 2, "Potential Loyalists", 3,
    "New Customers", 4, "Promising", 5, "Need Attention", 6,
    "About to Sleep", 7, "At Risk", 8, "Cannot Lose Them", 9, "Lost", 10,
    99
)

-- On CLV: simple flag used for slicer/bookmark targeting
Is_High_Value_Customer = IF(CLV[CLV_Category] = "High", 1, 0)
```

---

## 3. DAX Measures

Organize these into a hidden measures table named `_Measures` for a clean
field list (Home → Enter Data → create empty table → move measures into it).

### 3.1 Core Revenue & Profit KPIs
```dax
Total Revenue = SUM(fact_sales[Revenue])

Total Profit = SUM(fact_sales[Profit])

Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)

Total Orders = DISTINCTCOUNT(fact_sales[Order_ID])

Total Units Sold = SUM(fact_sales[Quantity])

Average Order Value =
DIVIDE([Total Revenue], [Total Orders], 0)

Total Customers = DISTINCTCOUNT(fact_sales[Customer_ID])

Revenue per Customer = DIVIDE([Total Revenue], [Total Customers], 0)

Avg Items per Order = DIVIDE([Total Units Sold], [Total Orders], 0)
```

### 3.2 Growth / Time-Intelligence (requires Date Table marked)
```dax
Revenue PM (Prior Month) =
CALCULATE([Total Revenue], DATEADD(dim_date[date_id], -1, MONTH))

Revenue MoM Growth % =
DIVIDE([Total Revenue] - [Revenue PM (Prior Month)], [Revenue PM (Prior Month)], 0)

Revenue PY (Prior Year) =
CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[date_id]))

Revenue YoY Growth % =
DIVIDE([Total Revenue] - [Revenue PY (Prior Year)], [Revenue PY (Prior Year)], 0)

Revenue YTD =
TOTALYTD([Total Revenue], dim_date[date_id])

Cumulative Revenue =
CALCULATE(
    [Total Revenue],
    FILTER(ALLSELECTED(dim_date), dim_date[date_id] <= MAX(dim_date[date_id]))
)
```

### 3.3 Customer / Retention KPIs
```dax
Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[Customer_ID]),
    FILTER(
        VALUES(fact_sales[Customer_ID]),
        CALCULATE(DISTINCTCOUNT(fact_sales[Order_ID])) > 1
    )
)

Repeat Customer Rate % = DIVIDE([Repeat Customers], [Total Customers], 0)

Churned Customers =
CALCULATE(COUNTROWS(RFM), RFM[Recency] > 180)

Churn Rate % = DIVIDE([Churned Customers], COUNTROWS(RFM), 0)

Retention Rate % = 1 - [Churn Rate %]

Average CLV = AVERAGE(CLV[CLV_Simple])

CLV to CAC Ratio = DIVIDE([Average CLV], 50, 0)   -- 50 = assumed blended CAC; expose as a What-If parameter (see §3.5)

Average Recency (days) = AVERAGE(RFM[Recency])
```

### 3.4 Segmentation KPIs
```dax
VIP Customer Count =
CALCULATE(COUNTROWS(Segments), Segments[Cluster_Name] = "VIP Customers")

VIP Revenue Share % =
VAR VIPRevenue =
    CALCULATE(SUM(Segments[Monetary]), Segments[Cluster_Name] = "VIP Customers")
VAR TotalRevenue = SUM(Segments[Monetary])
RETURN DIVIDE(VIPRevenue, TotalRevenue, 0)

Selected Segment Revenue =
CALCULATE(SUM(Segments[Monetary]))   -- responds to a Cluster_Name slicer
```

### 3.5 What-If Parameter — Customer Acquisition Cost (CAC)
Modeling → New Parameter → "What if parameter":
- Name: `CAC Assumption`
- Data type: Decimal
- Range: 10 to 200, increment 5, default 50

```dax
CLV to CAC Ratio (Dynamic) = DIVIDE([Average CLV], 'CAC Assumption'[CAC Assumption Value], 0)
```
Drop the generated `CAC Assumption` slicer on the Marketing page so
stakeholders can stress-test the ratio live.

### 3.6 Forecast & Variance
```dax
Forecasted Revenue = SUM(Forecast[Forecasted_Revenue])

Forecast vs Actual Variance =
[Total Revenue] - [Forecasted Revenue]

Forecast Accuracy % =
1 - DIVIDE(ABS([Forecast vs Actual Variance]), [Total Revenue], 0)
```

### 3.7 Conditional Formatting Helper Measures
```dax
Profit Margin KPI Color =
SWITCH(
    TRUE(),
    [Profit Margin %] >= 0.20, "#16A34A",   -- green
    [Profit Margin %] >= 0.10, "#F59E0B",   -- amber
    "#DC2626"                                -- red
)

Churn Risk Color =
SWITCH(
    TRUE(),
    SELECTEDVALUE(Churn_Scores[Risk_Tier]) = "High Risk", "#DC2626",
    SELECTEDVALUE(Churn_Scores[Risk_Tier]) = "Medium Risk", "#F59E0B",
    "#16A34A"
)
```

---

## 4. Dashboard Layout (4 pages)

### Page 1 — Executive Overview
| Zone | Visual | Measures |
|---|---|---|
| Top KPI strip (6 cards) | Card visuals | Total Revenue, Total Profit, Profit Margin %, Total Orders, Total Customers, AOV |
| Top-left | Line chart | Total Revenue & Revenue YoY Growth % by Month |
| Top-right | Donut | Revenue by Order_Priority |
| Bottom-left | Combo bar/line | Quarterly Revenue vs Profit |
| Bottom-right | Bar | Revenue by Region |
| Slicers (top bar) | Date range, Region, Product_Category | applies to whole page |

### Page 2 — Customer Analytics
| Zone | Visual | Measures |
|---|---|---|
| KPI strip | Cards | Total Customers, Repeat Customer Rate %, Churn Rate %, Average CLV, CLV to CAC Ratio |
| Left | Donut | Customer count by `Segments[Cluster_Name]` |
| Center | Scatter | Recency (x) vs Monetary (y), size = Frequency, color = Cluster_Name |
| Right | Matrix | Cluster_Name × Avg Recency / Avg Frequency / Avg Monetary / Revenue Share % |
| Bottom | Heatmap matrix | Cohort_Month (rows) × Cohort_Index (columns) = Retention % (conditional formatting, green→red) |

### Page 3 — Product Performance
| Zone | Visual | Measures |
|---|---|---|
| Left | Bar (horizontal) | Revenue by Product_Category |
| Center | Table | Top 10 products: Total_Revenue, Units_Sold, Order_Count |
| Right | Matrix heatmap | Product_Category × Region = Avg Profit Margin % |
| Bottom | Bar | Discount bucket vs Avg Profit Margin % |

### Page 4 — Marketing & Forecast
| Zone | Visual | Measures |
|---|---|---|
| KPI strip | Cards | Average CLV, CLV/CAC Ratio (Dynamic), CAC Assumption slicer, Forecast Accuracy % |
| Left | Line | Historical Revenue + Forecasted Revenue (dashed) |
| Right | Table | Churn_Scores sorted by Churn_Probability desc, conditional formatting via Churn Risk Color |
| Bottom | Funnel/bar | Customer count by RFM Customer_Segment (Champions → Lost) |

---

## 5. Visual Design Strategy

- **Color system**: Primary `#2563EB` (revenue/primary KPIs), Accent
  `#16A34A` (positive/profit/retention), Warning `#DC2626` (churn/risk),
  Neutral `#6B7280` (secondary text/gridlines). Keep this palette
  consistent across every page — it's what makes a recruiter believe the
  dashboard is "real" rather than a default-theme export.
- **Typography**: Segoe UI (Power BI default) for body, bold for KPI card
  values; keep card value font size noticeably larger than the label.
- **Layout discipline**: 12-column grid, consistent 8px gutters, KPI cards
  always pinned to the top of the page so users orient instantly.
- **Conditional formatting everywhere a number can be "good" or "bad"**:
  profit margin, churn rate, retention rate, forecast variance.
- **Tooltips**: build a custom tooltip page showing a mini trend sparkline
  for revenue when hovering over any region/category bar.
- **Drill-through**: enable drill-through from the Executive Overview page
  to the Customer Analytics page, filtered by the clicked Region.
- **Bookmarks**: create a "Reset Filters" bookmark + button on every page.
- **Accessibility**: every color-coded status also gets a text/icon
  redundant cue (e.g. ▲/▼ arrows alongside green/red growth %).

---

## 6. Suggested File Naming & Publishing
- File: `Retail_Marketing_Analytics_Dashboard.pbix`
- Workspace: `Retail Analytics — Portfolio`
- Refresh: configure a scheduled refresh (daily) against the SQL warehouse
  if deployed; otherwise refresh manually after re-running
  `python run_pipeline.py`.
