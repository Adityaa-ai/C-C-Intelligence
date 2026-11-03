
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    day INTEGER,
    month INTEGER,
    month_name TEXT,
    quarter INTEGER,
    year INTEGER,
    season TEXT
);

CREATE TABLE IF NOT EXISTS dim_station (
    station_key INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id INTEGER NOT NULL UNIQUE,
    station_name TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_air_quality (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,

    date_key INTEGER NOT NULL,
    station_key INTEGER NOT NULL,

    pm25 REAL,
    pm10 REAL,
    no2 REAL,
    o3 REAL,
    co REAL,
    so2 REAL,
    aqi REAL,

    dominant_pollutant TEXT,

    pm25_outlier INTEGER DEFAULT 0,
    pm10_outlier INTEGER DEFAULT 0,
    no2_outlier INTEGER DEFAULT 0,
    o3_outlier INTEGER DEFAULT 0,
    co_outlier INTEGER DEFAULT 0,
    so2_outlier INTEGER DEFAULT 0,

    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (station_key) REFERENCES dim_station(station_key),

    UNIQUE (date_key, station_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_date
ON fact_air_quality(date_key);

CREATE INDEX IF NOT EXISTS idx_fact_station
ON fact_air_quality(station_key);

CREATE INDEX IF NOT EXISTS idx_fact_aqi
ON fact_air_quality(aqi);
