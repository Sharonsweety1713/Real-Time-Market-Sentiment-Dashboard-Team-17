from sqlalchemy.orm import sessionmaker
from db import get_engine
from models import StockPrice, SentimentAnalysis
from sqlalchemy import func

# Set up DB session
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

def fetch_latest_stock_sentiment(symbol="AAPL"):
    # Latest stock price
    latest_price = session.query(StockPrice).filter_by(symbol=symbol).order_by(StockPrice.timestamp.desc()).first()
    
    # Average sentiment for last 10 news articles
    avg_sentiment = session.query(func.avg(SentimentAnalysis.sentiment_score)).join(
        StockPrice, StockPrice.symbol == symbol
    ).join(
        SentimentAnalysis, SentimentAnalysis.news_id != None
    ).order_by(SentimentAnalysis.id.desc()).limit(10).scalar()
    
    return {
        "current_price": latest_price.price if latest_price else None,
        "average_sentiment": avg_sentiment if avg_sentiment else 0.5,
        "recent_news_count": 10
    }
