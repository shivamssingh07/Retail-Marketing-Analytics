"""
Retail & Marketing Analytics Dashboard
=======================================

Interactive Streamlit web application showcasing:
- KPI cards and metrics
- Revenue trends and forecasts
- Customer segmentation analysis
- Churn risk detection
- Product/category/regional breakdowns

Run: streamlit run streamlit_app/app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

from src import config
from src.utils import fmt_currency, fmt_pct, load_csv

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Retail & Marketing Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Retail & Marketing Analytics Dashboard")

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_all_data():
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    rfm = load_csv(config.RFM_FILE)
    clv = load_csv(config.CLV_FILE)
    segments = load_csv(config.SEGMENTS_FILE)
    churn = load_csv(config.CHURN_PRED_FILE)
    
    return df, rfm, clv, segments, churn


df, rfm, clv, segments, churn = load_all_data()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================

st.sidebar.title("🎯 Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df["Order_Date"].min().date(), df["Order_Date"].max().date()),
)

regions = st.sidebar.multiselect(
    "Regions",
    options=sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique()),
)

# Apply filters
mask = (
    (df["Order_Date"].dt.date >= date_range[0]) &
    (df["Order_Date"].dt.date <= date_range[1]) &
    (df["Region"].isin(regions))
)
df_filtered = df[mask].copy()

# ============================================================================
# KPI CARDS
# ============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_revenue = df_filtered["Revenue"].sum()
    st.metric("💰 Total Revenue", fmt_currency(total_revenue))

with col2:
    total_orders = df_filtered["Order_ID"].nunique()
    st.metric("📦 Total Orders", f"{total_orders:,}")

with col3:
    num_customers = df_filtered["Customer_ID"].nunique()
    st.metric("👥 Customers", f"{num_customers:,}")

with col4:
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
    st.metric("📊 AOV", fmt_currency(avg_order_value))

with col5:
    profit_margin = (df_filtered["Profit"].sum() / total_revenue * 100) if total_revenue > 0 else 0
    st.metric("💹 Margin", fmt_pct(profit_margin))

# ============================================================================
# PAGE SELECTION
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Customers", "Products", "Risk"])

# ============================================================================
# TAB 1: OVERVIEW
# ============================================================================

with tab1:
    st.header("Executive Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Revenue")
        monthly_data = (
            df_filtered.groupby(df_filtered["Order_Date"].dt.to_period("M"))["Revenue"]
            .sum()
            .reset_index()
        )
        monthly_data["Order_Date"] = monthly_data["Order_Date"].astype(str)

        fig = px.line(
            monthly_data, x="Order_Date", y="Revenue", markers=True,
            labels={"Revenue": "Revenue ($)"}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Revenue by Category")
        cat_data = df_filtered.groupby("Product_Category")["Revenue"].sum().reset_index()
        fig = px.pie(cat_data, values="Revenue", names="Product_Category")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: CUSTOMERS
# ============================================================================

with tab2:
    st.header("Customer Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Customers by Segment (RFM)")
        seg_dist = rfm["Customer_Segment"].value_counts().reset_index()
        seg_dist.columns = ["Segment", "Count"]
        fig = px.bar(seg_dist, x="Segment", y="Count")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Customers by Cluster")
        cluster_dist = segments["Cluster_Name"].value_counts().reset_index()
        cluster_dist.columns = ["Cluster", "Count"]
        fig = px.pie(cluster_dist, values="Count", names="Cluster")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Customers by CLV")
    top_clv = clv.nlargest(10, "CLV_Simple")[["Customer_ID", "CLV_Simple", "CLV_Category"]]
    st.dataframe(top_clv, use_container_width=True)

# ============================================================================
# TAB 3: PRODUCTS
# ============================================================================

with tab3:
    st.header("Product Performance")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Products")
        top_products = (
            df_filtered.groupby("Product_Name")["Revenue"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        fig = px.bar(top_products, x="Revenue", y="Product_Name", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Revenue by Region")
        region_data = df_filtered.groupby("Region")["Revenue"].sum().reset_index()
        fig = px.pie(region_data, values="Revenue", names="Region")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 4: RISK
# ============================================================================

with tab4:
    st.header("Churn & Risk Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        high_risk = len(churn[churn["Risk_Tier"] == "High Risk"])
        st.metric("High Risk Customers", high_risk)

    with col2:
        med_risk = len(churn[churn["Risk_Tier"] == "Medium Risk"])
        st.metric("Medium Risk", med_risk)

    with col3:
        low_risk = len(churn[churn["Risk_Tier"] == "Low Risk"])
        st.metric("Low Risk", low_risk)

    st.subheader("Risk Distribution")
    risk_dist = churn["Risk_Tier"].value_counts().reset_index()
    risk_dist.columns = ["Risk", "Count"]
    fig = px.bar(risk_dist, x="Risk", y="Count", color="Risk",
                 color_discrete_map={
                     "Low Risk": "#16a34a",
                     "Medium Risk": "#f59e0b",
                     "High Risk": "#dc2626"
                 })
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 At-Risk Customers")
    at_risk = churn[churn["Risk_Tier"] == "High Risk"].nlargest(20, "Churn_Probability")
    st.dataframe(at_risk[["Customer_ID", "Churn_Probability", "Risk_Tier"]], use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("**Retail & Marketing Analytics Dashboard** | Data: 2022-2023")
