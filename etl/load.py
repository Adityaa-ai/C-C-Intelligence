
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "air_quality_cleaned.csv"
DB_PATH = BASE_DIR / "warehouse" / "city_chaos.db"
SCHEMA_PATH = BASE_DIR / "warehouse" / "schema.sql"

# Load processed dataset
df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Generate date keys
df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)

# Open database
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

try:
    # Create warehouse tables
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        conn.executescript(file.read())

    # Clear old data so the script can be rerun safely
    conn.execute("DELETE FROM fact_air_quality")
    conn.execute("DELETE FROM dim_station")
    conn.execute("DELETE FROM dim_date")
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name='dim_station'"
    )

    # -------------------------------
    # 1. LOAD DATE DIMENSION
    # -------------------------------
    dates = df.drop_duplicates("date")[
        ["date", "day", "month", "month_name",
         "quarter", "year", "season"]
    ].copy()

    dates["full_date"] = dates["date"].dt.strftime("%Y-%m-%d")
    dates["date_key"] = dates["date"].dt.strftime("%Y%m%d").astype(int)

    date_records = [
        (
            int(r.date_key),
            r.full_date,
            int(r.day),
            int(r.month),
            r.month_name,
            int(r.quarter),
            int(r.year),
            r.season
        )
        for r in dates.itertuples(index=False)
    ]

    conn.executemany("""
        INSERT INTO dim_date
        (date_key, full_date, day, month, month_name,
         quarter, year, season)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, date_records)

    # -------------------------------
    # 2. LOAD STATION DIMENSION
    # -------------------------------
    stations = df[
        ["station_id", "station_name", "city"]
    ].drop_duplicates("station_id")

    conn.executemany("""
        INSERT INTO dim_station
        (station_id, station_name, city)
        VALUES (?, ?, ?)
    """, [
        (int(r.station_id), r.station_name, r.city)
        for r in stations.itertuples(index=False)
    ])

    station_map = dict(
        conn.execute(
            "SELECT station_id, station_key FROM dim_station"
        ).fetchall()
    )

    # -------------------------------
    # 3. LOAD FACT TABLE
    # -------------------------------
    pollutants = ["pm25", "pm10", "no2", "o3", "co", "so2"]

    def db_value(value):
        return None if pd.isna(value) else value.item() if hasattr(value, "item") else value

    fact_records = []

    for r in df.itertuples(index=False):
        record = [
            int(r.date_key),
            station_map[int(r.station_id)]
        ]

        for col in ["pm25", "pm10", "no2", "o3", "co", "so2", "aqi"]:
            record.append(db_value(getattr(r, col)))

        record.append(db_value(r.dominant_pollutant))

        for col in pollutants:
            record.append(
                int(getattr(r, f"{col}_outlier_flag"))
            )

        fact_records.append(tuple(record))

    conn.executemany("""
        INSERT INTO fact_air_quality (
            date_key, station_key,
            pm25, pm10, no2, o3, co, so2, aqi,
            dominant_pollutant,
            pm25_outlier, pm10_outlier,
            no2_outlier, o3_outlier,
            co_outlier, so2_outlier
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_records)

    conn.commit()

    # -------------------------------
    # 4. WAREHOUSE VALIDATION
    # -------------------------------
    print("\n========== WAREHOUSE LOADED ==========")

    for table in ["dim_date", "dim_station", "fact_air_quality"]:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count} records")

    foreign_key_errors = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print("Foreign key errors:", len(foreign_key_errors))

    print("Database:", DB_PATH)
    print("ETL LOAD SUCCESSFUL!")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
