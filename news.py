# news.py
import requests
from sqlalchemy import insert
from db import get_engine
from models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime
from dotenv import load_dotenv
import os
from datetime import datetime
import unicodedata

load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")

# Define NewsArticles model if not added yet in models.py
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    title = Column(Text)
    description = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime)
    url = Column(Text)

# ----------------------------
# Helper function to clean text
# ----------------------------
def clean_text(text):
    """
    Normalize text to UTF-8 and remove problematic characters.
    """
    if text:
        # Normalize unicode characters
        text = unicodedata.normalize("NFKD", text)
        # Optional: Remove non-ASCII characters if needed
        text = text.encode("ascii", "ignore").decode()
        return text
    return text

# ----------------------------
# Fetch news from Finnhub API
# ----------------------------
def fetch_news(symbol="AAPL", limit=10):
    """
    Fetch latest news for a company from Finnhub API
    """
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2025-09-01&to=2025-09-20&token={API_KEY}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        print(f"Fetched {len(data)} news articles for {symbol}")
        return data[:limit]  # limit number of articles
    except Exception as e:
        print("Error fetching news:", e)
        return []

# ----------------------------
# Save news to PostgreSQL
# ----------------------------
def save_news(news_list, symbol="AAPL"):
    """
    Save news articles to PostgreSQL with cleaned text
    """
    if not news_list:
        print("No news to save.")
        return

    engine = get_engine()
    with engine.connect() as conn:
        for news in news_list:
            published_at = datetime.utcfromtimestamp(news.get("datetime")) if news.get("datetime") else None
            stmt = insert(NewsArticle).values(
                symbol=symbol,
                title=clean_text(news.get("headline")),
                description=clean_text(news.get("summary")),
                source=clean_text(news.get("source")),
                published_at=published_at,
                url=news.get("url")
            )
            conn.execute(stmt)
        conn.commit()
    print(f"Saved {len(news_list)} news articles to DB.")

# ----------------------------
# Main execution
# ----------------------------
if __name__ == "__main__":
    news_data = fetch_news()
    save_news(news_data)
