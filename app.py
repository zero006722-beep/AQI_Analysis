import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AQI Analysis Dashboard",
    page_icon="🌬️",
    layout="wide",
)

# ── AQI helpers ──────────────────────────────────────────────────────────────
AQI_BREAKPOINTS = [
    (0,   50,  "Good",                "#00e400"),
    (51,  100, "Moderate",            "#ffff00"),
    (101, 150, "Unhealthy for Sensitive Groups", "#ff7e00"),
    (151, 200, "Unhealthy",           "#ff0000"),
    (201, 300, "Very Unhealthy",      "#8f3f97"),
    (301, 500, "Hazardous",           "#7e0023"),
]

def aqi_category(aqi):
    for lo, hi, label, color in AQI_BREAKPOINTS:
        if lo <= aqi <= hi:
            return label, color
    return "Hazardous", "#7e0023"

def aqi_color(aqi):
    return aqi_category(aqi)[1]

def aqi_label(aqi):
    return aqi_category(aqi)[0]

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("air_quality.csv")
    df.columns = df.columns.str.strip()
    # Normalise common column name variants
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if "city" in cl:           rename[c] = "City"
        elif "date" in cl:         rename[c] = "Date"
        elif "aqi" == cl:          rename[c] = "AQI"
        elif cl == "pm2.5" or cl == "pm25": rename[c] = "PM2.5"
        elif cl == "pm10":         rename[c] = "PM10"
        elif "no2" in cl:          rename[c] = "NO2"
        elif "so2" in cl:          rename[c] = "SO2"
        elif "co" == cl:           rename[c] = "CO"
        elif "o3" == cl or "ozone" in cl: rename[c] = "O3"
    df.rename(columns=rename, inplace=True)

    # If no AQI column, try to derive from PM2.5
    if "AQI" not in df.columns and "PM2.5" in df.columns:
        df["AQI"] = (df["PM2.5"] * 4).clip(0, 500).round()

    # Parse dates
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # AQI category & color
    if "AQI" in df.columns:
        df["AQI_Category"] = df["AQI"].apply(lambda x: aqi_label(x) if pd.notna(x) else "Unknown")
        df["AQI_Color"]    = df["AQI"].apply(lambda x: aqi_color(x) if pd.notna(x) else "#cccccc")

    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🌬️ AQI Dashboard")
st.sidebar.markdown("Air Quality Index Analysis")

# City filter
cities = sorted(df["City"].dropna().unique()) if "City" in df.columns else []
selected_cities = st.sidebar.multiselect("Select Cities", cities, default=cities[:5] if len(cities) > 5 else cities)

# Date filter
if "Date" in df.columns and df["Date"].notna().any():
    min_d = df["Date"].min().date()
    max_d = df["Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
else:
    date_range = None

filtered = df.copy()
if selected_cities:
    filtered = filtered[filtered["City"].isin(selected_cities)]
if date_range and len(date_range) == 2 and "Date" in filtered.columns:
    filtered = filtered[(filtered["Date"].dt.date >= date_range[0]) & (filtered["Date"].dt.date <= date_range[1])]

# ── Main header ───────────────────────────────────────────────────────────────
st.title("🌬️ Air Quality Index (AQI) Analysis")
st.markdown("Interactive dashboard for exploring air quality data across cities and time.")

# ── KPI row ───────────────────────────────────────────────────────────────────
if "AQI" in filtered.columns:
    avg_aqi  = filtered["AQI"].mean()
    max_aqi  = filtered["AQI"].max()
    min_aqi  = filtered["AQI"].min()
    n_cities = filtered["City"].nunique() if "City" in filtered.columns else "-"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📊 Avg AQI",   f"{avg_aqi:.1f}", help=aqi_label(avg_aqi))
    k2.metric("🔴 Max AQI",   f"{max_aqi:.0f}", help=aqi_label(max_aqi))
    k3.metric("🟢 Min AQI",   f"{min_aqi:.0f}", help=aqi_label(min_aqi))
    k4.metric("🏙️ Cities",    n_cities)

st.markdown("---")

# ── Row 1: AQI distribution + AQI by city ────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("AQI Distribution")
    if "AQI" in filtered.columns:
        fig = px.histogram(filtered, x="AQI", nbins=30, color="AQI_Category",
                           color_discrete_map={label: color for _, _, label, color in AQI_BREAKPOINTS},
                           title="Distribution of AQI Values")
        fig.update_layout(showlegend=True, bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Average AQI by City")
    if "City" in filtered.columns and "AQI" in filtered.columns:
        city_avg = (filtered.groupby("City")["AQI"].mean()
                            .sort_values(ascending=False)
                            .reset_index())
        city_avg["Color"] = city_avg["AQI"].apply(aqi_color)
        fig = px.bar(city_avg, x="City", y="AQI",
                     color="AQI", color_continuous_scale=["green","yellow","orange","red","purple","maroon"],
                     title="Average AQI per City")
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Time series ────────────────────────────────────────────────────────
if "Date" in filtered.columns and filtered["Date"].notna().any() and "AQI" in filtered.columns:
    st.subheader("AQI Trend Over Time")
    if "City" in filtered.columns:
        ts = filtered.groupby(["Date", "City"])["AQI"].mean().reset_index()
        fig = px.line(ts, x="Date", y="AQI", color="City", title="AQI Over Time by City")
    else:
        ts = filtered.groupby("Date")["AQI"].mean().reset_index()
        fig = px.line(ts, x="Date", y="AQI", title="AQI Over Time")
    # AQI band reference lines
    for lo, hi, label, color in AQI_BREAKPOINTS[:4]:
        fig.add_hline(y=lo, line_dash="dot", line_color=color, annotation_text=label, annotation_position="right")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Pollutant breakdown ────────────────────────────────────────────────
pollutants = [c for c in ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"] if c in filtered.columns]

if pollutants:
    st.subheader("Pollutant Breakdown")
    tab_labels = ["Box Plot", "Correlation Heatmap", "Scatter vs AQI"]
    t1, t2, t3 = st.tabs(tab_labels)

    with t1:
        fig = px.box(filtered.melt(value_vars=pollutants, var_name="Pollutant", value_name="Concentration"),
                     x="Pollutant", y="Concentration", color="Pollutant",
                     title="Pollutant Concentration Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        cols_for_corr = pollutants + (["AQI"] if "AQI" in filtered.columns else [])
        corr = filtered[cols_for_corr].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        title="Pollutant Correlation Matrix")
        st.plotly_chart(fig, use_container_width=True)

    with t3:
        if "AQI" in filtered.columns:
            pol = st.selectbox("Choose pollutant", pollutants)
            color_col = "City" if "City" in filtered.columns else None
            fig = px.scatter(filtered, x=pol, y="AQI", color=color_col,
                             trendline="ols", title=f"{pol} vs AQI")
            st.plotly_chart(fig, use_container_width=True)

# ── Row 4: AQI category pie + worst days ─────────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.subheader("AQI Category Breakdown")
    if "AQI_Category" in filtered.columns:
        cat_counts = filtered["AQI_Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        color_map = {label: color for _, _, label, color in AQI_BREAKPOINTS}
        fig = px.pie(cat_counts, names="Category", values="Count",
                     color="Category", color_discrete_map=color_map,
                     title="Days by AQI Category")
        st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Top 10 Worst AQI Records")
    if "AQI" in filtered.columns:
        worst_cols = ["City", "Date", "AQI", "AQI_Category"] if "City" in filtered.columns else ["Date", "AQI", "AQI_Category"]
        worst_cols = [c for c in worst_cols if c in filtered.columns]
        worst = filtered.nlargest(10, "AQI")[worst_cols].reset_index(drop=True)
        st.dataframe(worst, use_container_width=True)

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("📄 View Raw Data"):
    st.dataframe(filtered, use_container_width=True)
    st.download_button("⬇️ Download CSV", filtered.to_csv(index=False), "filtered_aqi.csv", "text/csv")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("AQI Analysis Dashboard · Data sourced from air_quality.csv")
