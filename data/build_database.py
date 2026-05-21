import os
import pandas as pd
import duckdb
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# Just 2 series — keep it simple
SERIES = [
    ("FEDFUNDS", "Federal Funds Rate",  "monetary_policy"),
    ("SP500",    "S&P 500 Index",       "stock_market"),
]

# --- EXTRACT ---
obs_frames = []
for series_id, title, category in SERIES:
    print(f"Fetching {series_id}...")
    raw = fred.get_series(series_id,
        observation_start="2000-01-01",
        observation_end="2024-12-31")
    df = raw.dropna().reset_index()
    df.columns = ["date", "value"]
    df["series_id"] = series_id
    df["date"] = pd.to_datetime(df["date"])
    obs_frames.append(df[["series_id", "date", "value"]])

df_obs = pd.concat(obs_frames, ignore_index=True)
df_series = pd.DataFrame(
    SERIES,
    columns=["series_id", "title", "category"]
)

# --- LOAD ---
conn = duckdb.connect("data/mini.db")

conn.execute("""
    CREATE TABLE series (
        series_id VARCHAR PRIMARY KEY,
        title     VARCHAR,
        category  VARCHAR
    )
""")

conn.execute("""
    CREATE TABLE observations (
        series_id VARCHAR REFERENCES series(series_id),
        date      DATE,
        value     DOUBLE,
        PRIMARY KEY (series_id, date)
    )
""")

conn.execute("INSERT INTO series SELECT * FROM df_series")
conn.execute("INSERT INTO observations SELECT * FROM df_obs")

print("Database built successfully!")
conn.close()