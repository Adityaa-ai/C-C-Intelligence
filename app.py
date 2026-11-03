
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# =========================================
# CONFIGURATION
# =========================================

st.set_page_config(
    page_title="City Chaos Intelligence",
    page_icon="🌆",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "warehouse" / "city_chaos.db"

POLLUTANTS = ["pm25", "pm10", "no2", "o3", "co", "so2", "aqi"]

st.markdown("""
<style>
.main {
    background-color: #0b1120;
}
[data-testid="stMetric"] {
    background: #151f32;
    padding: 18px;
    border: 1px solid #29364d;
    border-radius: 12px;
}
[data-testid="stSidebar"] {
    background-color: #101a2b;
}
h1, h2, h3 {
    color: #f1f5f9;
}
</style>
""", unsafe_allow_html=True)


# =========================================
# DATABASE
# =========================================

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        f.*,
        d.full_date,
        d.day,
        d.month,
        d.month_name,
        d.quarter,
        d.year,
        d.season,
        s.station_name,
        s.station_id,
        s.city
    FROM fact_air_quality f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_station s ON f.station_key = s.station_key
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["full_date"] = pd.to_datetime(df["full_date"])
    return df


df = load_data()

if df.empty:
    st.error("Warehouse contains no records.")
    st.stop()


# =========================================
# SIDEBAR
# =========================================

st.sidebar.title("🌆 CITY CHAOS")
st.sidebar.caption("URBAN INTELLIGENCE PLATFORM")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Executive Overview",
        "Air Quality Analytics",
        "OLAP Explorer",
        "Data Mining Lab",
        "Warehouse Monitor"
    ]
)

st.sidebar.divider()
st.sidebar.success("Warehouse Connected")
st.sidebar.caption("Mumbai | Historical Air Quality")


# =========================================
# HEADER
# =========================================

st.title("🌆 City Chaos Intelligence")
st.caption(
    "REAL-WORLD URBAN DATA | DATA WAREHOUSING | "
    "MULTIDIMENSIONAL ANALYTICS"
)

st.divider()


# =========================================
# HELPER
# =========================================

def metric_mean(column):
    return df[column].mean()


def get_filtered_data(data, station=None, year=None):
    result = data.copy()

    if station and station != "All Stations":
        result = result[result["station_name"] == station]

    if year and year != "All Years":
        result = result[result["year"] == int(year)]

    return result


# =========================================
# 1. EXECUTIVE OVERVIEW
# =========================================

if page == "Executive Overview":

    st.subheader("Executive Command Center")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Observations", f"{len(df):,}")
    c2.metric("Monitoring Stations", df["station_id"].nunique())
    c3.metric("Average PM2.5", f"{df['pm25'].mean():.2f}")
    c4.metric("Available AQI Records", f"{df['aqi'].notna().sum():,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        monthly = (
            df.groupby(["year", "month"])["pm25"]
            .mean()
            .reset_index()
        )

        monthly["period"] = pd.to_datetime(
            monthly["year"].astype(str) + "-"
            + monthly["month"].astype(str) + "-01"
        )

        fig = px.line(
            monthly,
            x="period",
            y="pm25",
            markers=True,
            title="Monthly Average PM2.5"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        station_data = (
            df.groupby("station_name")["pm25"]
            .mean()
            .reset_index()
            .sort_values("pm25", ascending=False)
        )

        fig = px.bar(
            station_data,
            x="station_name",
            y="pm25",
            color="pm25",
            title="Station-wise PM2.5 Comparison"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pollutant Distribution")

    pollutant = st.selectbox(
        "Select pollutant",
        POLLUTANTS
    )

    fig = px.histogram(
        df.dropna(subset=[pollutant]),
        x=pollutant,
        nbins=40,
        title=f"{pollutant.upper()} Distribution"
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Warehouse Records")
    st.dataframe(
        df[[
            "full_date", "station_name",
            "pm25", "pm10", "no2", "aqi"
        ]].tail(20),
        use_container_width=True
    )


# =========================================
# 2. AIR QUALITY ANALYTICS
# =========================================

elif page == "Air Quality Analytics":

    st.subheader("Air Quality Intelligence")

    stations = ["All Stations"] + sorted(
        df["station_name"].dropna().unique().tolist()
    )

    years = ["All Years"] + sorted(
        df["year"].dropna().astype(int).unique().tolist(),
        reverse=True
    )

    selected_station = st.selectbox("Monitoring Station", stations)
    selected_year = st.selectbox("Year", years)

    filtered = get_filtered_data(
        df, selected_station, selected_year
    )

    pollutant = st.selectbox(
        "Choose pollutant",
        POLLUTANTS
    )

    col1, col2 = st.columns(2)

    col1.metric(
        f"Average {pollutant.upper()}",
        f"{filtered[pollutant].mean():.2f}"
    )

    col2.metric(
        "Available Measurements",
        f"{filtered[pollutant].count():,}"
    )

    trend = (
        filtered.groupby("full_date")[pollutant]
        .mean()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="full_date",
        y=pollutant,
        title=f"{pollutant.upper()} Historical Trend",
        markers=True
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Seasonal Comparison")

    seasonal = (
        filtered.groupby("season")[pollutant]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        seasonal,
        x="season",
        y=pollutant,
        color="season",
        title="Average Pollutant by Season"
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


# =========================================
# 3. OLAP EXPLORER
# =========================================

elif page == "OLAP Explorer":

    st.subheader("Multidimensional OLAP Explorer")

    operation = st.selectbox(
        "Select OLAP Operation",
        ["Roll-up", "Drill-down", "Slice", "Dice", "Pivot"]
    )

    pollutant = st.selectbox(
        "Select Measure",
        POLLUTANTS
    )

    conn = sqlite3.connect(DB_PATH)

    if operation == "Roll-up":

        level = st.selectbox(
            "Aggregation Level",
            ["Yearly", "Monthly", "Daily"]
        )

        if level == "Yearly":
            group = "d.year"
        elif level == "Monthly":
            group = "d.year, d.month"
        else:
            group = "d.full_date"

        query = f"""
        SELECT
            {group},
            AVG(f.{pollutant}) AS average_value,
            MAX(f.{pollutant}) AS maximum_value,
            COUNT(f.{pollutant}) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY {group}
        ORDER BY {group}
        """

        result = pd.read_sql_query(query, conn)

        st.info(f"ROLL-UP: Aggregation at {level} level")

        st.dataframe(result, use_container_width=True)

        fig = px.line(
            result,
            x=result.columns[0],
            y="average_value",
            markers=True,
            title=f"{pollutant.upper()} - {level} Roll-up"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif operation == "Drill-down":

        years = sorted(
            df["year"].dropna().astype(int).unique()
        )

        year = st.selectbox("Select Year", years)

        query = """
        SELECT
            d.month,
            d.month_name,
            AVG(f.pm25) AS average_pm25,
            AVG(f.aqi) AS average_aqi,
            COUNT(f.pm25) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.year = ?
        GROUP BY d.month, d.month_name
        ORDER BY d.month
        """

        result = pd.read_sql_query(
            query, conn, params=(year,)
        )

        st.info(f"DRILL-DOWN: Year {year} → Month")

        st.dataframe(result, use_container_width=True)

        fig = px.bar(
            result,
            x="month_name",
            y="average_pm25",
            title="Monthly PM2.5 Breakdown"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif operation == "Slice":

        season = st.selectbox(
            "Select Season",
            sorted(df["season"].dropna().unique())
        )

        query = f"""
        SELECT
            d.year,
            AVG(f.{pollutant}) AS average_value,
            COUNT(f.{pollutant}) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.season = ?
        GROUP BY d.year
        ORDER BY d.year
        """

        result = pd.read_sql_query(
            query, conn, params=(season,)
        )

        st.info(f"SLICE: Selected season = {season}")

        st.dataframe(result, use_container_width=True)

        fig = px.line(
            result,
            x="year",
            y="average_value",
            markers=True,
            title=f"{pollutant.upper()} - {season}"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif operation == "Dice":

        stations = sorted(
            df["station_name"].dropna().unique()
        )

        station = st.selectbox("Station", stations)

        year_values = sorted(
            df["year"].dropna().astype(int).unique()
        )

        start_year = st.selectbox("Start Year", year_values)
        end_year = st.selectbox(
            "End Year",
            [y for y in year_values if y >= start_year]
        )

        season = st.selectbox(
            "Season",
            sorted(df["season"].dropna().unique())
        )

        query = f"""
        SELECT
            s.station_name,
            d.year,
            d.season,
            AVG(f.{pollutant}) AS average_value,
            COUNT(f.{pollutant}) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_station s ON f.station_key = s.station_key
        WHERE s.station_name = ?
          AND d.year BETWEEN ? AND ?
          AND d.season = ?
        GROUP BY s.station_name, d.year, d.season
        ORDER BY d.year
        """

        result = pd.read_sql_query(
            query,
            conn,
            params=(station, start_year, end_year, season)
        )

        st.info("DICE: Multiple dimensions filtered together")

        st.dataframe(result, use_container_width=True)

        fig = px.bar(
            result,
            x="year",
            y="average_value",
            title=f"{pollutant.upper()} - {station}"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif operation == "Pivot":

        year_values = sorted(
            df["year"].dropna().astype(int).unique()
        )

        year = st.selectbox("Select Year", year_values)

        query = f"""
        SELECT
            s.station_name,
            d.month,
            AVG(f.{pollutant}) AS average_value
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_station s ON f.station_key = s.station_key
        WHERE d.year = ?
        GROUP BY s.station_name, d.month
        """

        result = pd.read_sql_query(
            query, conn, params=(year,)
        )

        pivot = result.pivot(
            index="station_name",
            columns="month",
            values="average_value"
        )

        st.info("PIVOT: Station versus Month")

        st.dataframe(
            pivot,
            use_container_width=True
        )

        fig = px.imshow(
            pivot,
            aspect="auto",
            color_continuous_scale="Viridis",
            title=f"{pollutant.upper()} Station-Month Heatmap"
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    conn.close()


# =========================================
# 4. DATA MINING LAB
# =========================================

elif page == "Data Mining Lab":

    st.subheader("Data Mining & Statistical Analysis")

    st.markdown("### Pollutant Correlation Matrix")

    numeric = df[POLLUTANTS].corr()

    fig = px.imshow(
        numeric,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Pollutant Correlation Heatmap"
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Anomaly Detection")

    from sklearn.ensemble import IsolationForest

    features = ["pm25", "pm10", "no2", "so2"]

    mining_data = df[features].dropna()

    if len(mining_data) >= 20:

        contamination = st.slider(
            "Expected anomaly proportion",
            0.01, 0.15, 0.05
        )

        model = IsolationForest(
            contamination=contamination,
            random_state=42
        )

        labels = model.fit_predict(mining_data)

        mining_data = mining_data.copy()
        mining_data["anomaly"] = labels

        anomalies = mining_data[
            mining_data["anomaly"] == -1
        ]

        st.metric("Flagged Anomalies", len(anomalies))

        st.dataframe(
            anomalies.head(100),
            use_container_width=True
        )

        st.caption(
            "These are statistical multivariate anomalies, "
            "not confirmed pollution events or faulty sensors."
        )

    else:
        st.warning("Not enough complete records for anomaly analysis.")


# =========================================
# 5. WAREHOUSE MONITOR
# =========================================

elif page == "Warehouse Monitor":

    st.subheader("Data Warehouse Monitor")

    conn = sqlite3.connect(DB_PATH)

    tables = [
        "dim_date",
        "dim_station",
        "fact_air_quality"
    ]

    for table in tables:
        count = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {table}",
            conn
        )["total"].iloc[0]

        st.metric(table.upper(), f"{count:,}")

    st.divider()

    st.markdown("### Database Table Preview")

    selected_table = st.selectbox("Choose Table", tables)

    preview = pd.read_sql_query(
        f"SELECT * FROM {selected_table} LIMIT 100",
        conn
    )

    st.dataframe(preview, use_container_width=True)

    st.markdown("### Data Quality")

    quality = pd.read_sql_query("""
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN pm25 IS NULL THEN 1 ELSE 0 END)
                AS missing_pm25,
            SUM(CASE WHEN aqi IS NULL THEN 1 ELSE 0 END)
                AS missing_aqi
        FROM fact_air_quality
    """, conn)

    st.dataframe(quality, use_container_width=True)

    foreign_keys = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if not foreign_keys:
        st.success("Foreign key integrity check passed.")
    else:
        st.error(f"Foreign key issues: {len(foreign_keys)}")

    conn.close()


# =========================================
# FOOTER
# =========================================

st.divider()

st.caption(
    "CITY CHAOS INTELLIGENCE 2.0 | "
    "Urban Environmental Analytics | "
    "Data Warehouse & OLAP System"
)
