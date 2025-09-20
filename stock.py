import requests
import pandas as pd
from sqlalchemy import insert
from db import get_engine
from models import StockPrice
from dotenv import load_dotenv
import os

# Load API key and DB credentials
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")

def fetch_stock_price(symbol="AAPL"):
    """
    Fetch current stock price, high, low, open, previous close, price change, percent change, and timestamp from Finnhub API.
    Returns None if API fails or data is missing.
    """
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()  # Raise error for HTTP errors
        data = resp.json()
        print("Raw API response:", data)  # Debug: see what API returns
    except Exception as e:
        print("Error fetching stock data:", e)
        return None

    # Check if API returned valid current price
    if data.get("c") is None:
        print("API returned empty or invalid data")
        return None

    # Convert UNIX timestamp to datetime
    timestamp = pd.to_datetime(data.get("t"), unit='s') if data.get("t") else pd.Timestamp.now()

    return {
        "current_price": data.get("c"),
        "price_change": data.get("d"),
        "percent_change": data.get("dp"),
        "high_price": data.get("h"),
        "low_price": data.get("l"),
        "open_price": data.get("o"),
        "previous_close": data.get("pc"),
        "timestamp": timestamp
    }

def save_stock_price(data, symbol="AAPL"):
    """
    Save fetched stock price to PostgreSQL database using SQLAlchemy.
    """
    if data is None:
        print("No data to save.")
        return

    engine = get_engine()
    try:
        with engine.connect() as conn:
            stmt = insert(StockPrice).values(
                symbol=symbol,
                price=data["current_price"],
                price_change=data.get("price_change"),
                percent_change=data.get("percent_change"),
                high=data.get("high_price"),
                low=data.get("low_price"),
                open=data.get("open_price"),
                previous_close=data.get("previous_close"),
                timestamp=data["timestamp"]
            )
            conn.execute(stmt)
            conn.commit()
        print(f"Stock price saved successfully for {symbol}: {data}")
    except Exception as e:
        print("Error saving stock price to DB:", e)

if __name__ == "__main__":
    stock_data = fetch_stock_price()
    save_stock_price(stock_data)
