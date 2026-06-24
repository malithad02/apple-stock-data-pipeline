import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Check if API key is loaded
print("API Key loaded:", API_KEY)

url = "https://www.alphavantage.co/query"
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol":   "AAPL",
    "apikey":   API_KEY
}

response = requests.get(url, params=params)
data = response.json()

# Print the full response to see what's coming back
print("Response keys:", data.keys())

# Check if data exists
if "Time Series (Daily)" in data:
    dates = list(data["Time Series (Daily)"].keys())[:3]
    print("✅ API working! Latest dates:")
    for d in dates:
        print(" →", d)
else:
    print("❌ Something wrong. Full response:")
    print(data)