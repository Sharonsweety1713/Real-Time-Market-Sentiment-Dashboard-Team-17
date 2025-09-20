# main.py
from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker
from db import get_engine
from models import StockPrice, NewsArticle, SentimentAnalysis, StockSentimentRecommendation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Apple Market Sentiment Dashboard")

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB session
engine = get_engine()
Session = sessionmaker(bind=engine)

# --------- Endpoints ---------
@app.get("/latest-stock")
def latest_stock():
    session = Session()
    stock = session.query(StockPrice).order_by(StockPrice.timestamp.desc()).first()
    session.close()
    if stock:
        return {
            "symbol": stock.symbol,
            "price": stock.price,
            "high": stock.high,
            "low": stock.low,
            "open": stock.open,
            "previous_close": stock.previous_close,
            "timestamp": stock.timestamp
        }
    return {"error": "No stock price found"}

@app.get("/latest-news")
def latest_news(limit: int = 5):
    session = Session()
    news = session.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit).all()
    session.close()
    result = []
    for n in news:
        result.append({
            "title": n.title,
            "description": n.description,
            "source": n.source,
            "published_at": n.published_at,
            "url": n.url
        })
    return result

@app.get("/latest-sentiment")
def latest_sentiment(limit: int = 5):
    session = Session()
    sentiment = (
        session.query(SentimentAnalysis)
        .join(NewsArticle)
        .order_by(SentimentAnalysis.id.desc())
        .limit(limit)
        .all()
    )
    session.close()
    result = []
    for s in sentiment:
        result.append({
            "news_id": s.news_id,
            "headline": s.news.title,
            "sentiment_score": s.sentiment_score,
            "sentiment_rating": s.sentiment_rating
        })
    return result

@app.get("/recommendation")
def recommendation():
    session = Session()
    rec = session.query(StockSentimentRecommendation).order_by(StockSentimentRecommendation.timestamp.desc()).first()
    session.close()
    if rec:
        return {
            "stock_price": rec.stock_price,
            "average_sentiment": rec.average_sentiment,
            "recommendation": rec.recommendation,
            "headlines": rec.get_headlines()
        }
    return {"error": "No recommendation found"}
