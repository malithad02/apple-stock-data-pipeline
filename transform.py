# transform.py
# PURPOSE: Combine Yahoo CSV + Alpha Vantage JSON, clean and save as one CSV

import json
import pandas as pd
from datetime import datetime

YAHOO_FILE  = "yahoo_data.csv"       # ← your Yahoo historical data file
API_FILE    = "raw_data.json"        # ← Alpha Vantage API data
OUTPUT_FILE = "transformed_data.csv" # ← final combined output


def transform_yahoo(filepath):
    print("Reading Yahoo Finance data...")

    # Skip first 2 rows (Ticker row and Date label row)
    df = pd.read_csv(filepath, skiprows=2, header=None)

    # Manually assign column names based on what we saw
    df.columns = ["TRADE_DATE", "CLOSE", "HIGH", "LOW", "OPEN", "VOLUME"]

    # Drop any empty or bad rows
    df = df.dropna(subset=["TRADE_DATE"])
    df = df[df["TRADE_DATE"] != "Date"]  # remove any leftover header rows

    # Fix data types
    df["TRADE_DATE"] = pd.to_datetime(df["TRADE_DATE"]).dt.date
    df["OPEN"]       = pd.to_numeric(df["OPEN"],   errors="coerce")
    df["HIGH"]       = pd.to_numeric(df["HIGH"],   errors="coerce")
    df["LOW"]        = pd.to_numeric(df["LOW"],    errors="coerce")
    df["CLOSE"]      = pd.to_numeric(df["CLOSE"],  errors="coerce")
    df["VOLUME"]     = pd.to_numeric(df["VOLUME"], errors="coerce")

    # Drop rows where all price columns are NaN
    df = df.dropna(subset=["OPEN", "HIGH", "LOW", "CLOSE"])

    # Add extra columns
    df["SYMBOL"]    = "AAPL"
    df["LOADED_AT"] = datetime.utcnow()
    df["SOURCE"]    = "Yahoo Finance"

    # Keep only needed columns in correct order
    df = df[["TRADE_DATE", "SYMBOL", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME", "LOADED_AT", "SOURCE"]]

    print(f"   ✅ Yahoo rows loaded: {len(df)}")
    return df


def transform_api(filepath):
    print("Reading Alpha Vantage API data...")

    with open(filepath, "r") as f:
        data = json.load(f)

    time_series = data["Time Series (Daily)"]

    records = []
    for date_str, values in time_series.items():
        records.append({
            "TRADE_DATE": datetime.strptime(date_str, "%Y-%m-%d").date(),
            "SYMBOL":     "AAPL",
            "OPEN":       float(values["1. open"]),
            "HIGH":       float(values["2. high"]),
            "LOW":        float(values["3. low"]),
            "CLOSE":      float(values["4. close"]),
            "VOLUME":     int(values["5. volume"]),
            "LOADED_AT":  datetime.utcnow(),
            "SOURCE":     "Alpha Vantage"
        })

    df = pd.DataFrame(records)
    print(f"   ✅ API rows loaded: {len(df)}")
    return df


def check_missing_days(df):
    print("\nChecking for unexpected missing days...")

    full_dates     = pd.bdate_range(
        start=df["TRADE_DATE"].min(),
        end=df["TRADE_DATE"].max()
    )
    existing_dates = pd.to_datetime(df["TRADE_DATE"])
    missing        = full_dates[~full_dates.isin(existing_dates)]

    if len(missing) == 0:
        print("✅ No unexpected missing weekdays!")
    else:
        print(f"⚠️  Found {len(missing)} missing weekdays (holidays are normal):")
        print(missing.strftime("%Y-%m-%d").tolist()[:10])


def transform():
    print("=" * 45)
    print("   TRANSFORM STEP STARTING")
    print("=" * 45)

    # Load both sources
    df_yahoo = transform_yahoo(YAHOO_FILE)
    df_api   = transform_api(API_FILE)

    # Combine both DataFrames
    df_combined = pd.concat([df_yahoo, df_api], ignore_index=True)

    # Remove duplicates — keep Alpha Vantage if same date exists
    df_combined = df_combined.sort_values(
        ["TRADE_DATE", "SOURCE"],
        ascending=[True, False]
    )
    df_combined = df_combined.drop_duplicates(subset="TRADE_DATE", keep="first")

    # Final sort by date
    df_combined = df_combined.sort_values("TRADE_DATE").reset_index(drop=True)

    # Check for missing days
    check_missing_days(df_combined)

    # Save to CSV
    df_combined.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ Combined data saved to '{OUTPUT_FILE}'")
    print(f"   Yahoo rows   : {len(df_yahoo)}")
    print(f"   API rows     : {len(df_api)}")
    print(f"   Total rows   : {len(df_combined)}")
    print(f"   Date range   : {df_combined['TRADE_DATE'].min()} → {df_combined['TRADE_DATE'].max()}")
    print(f"\nPreview (first 3 rows):")
    print(df_combined.head(3).to_string(index=False))
    print(f"\nPreview (last 3 rows):")
    print(df_combined.tail(3).to_string(index=False))

    return df_combined


if __name__ == "__main__":
    transform()