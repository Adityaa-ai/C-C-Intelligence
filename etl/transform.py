
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "data" / "raw" / "all_stations_combined.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load original data
df = pd.read_csv(RAW_PATH)

print("Starting ETL transformation...")
print("Original records:", len(df))

# 1. Preserve source data
df["source_date"] = df["date"].astype(str)

# 2. Convert date
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# 3. Standardize text columns
for col in ["city", "station_name", "dominant_pollutant"]:
    df[col] = df[col].astype("string").str.strip()

# 4. Handle negative pollutant readings
pollutants = ["co", "no2", "o3", "pm10", "pm25", "so2"]

quality_report = {
    "original_rows": int(len(df)),
    "negative_values": {},
    "outliers": {},
    "missing_values": {}
}

for col in pollutants:
    # Record invalid negative values
    negative_mask = df[col] < 0

    quality_report["negative_values"][col] = int(
        negative_mask.sum()
    )

    # Preserve original readings for audit
    df[f"{col}_source"] = df[col]

    # Exclude negative readings from cleaned analytical column
    df.loc[negative_mask, col] = np.nan

    # Calculate IQR bounds using available non-negative readings
    series = df[col].dropna()

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    # Flag, do not delete extreme observations
    df[f"{col}_outlier_flag"] = (
        (df[col] < lower) | (df[col] > upper)
    ).fillna(False)

    quality_report["outliers"][col] = int(
        df[f"{col}_outlier_flag"].sum()
    )

# 5. Validate station-date keys
duplicate_keys = df.duplicated(
    subset=["station_id", "date"]
).sum()

quality_report["duplicate_station_date_keys"] = int(
    duplicate_keys
)

# 6. Missing value report
quality_report["missing_values"] = {
    col: int(value)
    for col, value in df.isna().sum().items()
}

# 7. Preserve AQI exactly as supplied
# No assumed replacement of 401 or missing values.

# 8. Add date hierarchy
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["month_name"] = df["date"].dt.month_name()
df["quarter"] = df["date"].dt.quarter
df["day"] = df["date"].dt.day
df["season"] = df["month"].map({
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Summer", 4: "Summer", 5: "Summer",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon",
    9: "Monsoon", 10: "Post-Monsoon",
    11: "Post-Monsoon"
})

# 9. Save processed data
output_path = OUTPUT_DIR / "air_quality_cleaned.csv"
df.to_csv(output_path, index=False)

# 10. Save data quality report
report_path = OUTPUT_DIR / "quality_report.json"

with open(report_path, "w") as file:
    json.dump(quality_report, file, indent=4)

print("\nTransformation completed!")
print("Processed rows:", len(df))
print("Duplicate station-date keys:", duplicate_keys)
print("Cleaned dataset:", output_path)
print("Quality report:", report_path)
print("\nOutlier counts:", quality_report["outliers"])
