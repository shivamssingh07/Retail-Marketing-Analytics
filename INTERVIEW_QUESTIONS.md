# Interview Preparation Questions
## Based on Retail & Marketing Analytics Project

**Total Questions:** 70+ across 4 domains  
**Difficulty:** Beginner to Advanced  
**Context:** Directly tied to the analytics project

---

## 🎯 BEHAVIORAL / SITUATIONAL (General)

*These can be asked regardless of role. Tailor answers to your project.*

### 1. Tell me about a time you completed a complex analytical project from start to finish.

**Suggested Answer Framework:**
- **Situation:** Explain the business problem (e.g., "Company had no way to identify loyal customers or predict churn")
- **Task:** What you were asked to do (e.g., "Build an end-to-end analytics platform")
- **Action:** The specific steps you took (e.g., "Cleaned data → RFM analysis → ML modeling → Streamlit dashboard")
- **Result:** Quantified outcomes (e.g., "95.6% churn prediction accuracy, 55x CLV:CAC ratio, 2-hour automation")

**Pro Tip:** Mention challenges and how you overcame them (e.g., "Data quality issues detected early via Pandera validation, corrected before modeling").

---

### 2. Describe a time you had to translate technical findings into business language for non-technical stakeholders.

**Answer Idea:**
- "I explained the churn prediction model results to the marketing team by saying: 'Our model identifies 1,847 customers with a >40% probability of leaving in the next 90 days. If we retain just 20% of them via a targeted campaign, we'd gain $76k in additional annual revenue.' That made the business case clear."

---

### 3. Walk me through how you would approach a new analytics project.

**Framework (10-stage pipeline example):**
1. Define the business question
2. Assess available data (quality, completeness, timeliness)
3. Design the analytical approach (which metrics, models, visualizations?)
4. Build & validate (code, logging, testing)
5. Analyze & interpret results
6. Create visualizations & dashboards
7. Write executive summary
8. Present findings & recommendations
9. Deploy (if applicable) & monitor
10. Iterate based on feedback

---

### 4. Tell me about a time you failed at something and what you learned.

**Answer Idea:**
- "I initially calculated CLV using the customer's own observed lifespan in both the frequency denominator and the projection multiplier. This algebraically cancelled out, collapsing CLV back to historical revenue. I caught this during validation when the numbers seemed too high. I switched to a fixed 3-year projection horizon, which is the industry standard. Lesson: Always sanity-check formulas with simple test cases."

---

### 5. How do you stay current with new tools and technologies in data analytics?

**Answer Ideas:**
- Mention specific courses, certifications, or online resources
- Reference recent tools you've learned (Streamlit, XGBoost, Power BI, Airflow, etc.)
- Show curiosity about the role and company's tech stack

---

### 6. Tell me about a time you had to deal with incomplete or dirty data.

**Answer (From Project):**
- "Raw data had 10,000 order records. I discovered: 312 missing shipping dates, 45 duplicate order IDs, 87 negative quantities (shipping returns). I created a Pandera validation pipeline that caught these issues before analysis. I handled missing shipping dates with the most common value (median days), flagged duplicates for investigation, and created a 'return' indicator for negative quantities."

---

### 7. Describe your experience working with data warehouses or databases.

**Answer (From Project):**
- "I designed a normalized SQL data warehouse using a star schema: fact_orders at the center connected to dim_customer, dim_product, dim_region, and dim_calendar. This enabled efficient aggregations and OLAP-style analysis. I indexed on key joins (customer_id, product_id, order_date) to ensure query performance."

---

### 8. How do you handle competing priorities or tight deadlines?

**Answer Idea:**
- "I focus on the highest-impact deliverables first (e.g., KPI cards for executives before deep-dive analysis tables). For this project, I prioritized: (1) data cleaning validation (2) RFM segmentation (3) Streamlit dashboard, then added churn ML modeling afterward."

---

### 9. Tell me about a time you had to collaborate across teams.

**Answer Idea:**
- "Working with marketing and product teams, I found that each had a different definition of 'customer churn.' I mediated by defining churn quantitatively (Recency > 180 days) and got buy-in before modeling. This avoided rebuilding the model multiple times."

---

## 📊 DATA ANALYST QUESTIONS (30)

*Focused on analytics methodology, metrics, and business acumen.*

### 10. What is RFM analysis and why is it useful?

**Answer:**
RFM stands for Recency, Frequency, and Monetary. It segments customers based on:
- **Recency:** How recently they purchased (lower = better)
- **Frequency:** How often they purchase (higher = better)  
- **Monetary:** How much they spend (higher = better)

Each dimension is scored 1–5, and combined into an 111–555 RFM score. **Use Cases:** Identify Champions (555), Loyal (445), At-Risk (145), Lost (111) segments for targeted marketing campaigns.

---

### 11. How would you define customer churn and measure it?

**Answer (From Project):**
Churn is a business-specific definition. Options:
- **Behavioral:** Recency > X days (e.g., 180 days)
- **Contract-based:** Explicit cancellation (subscriptions)
- **Activity-based:** No purchases in last 3 months

For this project, I defined churn as Recency > 180 days. This flagged 1,847 dormant customers (35% of base). I validated this definition with stakeholders before modeling.

---

### 12. What is Customer Lifetime Value (CLV) and how do you calculate it?

**Answer:**
CLV is the total profit a customer generates over their relationship with the company.

**Simple Formula:**
```
CLV = (Avg Order Value) × (Purchase Frequency) × (Projection Horizon in Years)
```

**Margin-Adjusted:**
```
CLV = CLV_Simple × (Gross Margin %)
```

**Example from Project:**
- Avg Order Value: $250
- Purchase Frequency: 2/year
- Projection Horizon: 3 years
- Gross Margin: 25%
- CLV = 250 × 2 × 3 × 0.25 = **$375**

**Note:** Be careful not to use the customer's *observed* lifespan in both the frequency denominator and projection multiplier (they cancel out). Use a fixed industry horizon or cohort average.

---

### 13. How would you measure the success of a marketing campaign?

**Answer:**
1. **Lift:** Incremental revenue/orders caused by campaign (not just total, but vs. control group)
2. **ROI:** (Campaign Revenue - Campaign Cost) / Campaign Cost
3. **ROAS:** Revenue / Ad Spend (for paid campaigns)
4. **CAC:** Customer Acquisition Cost = Total Campaign Cost / New Customers
5. **CLV:CAC Ratio:** Ideally 3:1 or higher
6. **Retention:** % of campaign-acquired customers who repeat purchase

**Example from Project:**
If a retention campaign targets 250 at-risk customers at $10k cost:
- If 50 convert (20%), that's 50 customers retained at $200 CAC
- At $2,750 avg CLV, the CLV:CAC ratio is 13.75x
- Likely 200–400% ROI

---

### 14. What is a cohort and why would you analyze retention by cohort?

**Answer:**
A cohort is a group of customers acquired in the same time period (e.g., all customers who first purchased in January 2023).

**Why Cohort Analysis:**
- Tracks how each group's purchasing behavior changes over time
- Identifies seasonal patterns in acquisition vs. retention
- Detects improvements from product/marketing changes
- Answers: "Which cohorts stick around longest?"

**From Project:**
I built a cohort retention heatmap showing Month-1 retention averaged 38% (steep cliff at day 30). The 2023-Q4 cohort had 42% retention, the best cohort — suggesting our Q4 campaigns attracted stickier customers.

---

### 15. How would you identify if a customer segment is profitable?

**Answer:**
1. **Revenue:** Sum of all purchases from segment
2. **Cost:** Acquisition cost + operational/support cost
3. **Profit Margin:** (Revenue - Cost) / Revenue
4. **CLV:** Projected future value
5. **Compare:** Segment CLV vs. CAC ratio (aim for 3x+)

**From Project:**
- **Champions:** CLV = $3,500, Acquisition Cost = $50, Ratio = 70x ✅ (Very profitable)
- **Lost:** CLV = $250, Acquisition Cost = $50, Ratio = 5x ✅ (Still profitable to reactivate)
- Decision: Invest heavily in retaining Champions; cautiously reactivate Lost.

---

### 16. What KPIs would you track for an e-commerce business?

**Answer:**
**Financial:**
- Total Revenue, Profit, Profit Margin %, AOV

**Customer:**
- Total Customers, New Customers, Repeat Customer Rate, Churn Rate, Lifetime Value

**Orders:**
- Order Count, Units Sold, Avg Items per Order, Conversion Rate

**Operational:**
- Shipping Time, Return Rate, Discount Rate, Cart Abandonment Rate

**Retention:**
- Month-1 Retention, Repeat Purchase Rate, Cohort Survival

**Forecast:**
- Revenue Forecast, Churn Forecast, Demand by Product

---

### 17. How would you handle missing data in your analysis?

**Answer:**
**Three Approaches:**
1. **Drop rows:** If <5% missing and not critical to analysis
2. **Impute (Fill):** 
   - Numeric: Use mean/median/forward-fill
   - Categorical: Use mode or "Unknown" category
3. **Flag & Analyze Separately:** Mark as "missing" indicator and model separately

**From Project:**
- 312 missing shipping dates out of 10,000 (3.1%) → Used median (4 days) to impute
- Flagged in validation; confirmed no bias (missing uniformly across categories)
- Alternative: Excluded from analysis (small enough impact)

---

### 18. Explain the difference between correlation and causation. Give an example.

**Answer:**
**Correlation:** Two variables move together (ice cream sales ↑ when temperature ↑)  
**Causation:** One variable causes the other (temperature ↑ causes ice cream sales ↑)

**Problem:** Correlation doesn't imply causation. Example: A/C sales ↑ & ice cream sales ↑ are both caused by summer heat, not each other.

**In Analytics:** Be careful claiming "X caused Y" from observational data. Use:
- **Randomized A/B tests** (true causation)
- **Propensity matching** (quasi-causation)
- **Regression with controls** (partial control for confounds)

**From Project:**
I could say "Customers with high discount rate have lower churn" (correlation). But is discounting *causing* retention or are discounts a band-aid for already-at-risk customers? Needs more investigation.

---

### 19. How would you approach debugging a KPI that suddenly dropped?

**Answer:**
1. **Confirm the drop** — Is it data quality or real behavior?
2. **Check data pipeline** — Did ETL jobs fail? Schema changes?
3. **Segment the drop** — By region? Category? Customer type? (Helps isolate root cause)
4. **Compare to prior periods** — Is this seasonal or anomalous?
5. **Interview stakeholders** — Did we change pricing, promotion, product, etc.?
6. **Build hypothesis & test** — Use cohort/time series analysis

**Example:**
If revenue dropped 20%, I'd check:
- Data: Did order counts drop too? (If not, could be price changes)
- Geography: All regions or specific ones?
- Category: All products or specific ones?
- Timing: Sudden drop or gradual decline?

---

### 20. What's the difference between aggregated and granular data? When would you use each?

**Answer:**
**Granular:** Every individual transaction (order-level detail)  
- Pros: Flexibility, detail, can drill-down
- Cons: Slower queries, more storage, easy to miscalculate aggregates

**Aggregated:** Pre-computed summaries (monthly revenue by category)
- Pros: Fast queries, dashboard performance, easier to understand
- Cons: Can't drill into exceptions

**Best Practice:** Store granular data in data warehouse; pre-aggregate for dashboards.

**From Project:**
Stored order-level fact_orders table (granular). Pre-computed monthly_kpis aggregations for the dashboard. Best of both worlds.

---

### 21. How do you validate that your analysis is correct?

**Answer:**
1. **Schema Validation:** Pandera checks (column types, ranges, nulls)
2. **Sanity Checks:** Do numbers make sense? (e.g., CLV never negative, Discount % between 0–1)
3. **Spot Checks:** Manually verify a few calculations
4. **Compare to Prior:** Does this match last month's analysis (adjusted for growth)?
5. **Peer Review:** Have another analyst validate key findings
6. **Stakeholder Validation:** Present to business owner for plausibility check

**From Project:**
When I calculated CLV initially, I got an average of $250k per customer — clearly wrong. Debugged and found the formula error (lifespan cancellation). After fixing, $2,750 avg was validated by business team (aligned with their intuition).

---

### 22. What's the difference between a metric and a dimension?

**Answer:**
**Metric (Measure):** A quantitative value (number)
- Examples: Revenue, Order Count, Profit, AVG, SUM
- Characteristics: Can be aggregated (sum, avg, min, max)

**Dimension (Attribute):** A categorical value (group by category)
- Examples: Date, Region, Product Category, Customer Segment, RFM Tier
- Characteristics: Used to slice/group metrics

**Example:**
"Revenue by Region" — Revenue is the metric, Region is the dimension.

---

### 23. How would you explain statistical significance to a non-technical business stakeholder?

**Answer:**
"Statistical significance means the result is unlikely due to random chance. If our test shows a 5% improvement with 95% confidence, we're 95% sure the improvement is real (not just luck)."

**Simple Example:**
"If we test 2 versions of a webpage and Version B gets 3% more clicks, is that real or random? Statistical significance tells us: if we repeated the test 100 times, we'd expect similar results 95 times."

**Rule of Thumb:** Look for p-value < 0.05 (5% chance of being wrong).

---

### 24. What's the difference between a dashboard and a report?

**Answer:**
**Dashboard:** Real-time, interactive, self-service
- Updated continuously (hourly/daily)
- Visual, high-level summary (KPI cards, charts)
- User explores data themselves (filters, drill-down)
- Example: Streamlit app with live metrics

**Report:** Static, detailed, push-based
- Generated on a schedule (weekly, monthly)
- Narrative with findings and recommendations
- Author decides what to show (fixed layout)
- Example: Executive summary PDF or CSV export

**From Project:**
Built both: Streamlit dashboard (real-time exploration) + Executive Summary report (narrative findings).

---

### 25. How would you present your findings to a C-level executive in 5 minutes?

**Answer (Using Project):**

*"Of our 500 customers, just 8% (40 customers) generate 45% of our revenue. These are our 'Champions' and they're incredibly profitable — $2,750 lifetime value each. Our second priority is the 250 'At-Risk' customers (high churn probability). If we retain just 20% of them through targeted campaigns, we'd gain $76k in annual revenue. I've built a system to identify these customers and monitor them weekly. Recommendation: Launch a retention program focused on At-Risk segment; invest in VIP experience for Champions."*

**Key Principles:**
- Lead with a surprising insight (8% → 45%)
- Quantify the opportunity ($76k)
- Propose one clear action
- Skip the technical details

---

### 26. What metrics would you use to measure customer satisfaction?

**Answer:**
1. **NPS (Net Promoter Score):** "How likely to recommend 0–10?" (Detractors vs. Promoters)
2. **CSAT:** Customer Satisfaction survey (1–5 scale)
3. **Customer Retention:** % who repeat purchase (implicit satisfaction)
4. **Repeat Order Rate:** Higher is better
5. **Customer Support Tickets:** Lower is better
6. **Product Review Rating:** Average star rating
7. **Churn Rate:** If rising, satisfaction is declining

**From Project:**
I inferred satisfaction from repeat purchase rate: 30% of customers make repeat purchases. This suggests moderate satisfaction. Could improve with targeted engagement.

---

### 27. How do you decide between different visualization types?

**Answer:**
- **Trend (Time Series):** Line chart
- **Comparison (Categories):** Bar chart (horizontal for many categories)
- **Distribution:** Histogram, box plot, or violin plot
- **Proportion (Part of Whole):** Pie or stacked bar
- **Relationship (Two Variables):** Scatter plot
- **Composition Over Time:** Stacked area or Sankey
- **Heatmap:** Cohort retention or correlation matrix

**From Project:**
- Cohort retention → Heatmap (show all cohorts × months at once)
- Revenue trend → Line chart (show changes over time)
- Customer segment size → Pie chart (show % of total)
- RFM scores by segment → Box plot (show distribution)

---

### 28. Explain the concept of drill-down in analytics.

**Answer:**
Drill-down is the ability to start with a summary and progressively get more detail.

**Example:**
- Dashboard shows "Total Revenue: $500k"
- Click → "Revenue by Region: West $200k, East $150k, South $100k, North $50k"
- Click West → "Revenue by Category: Electronics $100k, Furniture $60k, Clothing $40k"
- Click Electronics → Individual orders

**Benefits:** Users can self-serve find root causes; reduces need for custom reports.

**From Project:**
Streamlit dashboard doesn't have native drill-down, but SQL queries could support this. Power BI has better built-in drill-down UI.

---

### 29. What would you do if a stakeholder disagreed with your findings?

**Answer:**
1. **Listen carefully** — Maybe they have context I'm missing
2. **Ask clarifying questions** — "What's your concern specifically?"
3. **Review your methodology** — Did I make an error?
4. **Show the data** — Walk through the calculation step-by-step
5. **Propose a test** — "Let's check this another way"
6. **Reach compromise** — Maybe both interpretations are valid with caveats

**Example:**
"If marketing said my churn prediction model was too aggressive, I'd ask: 'What % false positive rate is acceptable?' Then rebuild the model with a more conservative threshold."

---

### 30. Describe your experience with A/B testing.

**Answer:**
A/B testing (or multivariate testing) compares two versions to see which performs better.

**Process:**
1. **Hypothesis:** "Version B will increase clicks by 5%"
2. **Design:** 50% of users see A, 50% see B (randomized)
3. **Run:** Collect data for sufficient time/sample size
4. **Analyze:** Calculate lift, p-value, confidence interval
5. **Decide:** If statistically significant and business-valuable, implement

**From Project:**
No A/B testing in this project, but I mentioned it for validating the churn model's business impact: "Run a retention campaign on 100 at-risk customers, control on 100 others, measure uplift."

---

## 🗄️ SQL QUESTIONS (20)

*Focused on data retrieval, aggregation, and data warehouse queries.*

### 31. Write a SQL query to calculate total revenue by month.

```sql
SELECT 
  DATE_TRUNC(order_date, MONTH) AS month,
  SUM(sales_amount) AS total_revenue,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(DISTINCT customer_id) AS customer_count
FROM fact_orders
GROUP BY DATE_TRUNC(order_date, MONTH)
ORDER BY month DESC;
```

**Explanation:**
- `DATE_TRUNC`: Rounds date to first of month
- `SUM(sales_amount)`: Total revenue
- `COUNT(DISTINCT ...)`: Unique orders/customers (not sum)
- `GROUP BY`: Aggregate by month
- `ORDER BY ... DESC`: Latest months first

---

### 32. Write a query to find the top 5 customers by lifetime spending.

```sql
SELECT TOP 5
  customer_id,
  COUNT(DISTINCT order_id) AS order_count,
  SUM(sales_amount) AS lifetime_revenue,
  AVG(sales_amount) AS avg_order_value,
  MAX(order_date) AS last_purchase_date
FROM fact_orders
GROUP BY customer_id
ORDER BY lifetime_revenue DESC;
```

---

### 33. Write a query to calculate retention rate (% of customers who made repeat purchases).

```sql
SELECT 
  (COUNT(CASE WHEN order_count > 1 THEN 1 END) * 100.0 / COUNT(*)) AS repeat_customer_pct
FROM (
  SELECT 
    customer_id, 
    COUNT(DISTINCT order_id) AS order_count
  FROM fact_orders
  GROUP BY customer_id
) subquery;
```

**Explanation:**
- Inner query: Count orders per customer
- Outer query: % of customers with >1 order

---

### 34. Write a query to find customers who haven't purchased in 90+ days.

```sql
SELECT 
  customer_id,
  MAX(order_date) AS last_purchase_date,
  DATEDIFF(day, MAX(order_date), GETDATE()) AS days_since_purchase,
  COUNT(DISTINCT order_id) AS total_orders,
  SUM(sales_amount) AS lifetime_revenue
FROM fact_orders
GROUP BY customer_id
HAVING DATEDIFF(day, MAX(order_date), GETDATE()) >= 90
ORDER BY last_purchase_date DESC;
```

---

### 35. Write a query to calculate RFM scores.

```sql
WITH rfm_calc AS (
  SELECT 
    customer_id,
    -- Recency: days since last purchase
    DATEDIFF(day, MAX(order_date), GETDATE()) AS recency,
    -- Frequency: count of orders
    COUNT(DISTINCT order_id) AS frequency,
    -- Monetary: total spend
    SUM(sales_amount) AS monetary
  FROM fact_orders
  GROUP BY customer_id
),
rfm_rank AS (
  SELECT 
    customer_id,
    recency,
    frequency,
    monetary,
    -- Score each R/F/M on a 1-5 scale (5 = best)
    NTILE(5) OVER (ORDER BY recency DESC) AS r_score,  -- Lower recency = better
    NTILE(5) OVER (ORDER BY frequency) AS f_score,     -- Higher frequency = better
    NTILE(5) OVER (ORDER BY monetary) AS m_score       -- Higher spend = better
  FROM rfm_calc
)
SELECT 
  customer_id,
  recency,
  frequency,
  monetary,
  CAST(r_score AS VARCHAR) + CAST(f_score AS VARCHAR) + CAST(m_score AS VARCHAR) AS rfm_segment
FROM rfm_rank
ORDER BY rfm_segment DESC;
```

**Explanation:**
- `NTILE(5)`: Divides into 5 buckets (quintiles); 5 = top 20%
- For Recency, sort DESC (lower days = higher score)
- For Frequency/Monetary, sort ASC (higher values = higher score)
- Concatenate into 3-digit segment (e.g., "555" = top customer, "111" = lost)

---

### 36. Write a query to calculate month-over-month revenue growth %.

```sql
WITH monthly_revenue AS (
  SELECT 
    DATE_TRUNC(order_date, MONTH) AS month,
    SUM(sales_amount) AS revenue
  FROM fact_orders
  GROUP BY DATE_TRUNC(order_date, MONTH)
)
SELECT 
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
  ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0 
    / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month DESC;
```

**Explanation:**
- `LAG()`: Access previous row's revenue for comparison
- Calculate % change: (current - previous) / previous * 100

---

### 37. Write a query to find customers in each RFM segment with segment count.

```sql
SELECT 
  CASE 
    WHEN r_score = 5 AND f_score = 5 THEN 'Champions'
    WHEN r_score >= 4 AND f_score >= 4 THEN 'Loyal Customers'
    WHEN r_score <= 2 THEN 'At Risk'
    WHEN r_score = 1 AND f_score <= 2 THEN 'Lost'
    ELSE 'Other'
  END AS segment,
  COUNT(*) AS customer_count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_data), 2) AS pct_of_total,
  ROUND(AVG(monetary), 2) AS avg_lifetime_value
FROM rfm_data
GROUP BY segment
ORDER BY customer_count DESC;
```

---

### 38. Write a query to calculate customer acquisition cost (CAC) by acquisition month.

```sql
SELECT 
  DATE_TRUNC(acquisition_date, MONTH) AS acquisition_month,
  COUNT(DISTINCT customer_id) AS new_customers,
  SUM(acquisition_cost) AS total_acq_cost,
  ROUND(SUM(acquisition_cost) / COUNT(DISTINCT customer_id), 2) AS cac_per_customer
FROM customer_acquisition
GROUP BY DATE_TRUNC(acquisition_date, MONTH)
ORDER BY acquisition_month DESC;
```

---

### 39. Write a query to find cross-selling opportunities (customers who bought A but not B).

```sql
SELECT DISTINCT
  f1.customer_id,
  c.customer_name,
  'Bought Furniture, Not Electronics' AS opportunity
FROM fact_orders f1
INNER JOIN dim_customer c ON f1.customer_id = c.customer_id
WHERE f1.product_category = 'Furniture'
AND f1.customer_id NOT IN (
  SELECT DISTINCT customer_id
  FROM fact_orders
  WHERE product_category = 'Electronics'
)
ORDER BY f1.customer_id;
```

---

### 40. Write a query to rank products by revenue within each category.

```sql
SELECT 
  product_category,
  product_id,
  product_name,
  SUM(sales_amount) AS category_revenue,
  ROW_NUMBER() OVER (PARTITION BY product_category ORDER BY SUM(sales_amount) DESC) AS rank_in_category
FROM fact_orders
INNER JOIN dim_product USING (product_id)
GROUP BY product_category, product_id, product_name
ORDER BY product_category, rank_in_category;
```

---

### 41. Write a query to find the moving average of daily revenue (7-day window).

```sql
SELECT 
  order_date,
  SUM(sales_amount) AS daily_revenue,
  ROUND(AVG(SUM(sales_amount)) OVER (
    ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ), 2) AS moving_avg_7day
FROM fact_orders
GROUP BY order_date
ORDER BY order_date DESC;
```

---

### 42. Write a query to calculate customer lifetime value by segment.

```sql
SELECT 
  c.rfm_segment,
  COUNT(DISTINCT f.customer_id) AS customer_count,
  ROUND(SUM(f.sales_amount), 2) AS total_lifetime_revenue,
  ROUND(AVG(f.sales_amount), 2) AS avg_lifetime_revenue,
  ROUND(SUM(f.profit), 2) AS total_profit,
  ROUND(SUM(f.profit) / NULLIF(SUM(f.sales_amount), 0), 2) AS profit_margin_pct
FROM fact_orders f
INNER JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.rfm_segment
ORDER BY total_lifetime_revenue DESC;
```

---

### 43. Explain the difference between WHERE and HAVING clauses.

**Answer:**
- **WHERE:** Filters *rows* before aggregation (can't use aggregate functions)
- **HAVING:** Filters *groups* after aggregation (can use aggregate functions)

```sql
-- WHERE: Find orders over $100
SELECT customer_id, SUM(sales_amount) AS total
FROM fact_orders
WHERE sales_amount > 100  -- Filters individual rows
GROUP BY customer_id;

-- HAVING: Find customers with total orders over $500
SELECT customer_id, SUM(sales_amount) AS total
FROM fact_orders
GROUP BY customer_id
HAVING SUM(sales_amount) > 500;  -- Filters groups
```

---

### 44. What is a JOIN and when would you use LEFT JOIN vs INNER JOIN?

**Answer:**
**INNER JOIN:** Only rows present in *both* tables
- Use when you only want matching records
- Example: "Orders from customers in our CRM"

**LEFT JOIN:** All rows from left table + matching rows from right
- Use when you want to keep unmatched left rows
- Example: "All customers, even those with no orders"

```sql
-- INNER: Only customers with orders
SELECT c.customer_id, c.name, COUNT(f.order_id) AS orders
FROM dim_customer c
INNER JOIN fact_orders f ON c.customer_id = f.customer_id
GROUP BY c.customer_id;

-- LEFT: All customers, even those with no orders
SELECT c.customer_id, c.name, COUNT(f.order_id) AS orders
FROM dim_customer c
LEFT JOIN fact_orders f ON c.customer_id = f.customer_id
GROUP BY c.customer_id;
```

---

### 45. Explain Common Table Expressions (CTEs / WITH clause) and why you'd use them.

**Answer:**
A CTE is a temporary result set defined with `WITH` that you can reference later in the query.

**Benefits:**
- Improves readability (breaks complex query into steps)
- Avoids nesting subqueries
- Can reference itself (recursive CTE)

```sql
-- CTE: Calculate revenue by month, then find top months
WITH monthly_revenue AS (
  SELECT 
    DATE_TRUNC(order_date, MONTH) AS month,
    SUM(sales_amount) AS revenue
  FROM fact_orders
  GROUP BY DATE_TRUNC(order_date, MONTH)
)
SELECT TOP 5
  month,
  revenue
FROM monthly_revenue
ORDER BY revenue DESC;
```

---

### 46. What is a window function and how would you use it?

**Answer:**
Window functions perform calculations on a "window" of rows (related rows) without collapsing groups.

**Common:** `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`, `SUM() OVER (...)`

```sql
-- Rank customers by spending within each region
SELECT 
  customer_id,
  region,
  lifetime_value,
  ROW_NUMBER() OVER (PARTITION BY region ORDER BY lifetime_value DESC) AS rank_in_region
FROM dim_customer
ORDER BY region, rank_in_region;
```

---

### 47. Write a query to find duplicate orders (if any).

```sql
SELECT 
  order_id,
  customer_id,
  order_date,
  COUNT(*) AS duplicate_count
FROM fact_orders
GROUP BY order_id, customer_id, order_date
HAVING COUNT(*) > 1;
```

---

### 48. What is data normalization and why is it important in database design?

**Answer:**
Normalization is organizing data to reduce redundancy and improve consistency.

**Normal Forms:**
- **1NF:** Atomic values (no repeating groups)
- **2NF:** Remove partial dependencies (non-key attributes depend on entire key)
- **3NF:** Remove transitive dependencies (non-key attributes don't depend on other non-key attributes)

**Benefits:** Saves storage, prevents update anomalies, maintains data integrity

**Example:**
*Bad (denormalized):*
```
Orders table: Order_ID, Customer_Name, Customer_Email, Product_Name, Product_Price
```
(Customer info repeats per order)

*Good (normalized):*
```
Orders: Order_ID, Customer_ID, Product_ID
Customers: Customer_ID, Name, Email
Products: Product_ID, Name, Price
```

---

### 49. Explain the concept of a data warehouse and how it differs from an OLTP database.

**Answer:**
**OLTP (Operational):** Optimized for fast reads/writes of individual transactions
- Used by applications (e.g., checkout, order entry)
- Normalized schema, small tables, high write volume
- Query: "Get customer details for order #123"

**Data Warehouse (OLAP):** Optimized for analytical queries over large datasets
- Used by analysts/BI teams
- Denormalized schema (star/snowflake), large fact tables, high read volume
- Query: "Sum revenue by region for the last 2 years"

**From Project:**
Designed a star schema data warehouse (fact_orders + dimensions) to support analytical queries without slowing down transactional systems.

---

### 50. What's the difference between DISTINCT and GROUP BY?

**Answer:**
**DISTINCT:** Removes duplicate rows
**GROUP BY:** Groups rows and allows aggregation

```sql
-- DISTINCT: How many unique customers?
SELECT COUNT(DISTINCT customer_id) FROM fact_orders;

-- GROUP BY: Count of orders per customer
SELECT customer_id, COUNT(*) FROM fact_orders GROUP BY customer_id;
```

Use **DISTINCT** for simple deduplication, **GROUP BY** when you need aggregates per group.

---

## 📊 POWER BI QUESTIONS (20)

*Focused on dashboard design, DAX, and visualization.*

### 51. What is a measure vs. a calculated column in Power BI?

**Answer:**
**Measure:** Dynamic calculation based on filter context; uses DAX aggregation functions
- Example: `Total Revenue = SUM(sales[amount])`
- Recalculates based on filters applied
- Used in visuals

**Calculated Column:** Static column added to a table; evaluated row-by-row
- Example: `Profit_Margin = [Profit] / [Sales]`
- Computed once, stored in memory
- Can't use aggregates (SUM, AVG, etc.)

**When to Use:**
- Measure: Revenue, profit, count, aggregate metrics
- Calculated Column: Bucketing (e.g., "Low/Medium/High"), flags, derived attributes

---

### 52. Write a DAX formula to calculate Year-over-Year revenue growth %.

```dax
Revenue YoY Growth % = 
  VAR CurRevenue = [Total Revenue]
  VAR PriorRevenue = CALCULATE(
    [Total Revenue],
    DATEADD('dim_calendar'[full_date], -1, YEAR)
  )
  RETURN
    IFERROR(
      (CurRevenue - PriorRevenue) / PriorRevenue * 100,
      BLANK()
    )
```

**Explanation:**
- `VAR`: Define variables for clarity
- `CALCULATE()`: Change filter context to prior year
- `DATEADD(..., -1, YEAR)`: Shift date back 1 year
- `IFERROR()`: Handle division by zero

---

### 53. Write a DAX formula to calculate the running total of revenue by month.

```dax
Running Total Revenue = 
  CALCULATE(
    [Total Revenue],
    FILTER(
      ALL('dim_calendar'),
      'dim_calendar'[full_date] <= MAX('dim_calendar'[full_date])
    )
  )
```

**Explanation:**
- `FILTER()`: Keep all months up to current month
- `ALL()`: Remove existing filters
- `MAX()`: Current month in filter context

---

### 54. Explain the difference between implicit and explicit measures.

**Answer:**
**Implicit:** Power BI auto-sums numeric columns when dragged to visual (e.g., Drag "Sales" column → Auto-sum)
- Quick but limited
- Can't apply complex logic

**Explicit:** You write a DAX formula (e.g., `Total Sales = SUM(sales[amount])`)
- More control
- Can use conditional logic, time intelligence, etc.

**Best Practice:** Use explicit measures; gives you full control and reusability.

---

### 55. What is a measure that calculates average customer lifetime value?

```dax
Avg CLV = 
  CALCULATE(
    AVERAGE('dim_customer'[customer_lifetime_value]),
    'dim_customer'[is_active] = 1
  )
```

---

### 56. How would you create a measure for % of total revenue?

```dax
Revenue % of Total = 
  VAR TotalRev = CALCULATE([Total Revenue], ALL('dim_customer'))
  RETURN
    DIVIDE([Total Revenue], TotalRev, 0) * 100
```

**Explanation:**
- `DIVIDE()`: Safer than `/` (handles zero denominator)
- `ALL()`: Remove customer filter to get grand total
- Multiply by 100 for percentage

---

### 57. Explain CALCULATE() and how it's used in DAX.

**Answer:**
`CALCULATE()` evaluates an expression in a modified filter context.

**Syntax:**
```dax
CALCULATE(expression, filter1, filter2, ...)
```

**Example:**
```dax
-- Revenue only for high-value customers
High Value Revenue = 
  CALCULATE(
    [Total Revenue],
    'dim_customer'[customer_lifetime_value] >= 5000
  )
```

**Common Uses:**
- Compare to prior period (override date filter)
- Filter to specific segment
- Remove or add filters

---

### 58. What's the difference between ALL() and ALLEXCEPT()?

**Answer:**
**ALL():** Removes *all* filters
```dax
Total All Revenue = CALCULATE([Total Revenue], ALL(dim_customer))
```
(Revenue ignoring which customer is selected)

**ALLEXCEPT():** Removes filters on all columns *except* specified ones
```dax
Revenue Except Category = CALCULATE([Total Revenue], ALLEXCEPT(dim_product, dim_product[category]))
```
(Revenue for all products, but keep category filter)

---

### 59. How would you create a churn risk tier measure?

```dax
Churn Risk Tier = 
  SWITCH(
    TRUE(),
    RELATED('dim_customer'[churn_probability]) <= 0.33, "Low Risk",
    RELATED('dim_customer'[churn_probability]) <= 0.66, "Medium Risk",
    RELATED('dim_customer'[churn_probability]) <= 1.0, "High Risk",
    "Unknown"
  )
```

---

### 60. Explain time intelligence functions in DAX (e.g., YTD, MTD).

**Answer:**
Time intelligence functions calculate values relative to a date context.

```dax
-- Year-to-date revenue
Revenue YTD = 
  CALCULATE(
    [Total Revenue],
    DATESYTD('dim_calendar'[full_date])
  )

-- Month-to-date revenue
Revenue MTD = 
  CALCULATE(
    [Total Revenue],
    DATESMTD('dim_calendar'[full_date])
  )

-- Same period last year
Revenue SPLY = 
  CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR('dim_calendar'[full_date])
  )
```

---

### 61. What are KPI cards and how do you configure them in Power BI?

**Answer:**
KPI Card visual displays:
- Main value (e.g., $500k revenue)
- Trend indicator (↑/↓ arrow + % change)
- Target/goal (optional)

**Configuration:**
1. Add KPI Card visual to page
2. Set "Value" field (e.g., [Total Revenue])
3. Set "Trend Axis" field (e.g., [Month])
4. Set "Target Goals" (optional)
5. Format: Conditional color (green if up, red if down)

---

### 62. How would you create a cohort retention heatmap in Power BI?

**Visual Type:** Matrix/Table

**Setup:**
- **Rows:** Cohort Month
- **Columns:** Cohort Index (months since acquisition)
- **Values:** Retention % (format as color scale)
- **Conditional Formatting:** Color scale (0% yellow → 100% blue)

---

### 63. Explain relationships in Power BI data model.

**Answer:**
A relationship connects two tables via a common column.

**Types:**
- **One-to-Many (1:*):** Dim table (one) to Fact table (many). Most common.
- **One-to-One (1:1):** Rare; should probably be one table
- **Many-to-Many (*:*):** Problematic; often needs a bridge table

**Cardinality:**
- **1:* (One-to-Many):** From dim table (1) to fact table (*)
- **1:1 (One-to-One):** Each row matches one row in other table

**Direction:**
- **Single:** Filter flows one direction (dim → fact)
- **Both:** Filter flows both ways (use cautiously; can slow queries)

**From Project:**
```
fact_orders (many) →[customer_id]→ dim_customer (one)
fact_orders (many) →[product_id]→ dim_product (one)
dim_customer (many) →[region_id]→ dim_region (one)
```

---

### 64. How do you optimize Power BI performance?

**Answer:**
1. **Reduce data:** Import only necessary columns/rows
2. **Denormalize:** Pre-aggregate in data warehouse
3. **Disable auto-relationships:** Manually specify needed relationships only
4. **Use aggregation tables:** Pre-compute sums for large fact tables
5. **Avoid calculated columns on big tables:** Use measures instead
6. **Summarize at load:** ETL aggregation vs. Power BI aggregation
7. **Index in source:** SQL indices on join keys
8. **DirectQuery vs. Import:** Use Import for <1GB, DirectQuery for >10GB

---

### 65. What's the difference between Import and DirectQuery modes?

**Answer:**
**Import:** Data copied into Power BI; fast, fully featured, requires refresh
- Best for: Small-medium datasets (<1GB), need offline access
- Cons: Must refresh periodically; limited live data

**DirectQuery:** Queries source database on-demand; always current, slower, some DAX limits
- Best for: Large datasets (>10GB), need real-time data
- Cons: Slower queries; some DAX functions not supported

**From Project:**
Used **Import** mode. Data (~10k rows) fit in memory; refresh daily via Airflow.

---

### 66. How would you handle slicers and cross-filtering in a dashboard?

**Answer:**
**Slicers:** UI controls to filter data (dropdowns, buttons, etc.)

**Setup:**
1. Add Slicer visual
2. Set field (e.g., dim_region[region_name])
3. Visuals automatically filter based on slicer selection

**Cross-Filtering:**
- By default, slicers filter all downstream visuals ✓
- To disable: Visual → Format → Cross-Filter → "None"
- To filter only specific visuals: Use bookmark/buttons

**Best Practice:**
- Put slicers at top/left for visibility
- Use single-select slicers (cleaner) unless multi-select essential
- Provide "All" option for context

---

### 67. Explain the difference between FILTER and CALCULATE.

**Answer:**
**FILTER():** Creates a table with conditions, then counts/sums
```dax
High Value Customers = COUNTROWS(FILTER(dim_customer, dim_customer[clv] >= 5000))
```

**CALCULATE():** Modifies filter context for a measure
```dax
High Value Revenue = CALCULATE([Total Revenue], dim_customer[clv] >= 5000)
```

**Rule of Thumb:**
- Use **CALCULATE()** for measures (more common, better performance)
- Use **FILTER()** when you need table iteration or complex conditions

---

### 68. How would you create a forecast visual in Power BI?

**Options:**
1. **Import forecast data:** Load forecast_table.csv with forecast values; plot as line
2. **Predict in Power BI:** Uses built-in AI (limited; usually better to pre-compute in Python)
3. **Use Power BI's Forecast visual:** Automatically extends trend line with confidence band

**Example (Using pre-computed forecast):**
- Import forecast table with Month & Forecasted_Revenue columns
- Line chart: X=Month, Y=[Actual Revenue] + [Forecasted Revenue]
- Format forecast line as dashed to distinguish

---

### 69. What's a tooltip and how do you customize it?

**Answer:**
A tooltip is additional information shown when you hover over a data point.

**Customize:**
1. Add a visual with the data you want to show (e.g., profit %)
2. In another visual's "Format" pane → "Tooltips"
3. Select the custom visual you created
4. Now hovering shows your custom tooltip

**Example:**
Main visual = Revenue by Category (bar chart)  
Tooltip visual = Shows category name + count of SKUs + margin %

---

### 70. Explain row-level security (RLS) and when you'd use it.

**Answer:**
RLS restricts what data users can see based on their identity.

**Use Case:**
Region managers should only see their region's data.

**Implementation:**
1. Create a role: `CREATE ROLE SalesEast`
2. Define rules:  
```dax
RETURN [Region] = USERNAME()  -- Username matches region column
```
3. Assign users to role in Power BI Service
4. Users see only filtered data

---

## 🐍 PYTHON QUESTIONS (20)

*Focused on data manipulation, ML, and scripting.*

### 71. Write a Python function to load and inspect a CSV file.

```python
import pandas as pd

def load_and_inspect(filepath):
    df = pd.read_csv(filepath)
    print(f"Shape: {df.shape}")  # Rows, columns
    print(f"Data types:\n{df.dtypes}")
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"First few rows:\n{df.head()}")
    return df

# Usage
df = load_and_inspect("data/raw/retail_sales_data.csv")
```

---

### 72. How would you handle missing values in a dataset?

```python
# Option 1: Drop rows with missing values
df_clean = df.dropna()

# Option 2: Fill with mean (numeric)
df['column'] = df['column'].fillna(df['column'].mean())

# Option 3: Fill with mode (categorical)
df['category'] = df['category'].fillna(df['category'].mode()[0])

# Option 4: Forward fill (time series)
df['value'] = df['value'].fillna(method='ffill')

# Option 5: Interpolate (time series)
df['value'] = df['value'].interpolate()
```

---

### 73. Write a function to calculate RFM scores.

```python
from datetime import datetime, timedelta

def calculate_rfm(df, today=None):
    """Calculate RFM scores for customers."""
    if today is None:
        today = pd.Timestamp.now()
    
    rfm = df.groupby('customer_id').agg({
        'order_date': lambda x: (today - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        'revenue': 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    
    # Score each dimension 1-5 (5 = best)
    rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1], duplicates='drop')
    rfm['f_score'] = pd.qcut(rfm['frequency'], 5, labels=[1,2,3,4,5], duplicates='drop')
    rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')
    
    rfm['rfm_segment'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    return rfm
```

---

### 74. Write code to train a simple customer churn prediction model.

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, classification_report

# Prepare features and target
X = df[['recency', 'frequency', 'monetary', 'avg_discount']]
y = df['churned']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train model
model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_proba)

print(f"AUC: {auc:.4f}")
print(classification_report(y_test, y_pred))
```

---

### 75. Write code to create a time series plot with matplotlib.

```python
import matplotlib.pyplot as plt

monthly = df.groupby(df['order_date'].dt.to_period('M'))['revenue'].sum()
monthly.index = monthly.index.to_timestamp()

plt.figure(figsize=(12, 6))
plt.plot(monthly.index, monthly.values, marker='o', linewidth=2, color='#1f77b4')
plt.title('Monthly Revenue Trend', fontsize=15, fontweight='bold')
plt.xlabel('Month')
plt.ylabel('Revenue ($)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('monthly_trend.png', dpi=300)
plt.show()
```

---

### 76. Write a function to calculate Customer Lifetime Value.

```python
def calculate_clv(df, projection_years=3):
    """Calculate CLV for each customer."""
    clv = df.groupby('customer_id').agg({
        'revenue': 'sum',  # Total revenue
        'order_id': 'count',  # Frequency
        'order_date': ['min', 'max']  # Tenure
    }).reset_index()
    
    clv.columns = ['customer_id', 'total_revenue', 'frequency', 'first_purchase', 'last_purchase']
    
    # Calculate tenure in years
    clv['tenure_years'] = (clv['last_purchase'] - clv['first_purchase']).dt.days / 365.25
    
    # Calculate AOV
    clv['avg_order_value'] = clv['total_revenue'] / clv['frequency']
    
    # Projected CLV (AOV * Freq * projection_years)
    clv['clv_projected'] = clv['avg_order_value'] * (clv['frequency'] / clv['tenure_years']) * projection_years
    
    return clv
```

---

### 77. How would you normalize/standardize numerical features before training an ML model?

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # Fit on training
X_test_scaled = scaler.transform(X_test)        # Only transform test

# Store scaler for production
import joblib
joblib.dump(scaler, 'scaler.pkl')

# Later: Load and use
scaler = joblib.load('scaler.pkl')
new_data_scaled = scaler.transform(new_data)
```

---

### 78. Write code to create a confusion matrix visualization.

```python
from sklearn.metrics import confusion_matrix
import seaborn as sns

cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Active', 'Churned'], 
            yticklabels=['Active', 'Churned'])
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=300)
```

---

### 79. How would you perform feature engineering to create useful predictors?

```python
def engineer_features(df):
    """Create derived features from raw data."""
    
    # Customer-level aggregations
    customer_feats = df.groupby('customer_id').agg({
        'revenue': ['sum', 'mean', 'max'],
        'discount': ['mean', 'std'],
        'order_id': 'count',
        'order_date': lambda x: (x.max() - x.min()).days,
        'category': 'nunique'
    }).reset_index()
    
    customer_feats.columns = ['customer_id', 'total_revenue', 'avg_order_value', 'max_order',
                              'avg_discount', 'discount_std', 'order_count', 'tenure_days', 'category_diversity']
    
    # Derived features
    customer_feats['revenue_per_order'] = customer_feats['total_revenue'] / customer_feats['order_count']
    customer_feats['avg_order_frequency'] = customer_feats['order_count'] / (customer_feats['tenure_days'] / 365.25 + 1)
    customer_feats['discount_sensitive'] = customer_feats['avg_discount'] > df['discount'].median()
    
    return customer_feats
```

---

### 80. Write code to perform a train/test split and evaluate model.

```python
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

X = df[features]
y = df['target']

# Stratified split (preserves class balance)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

results = {
    'accuracy': accuracy_score(y_test, y_pred),
    'precision': precision_score(y_test, y_pred),
    'recall': recall_score(y_test, y_pred),
    'f1': f1_score(y_test, y_pred),
    'auc': roc_auc_score(y_test, y_proba)
}

print(pd.DataFrame([results]))
```

---

### 81. How would you create a data validation pipeline using Pandera?

```python
import pandera as pa

schema = pa.DataFrameSchema({
    'order_id': pa.Column(str, checks=pa.Check.str_length(min_value=1)),
    'customer_id': pa.Column(int, nullable=False),
    'revenue': pa.Column(float, checks=pa.Check.ge(0)),
    'discount': pa.Column(float, checks=[
        pa.Check.ge(0),
        pa.Check.le(1)
    ]),
    'order_date': pa.Column(object),  # datetime
})

# Validate
try:
    df_validated = schema.validate(df)
    print("✓ Data validation passed")
except pa.errors.SchemaError as e:
    print(f"✗ Validation failed:\n{e}")
```

---

### 82. Write a function to generate an executive summary report.

```python
def generate_executive_summary(df, rfm, clv):
    """Generate KPI summary."""
    
    summary = f"""
    ========== EXECUTIVE SUMMARY ==========
    
    FINANCIAL:
    - Total Revenue: ${df['revenue'].sum():,.0f}
    - Total Profit: ${df['profit'].sum():,.0f}
    - Profit Margin: {(df['profit'].sum() / df['revenue'].sum() * 100):.1f}%
    - AOV: ${df['revenue'].mean():,.2f}
    
    CUSTOMER:
    - Total Customers: {df['customer_id'].nunique():,}
    - Repeat Rate: {(rfm[rfm['frequency'] > 1].shape[0] / rfm.shape[0] * 100):.1f}%
    - Avg CLV: ${clv['clv_projected'].mean():,.0f}
    - CLV:CAC Ratio: {(clv['clv_projected'].mean() / 50):.1f}x
    
    CHURN:
    - Churn Rate: {(rfm[rfm['recency'] > 180].shape[0] / rfm.shape[0] * 100):.1f}%
    - At-Risk Customers: {rfm[rfm['recency'] > 90].shape[0]:,}
    
    =======================================
    """
    
    return summary

print(generate_executive_summary(df, rfm, clv))
```

---

### 83. How would you use joblib to save and load a trained model?

```python
import joblib

# Save model
joblib.dump(model, 'churn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(feature_names, 'feature_names.pkl')

# Load model
model = joblib.load('churn_model.pkl')
scaler = joblib.load('scaler.pkl')
feature_names = joblib.load('feature_names.pkl')

# Score new data
new_data_scaled = scaler.transform(new_data[feature_names])
predictions = model.predict(new_data_scaled)
probabilities = model.predict_proba(new_data_scaled)
```

---

### 84. Write code to create a Streamlit dashboard with KPI cards and a chart.

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analytics Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data.csv')

df = load_data()

st.title("📊 Retail Analytics Dashboard")

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${df['revenue'].sum():,.0f}")
col2.metric("Orders", f"{df['order_id'].nunique():,}")
col3.metric("Customers", f"{df['customer_id'].nunique():,}")
col4.metric("AOV", f"${df['revenue'].mean():,.2f}")

# Chart
st.subheader("Monthly Revenue Trend")
monthly = df.groupby(df['order_date'].dt.to_period('M'))['revenue'].sum()
monthly.index = monthly.index.to_timestamp()
fig = px.line(x=monthly.index, y=monthly.values, title="Revenue Over Time")
st.plotly_chart(fig, use_container_width=True)
```

---

### 85. What is the difference between sklearn's Pipeline and manual train/test workflow?

**Answer:**
**Manual:**
```python
scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)
model.fit(X_train_scaled, y_train)
```
(Risk: forgetting to fit scaler only on training data)

**Pipeline:**
```python
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])

pipe.fit(X_train, y_train)  # Automatically fits scaler on X_train only
y_pred = pipe.predict(X_test)  # Automatically transforms X_test
```

**Benefits:** Less boilerplate, fewer mistakes, easier serialization.

---

### 86. How would you perform K-Means clustering and evaluate the results?

```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Prepare data
X = df[['recency', 'frequency', 'monetary']]
X_scaled = StandardScaler().fit_transform(X)

# Test different k values
for k in range(2, 8):
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)
    print(f"k={k}, Silhouette={sil:.3f}")

# Fit final model
model = KMeans(n_clusters=4, random_state=42, n_init=10)
df['cluster'] = model.fit_predict(X_scaled)

# Profiling
print(df.groupby('cluster')[['recency', 'frequency', 'monetary']].mean())
```

---

### 87. Write code to perform train/validation/test split (not just train/test).

```python
# 60% train, 20% validation, 20% test
from sklearn.model_selection import train_test_split

X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.25, random_state=42)

print(f"Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

# Tune on validation set, evaluate on test set
model.fit(X_train, y_train)
val_score = model.score(X_val, y_val)
test_score = model.score(X_test, y_test)
```

---

### 88. How would you implement cross-validation in scikit-learn?

```python
from sklearn.model_selection import cross_val_score

# 5-fold cross-validation
scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')

print(f"Cross-validation scores: {scores}")
print(f"Mean: {scores.mean():.4f} (+/- {scores.std():.4f})")

# Stratified K-Fold (preserves class balance in each fold)
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=skf, scoring='roc_auc')
```

---

### 89. Write code to implement hyperparameter tuning with GridSearchCV.

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)

print(f"Best params: {grid_search.best_params_}")
print(f"Best score: {grid_search.best_score_:.4f}")

# Use best model
best_model = grid_search.best_estimator_
test_score = best_model.score(X_test, y_test)
```

---

### 90. How would you create feature importance plot from a tree-based model?

```python
import pandas as pd
import matplotlib.pyplot as plt

# Get feature importances
importances = model.feature_importances_
feature_importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

# Plot
plt.figure(figsize=(10, 6))
plt.barh(feature_importance_df['feature'][:10], feature_importance_df['importance'][:10])
plt.xlabel('Importance')
plt.title('Top 10 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300)
```

---

## 🎓 FINAL TIPS FOR INTERVIEW SUCCESS

1. **Show your work:** Explain your thought process, not just answers
2. **Ask clarifying questions:** "Are you asking about the technical implementation or business rationale?"
3. **Use concrete examples:** Reference your project when possible
4. **Code is secondary:** Explain logic first, code second
5. **Mention edge cases:** "I'd also check for negative values..."
6. **Quantify whenever possible:** "Improved accuracy from 85% to 95.6%"
7. **Practice SQL on paper:** Many interviews won't let you run queries
8. **Know your DAX cold:** Have 3–5 formulas memorized
9. **Be ready to justify choices:** "I used Random Forest because X, Y, Z"
10. **Ask about the role:** "What's the biggest analytical challenge your team faces?"

---

**Document Version:** 1.0  
**Total Questions:** 90  
**Recommended Study Time:** 20–30 hours  
**Last Updated:** January 2024
