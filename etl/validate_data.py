
import pandas as pd
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "raw" / "all_stations_combined.csv"
)

df = pd.read_csv(DATA_PATH)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

print("\n========== DATASET VALIDATION ==========")

# 1. Date coverage
print("\nDATE COVERAGE")
print("Start:", df["date"].min())
print("End:", df["date"].max())
print("Unique dates:", df["date"].nunique())

# 2. Station distribution
print("\nSTATION DISTRIBUTION")
print(df.groupby("station_name").agg(
    records=("station_id", "count"),
    start_date=("date", "min"),
    end_date=("date", "max")
).to_string())

# 3. Missing percentage
print("\nMISSING VALUE PERCENTAGE")
missing = (df.isnull().mean() * 100).round(2)
print(missing.to_string())

# 4. Duplicate station-date combinations
print("\nDUPLICATE STATION-DATE KEYS")
print(
    df.duplicated(subset=["station_id", "date"]).sum()
)

# 5. Negative values
pollutants = ["co", "no2", "o3", "pm10", "pm25", "so2"]

print("\nNEGATIVE POLLUTANT VALUES")
for col in pollutants:
    print(col, ":", (df[col] < 0).sum())

# 6. Extreme values using IQR
print("\nEXTREME VALUE COUNTS (IQR)")
for col in pollutants:
    series = df[col].dropna()

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    count = ((series < lower) | (series > upper)).sum()

    print(col, ":", count)

# 7. AQI distribution
print("\nAQI DISTRIBUTION")
print(df["aqi"].describe())

print("\n========== VALIDATION COMPLETE ==========")
