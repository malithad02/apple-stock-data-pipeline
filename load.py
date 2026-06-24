# load.py
# PURPOSE: Read transformed CSV and load into Snowflake

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

INPUT_FILE   = "transformed_data.csv"
TARGET_TABLE = "APPLE_STOCK_DAILY"

SNOWFLAKE_CONFIG = {
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database":  os.getenv("SNOWFLAKE_DATABASE"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA"),
}

def validate_config():
    """Check all Snowflake credentials are loaded from .env"""
    missing = []
    for key, value in SNOWFLAKE_CONFIG.items():
        if not value:
            missing.append(f"SNOWFLAKE_{key.upper()}")
    if missing:
        raise EnvironmentError(
            f"❌ Missing in .env file: {', '.join(missing)}"
        )
    print("✅ Snowflake credentials loaded successfully.")


def load():
    print("=" * 45)
    print("   LOAD STEP STARTING")
    print("=" * 45)

    # Validate credentials first
    validate_config()

    # Read transformed CSV
    print("\nReading transformed_data.csv...")
    df = pd.read_csv(INPUT_FILE)

    # Fix data types
    df["TRADE_DATE"] = pd.to_datetime(df["TRADE_DATE"]).dt.date
    df["OPEN"]       = pd.to_numeric(df["OPEN"],   errors="coerce")
    df["HIGH"]       = pd.to_numeric(df["HIGH"],   errors="coerce")
    df["LOW"]        = pd.to_numeric(df["LOW"],    errors="coerce")
    df["CLOSE"]      = pd.to_numeric(df["CLOSE"],  errors="coerce")
    df["VOLUME"]     = pd.to_numeric(df["VOLUME"], errors="coerce").astype("Int64")
    df["LOADED_AT"]  = datetime.utcnow()

    # Keep only Snowflake table columns — drop SOURCE column
    df = df[["TRADE_DATE", "SYMBOL", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME", "LOADED_AT"]]

    print(f"   Rows to load : {len(df)}")
    print(f"   Date range   : {df['TRADE_DATE'].min()} → {df['TRADE_DATE'].max()}")

    # Connect to Snowflake
    print("\nConnecting to Snowflake...")
    conn   = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()

    try:
        # Create table if not exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
                TRADE_DATE  DATE         NOT NULL,
                SYMBOL      VARCHAR(10)  NOT NULL,
                OPEN        FLOAT,
                HIGH        FLOAT,
                LOW         FLOAT,
                CLOSE       FLOAT,
                VOLUME      BIGINT,
                LOADED_AT   TIMESTAMP_NTZ,
                PRIMARY KEY (TRADE_DATE, SYMBOL)
            )
        """)
        print(f"   Table '{TARGET_TABLE}' ready.")

        # Clear old data and reload fresh
        cursor.execute(f"TRUNCATE TABLE {TARGET_TABLE}")
        print("   Old rows cleared.")

        # Load data into Snowflake
        print("   Uploading data...")
        success, num_chunks, num_rows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=TARGET_TABLE,
            auto_create_table=False,
            overwrite=False,
        )

        if success:
            print(f"\n✅ {num_rows} rows loaded into Snowflake successfully!")
        else:
            print("❌ Load failed.")

    finally:
        cursor.close()
        conn.close()
        print("   Snowflake connection closed.")


if __name__ == "__main__":
    load()