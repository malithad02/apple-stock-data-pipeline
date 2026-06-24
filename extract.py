# PURPOSE: Fetch raw stock data from Alpha Vantage and save as CSV

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY    = os.getenv("ALPHA_VANTAGE_API_KEY")
SYMBOL     = "AAPL"
OUTPUT_FILE = "raw_data.json"

def extract():
    print(f"Fetching data for {SYMBOL}...")

    url = "https://www.alphavantage.co/query"
    params = {
        "function":   "TIME_SERIES_DAILY",
        "symbol":     SYMBOL,
        "outputsize": "compact",   # last 100 days
        "apikey":     API_KEY
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        raise ValueError(f"API Error: {data['Error Message']}")

    # Save raw JSON to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Raw data saved to '{OUTPUT_FILE}'")
    print(f"   Total dates fetched: {len(data['Time Series (Daily)'])}")
    return data

if __name__ == "__main__":
    extract()