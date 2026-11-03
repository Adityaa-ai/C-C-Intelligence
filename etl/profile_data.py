
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

csv_files = list(DATA_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found in data/raw/")
    raise SystemExit(1)

for file in csv_files:
    print("\n" + "=" * 60)
    print("FILE:", file.name)
    print("=" * 60)

    df = pd.read_csv(file)

    print("\nDataset Shape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 Records:")
    print(df.head())

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nDuplicate Rows:", df.duplicated().sum())

    print("\nData Types:")
    print(df.dtypes)

    print("\nStatistical Summary:")
    print(df.describe(include="all").T)
