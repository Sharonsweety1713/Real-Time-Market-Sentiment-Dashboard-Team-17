from db import get_engine
from sqlalchemy.orm import sessionmaker
from models import StockPrice, NewsArticle, StockSentimentRecommendation
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# ---------- Load FinBERT ----------
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
finbert = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# ---------- DB session ----------
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

def generate_finbert_recommendation(news_count=5):
    # ---------- Latest stock price ----------
    latest_price = session.query(StockPrice).order_by(StockPrice.timestamp.desc()).first()
    if not latest_price:
        return {"error": "No stock price data available"}

    # ---------- Latest news ----------
    recent_news = (
        session.query(NewsArticle)
        .order_by(NewsArticle.published_at.desc())
        .limit(news_count)
        .all()
    )
    if not recent_news:
        return {"error": "No news articles available"}

    # ---------- Sentiment analysis ----------
    sentiments = []
    headlines_with_sentiment = []

    for i, news in enumerate(recent_news, start=1):
        text = news.title + (" " + news.description if news.description else "")
        result = finbert(text)[0]

        label = result['label'].lower()
        if label == "positive":
            score = result["score"]
        elif label == "negative":
            score = -result["score"]
        else:
            score = 0
        sentiments.append(score)

        headlines_with_sentiment.append(
            f"{i}. {news.title}"
            + (f" - {news.description}" if news.description else "")
            + f" => Sentiment: {result['label']} ({result['score']:.2f})"
        )

    avg_sentiment = sum(sentiments) / len(sentiments)

    # ---------- Recommendation ----------
    if avg_sentiment > 0.3:
        recommendation = "BUY 📈 (Positive market sentiment)"
    elif avg_sentiment < -0.3:
        recommendation = "SELL 📉 (Negative market sentiment)"
    else:
        recommendation = "HOLD 🤝 (Unclear market sentiment)"

    # ---------- Store in DB ----------
    record = StockSentimentRecommendation(
        stock_price=latest_price.price,
        average_sentiment=round(avg_sentiment, 2),
        recommendation=recommendation
    )
    record.set_headlines(headlines_with_sentiment)
    session.add(record)
    session.commit()

    return {
        "price": latest_price.price,
        "avg_sentiment": round(avg_sentiment, 2),
        "recommendation": recommendation,
        "headlines": headlines_with_sentiment
    }

if __name__ == "__main__":
    result = generate_finbert_recommendation()
    print(f"Current Price: {result['price']}")
    print(f"Average Sentiment: {result['avg_sentiment']}")
    print("Headlines & Sentiments:")
    for h in result['headlines']:
        print(h)
    print(f"\nRECOMMENDATION: {result['recommendation']}")
