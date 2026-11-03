
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "warehouse" / "city_chaos.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# ==========================================
# 1. ROLL-UP: Daily -> Monthly -> Yearly
# ==========================================

def roll_up(level="monthly", pollutant="pm25"):

    allowed_pollutants = [
        "pm25", "pm10", "no2", "o3", "co", "so2", "aqi"
    ]

    if pollutant not in allowed_pollutants:
        raise ValueError("Invalid pollutant")

    if level == "daily":
        grouping = "d.full_date"
    elif level == "monthly":
        grouping = "d.year, d.month"
    elif level == "yearly":
        grouping = "d.year"
    else:
        raise ValueError("Level must be daily, monthly or yearly")

    query = f"""
        SELECT
            {grouping} AS period,
            AVG(f.{pollutant}) AS average_value,
            MAX(f.{pollutant}) AS maximum_value,
            MIN(f.{pollutant}) AS minimum_value,
            COUNT(f.{pollutant}) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY {grouping}
        ORDER BY {grouping}
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ==========================================
# 2. DRILL-DOWN: Year -> Month -> Day
# ==========================================

def drill_down(year, month=None):

    if month is None:
        query = """
            SELECT
                d.month,
                d.month_name,
                AVG(f.pm25) AS avg_pm25,
                AVG(f.aqi) AS avg_aqi,
                COUNT(f.pm25) AS observations
            FROM fact_air_quality f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.year = ?
            GROUP BY d.month, d.month_name
            ORDER BY d.month
        """

        params = (year,)

    else:
        query = """
            SELECT
                d.full_date,
                AVG(f.pm25) AS avg_pm25,
                AVG(f.aqi) AS avg_aqi,
                COUNT(f.pm25) AS observations
            FROM fact_air_quality f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.year = ? AND d.month = ?
            GROUP BY d.full_date
            ORDER BY d.full_date
        """

        params = (year, month)

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


# ==========================================
# 3. SLICE: Select one season
# ==========================================

def slice_data(season, pollutant="pm25"):

    allowed = [
        "pm25", "pm10", "no2", "o3", "co", "so2", "aqi"
    ]

    if pollutant not in allowed:
        raise ValueError("Invalid pollutant")

    query = f"""
        SELECT
            d.year,
            d.season,
            AVG(f.{pollutant}) AS average_value,
            COUNT(f.{pollutant}) AS observations
        FROM fact_air_quality f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.season = ?
        GROUP BY d.year, d.season
        ORDER BY d.year
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=(season,))


# ==========================================
# 4. DICE: Multiple dimensions
# ==========================================

def dice_data(station, start_year, end_year, season):

    query = """
        SELECT
            s.station_name,
            d.year,
            d.season,
            AVG(f.pm25) AS avg_pm25,
            AVG(f.pm10) AS avg_pm10,
            AVG(f.aqi) AS avg_aqi,
            COUNT(f.pm25) AS observations
        FROM fact_air_quality f

        JOIN dim_date d
            ON f.date_key = d.date_key

        JOIN dim_station s
            ON f.station_key = s.station_key

        WHERE s.station_name = ?
          AND d.year BETWEEN ? AND ?
          AND d.season = ?

        GROUP BY s.station_name, d.year, d.season
        ORDER BY d.year
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(station, start_year, end_year, season)
        )


# ==========================================
# 5. PIVOT: Station vs Month
# ==========================================

def pivot_data(year, pollutant="pm25"):

    allowed = [
        "pm25", "pm10", "no2", "o3", "co", "so2", "aqi"
    ]

    if pollutant not in allowed:
        raise ValueError("Invalid pollutant")

    query = f"""
        SELECT
            s.station_name,

            AVG(CASE WHEN d.month = 1 THEN f.{pollutant} END) AS Jan,
            AVG(CASE WHEN d.month = 2 THEN f.{pollutant} END) AS Feb,
            AVG(CASE WHEN d.month = 3 THEN f.{pollutant} END) AS Mar,
            AVG(CASE WHEN d.month = 4 THEN f.{pollutant} END) AS Apr,
            AVG(CASE WHEN d.month = 5 THEN f.{pollutant} END) AS May,
            AVG(CASE WHEN d.month = 6 THEN f.{pollutant} END) AS Jun,
            AVG(CASE WHEN d.month = 7 THEN f.{pollutant} END) AS Jul,
            AVG(CASE WHEN d.month = 8 THEN f.{pollutant} END) AS Aug,
            AVG(CASE WHEN d.month = 9 THEN f.{pollutant} END) AS Sep,
            AVG(CASE WHEN d.month = 10 THEN f.{pollutant} END) AS Oct,
            AVG(CASE WHEN d.month = 11 THEN f.{pollutant} END) AS Nov,
            AVG(CASE WHEN d.month = 12 THEN f.{pollutant} END) AS Dec

        FROM fact_air_quality f

        JOIN dim_date d
            ON f.date_key = d.date_key

        JOIN dim_station s
            ON f.station_key = s.station_key

        WHERE d.year = ?

        GROUP BY s.station_name
        ORDER BY s.station_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=(year,))


# ==========================================
# TEST ALL FIVE OPERATIONS
# ==========================================

if __name__ == "__main__":

    print("\n========== OLAP ENGINE TEST ==========")

    print("\n1. ROLL-UP: Monthly PM2.5")
    print(roll_up("monthly", "pm25").head(10))

    print("\n2. DRILL-DOWN: Year 2025")
    print(drill_down(2025).head(10))

    print("\n3. SLICE: Monsoon PM2.5")
    print(slice_data("Monsoon", "pm25"))

    print("\n4. DICE: Kurla, 2019-2022, Monsoon")

    with get_connection() as conn:
        stations = pd.read_sql_query(
            "SELECT station_name FROM dim_station", conn
        )

    kurla = stations[
        stations["station_name"].str.contains("Kurla", case=False)
        & ~stations["station_name"].str.contains(
            "Complex", case=False
        )
    ]

    if not kurla.empty:
        print(dice_data(
            kurla.iloc[0]["station_name"],
            2019, 2022, "Monsoon"
        ))

    print("\n5. PIVOT: Station vs Month (2025)")
    print(pivot_data(2025, "pm25"))

    print("\n========== OLAP TEST COMPLETE ==========")
