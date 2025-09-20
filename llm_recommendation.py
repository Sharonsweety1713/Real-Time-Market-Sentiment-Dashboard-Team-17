# from db import get_engine
# from sqlalchemy.orm import sessionmaker
# from models import StockPrice, NewsArticle, StockSentimentRecommendation
# from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# # ---------- Load FinBERT ----------
# model_name = "ProsusAI/finbert"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)
# finbert = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# # ---------- DB session ----------
# engine = get_engine()
# Session = sessionmaker(bind=engine)
# session = Session()

# def generate_finbert_recommendation(news_count=5):
#     # ---------- Latest stock price ----------
#     latest_price = session.query(StockPrice).order_by(StockPrice.timestamp.desc()).first()
#     if not latest_price:
#         return {"error": "No stock price data available"}

#     # ---------- Latest news ----------
#     recent_news = (
#         session.query(NewsArticle)
#         .order_by(NewsArticle.published_at.desc())
#         .limit(news_count)
#         .all()
#     )
#     if not recent_news:
#         return {"error": "No news articles available"}

#     # ---------- Sentiment analysis ----------
#     sentiments = []
#     headlines_with_sentiment = []

#     for i, news in enumerate(recent_news, start=1):
#         text = news.title + (" " + news.description if news.description else "")
#         result = finbert(text)[0]

#         label = result['label'].lower()
#         if label == "positive":
#             score = result["score"]
#         elif label == "negative":
#             score = -result["score"]
#         else:
#             score = 0
#         sentiments.append(score)

#         headlines_with_sentiment.append(
#             f"{i}. {news.title}"
#             + (f" - {news.description}" if news.description else "")
#             + f" => Sentiment: {result['label']} ({result['score']:.2f})"
#         )

#     avg_sentiment = sum(sentiments) / len(sentiments)

#     # ---------- Recommendation ----------
#     if avg_sentiment > 0.3:
#         recommendation = "BUY 📈 (Positive market sentiment)"
#     elif avg_sentiment < -0.3:
#         recommendation = "SELL 📉 (Negative market sentiment)"
#     else:
#         recommendation = "HOLD 🤝 (Unclear market sentiment)"

#     # ---------- Store in DB ----------
#     record = StockSentimentRecommendation(
#         stock_price=latest_price.price,
#         average_sentiment=round(avg_sentiment, 2),
#         recommendation=recommendation
#     )
#     record.set_headlines(headlines_with_sentiment)
#     session.add(record)
#     session.commit()

#     return {
#         "price": latest_price.price,
#         "avg_sentiment": round(avg_sentiment, 2),
#         "recommendation": recommendation,
#         "headlines": headlines_with_sentiment
#     }

# if __name__ == "__main__":
#     result = generate_finbert_recommendation()
#     print(f"Current Price: {result['price']}")
#     print(f"Average Sentiment: {result['avg_sentiment']}")
#     print("Headlines & Sentiments:")
#     for h in result['headlines']:
#         print(h)
#     print(f"\nRECOMMENDATION: {result['recommendation']}")






import os
from google import genai
from db import get_engine
from sqlalchemy.orm import sessionmaker
from models import StockPrice, NewsArticle, SentimentAnalysis, StockSentimentRecommendation
from datetime import datetime
import json


# Initialize Gemini client with API key from env
API_KEY = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=API_KEY)


# Setup DB session
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()


def prepare_prompt(stock_symbol="AAPL", news_count=5):
    # Fetch latest stock price
    latest_price = session.query(StockPrice).order_by(StockPrice.timestamp.desc()).first()
    if not latest_price:
        return None, None, None, "No stock price data available"

    # Fetch recent news and sentiments
    news_items = (session.query(NewsArticle)
                  .order_by(NewsArticle.published_at.desc())
                  .limit(news_count)
                  .all())
    if not news_items:
        return None, None, None, "No recent news articles available"

    headlines = []
    sentiments = []
    for news in news_items:
        headlines.append(news.title)
        sentiment = session.query(SentimentAnalysis).filter(SentimentAnalysis.news_id == news.id).first()
        if sentiment:
            sentiments.append(sentiment.sentiment_score)
        else:
            sentiments.append(0.5)  # Neutral default

    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5

    # Build prompt string for Gemini
    prompt = f"""
You are a professional financial advisor. Based on the stock data and recent news below, provide a clear recommendation to BUY, SELL, or HOLD {stock_symbol} and explain why simply.

Stock: {stock_symbol}
Current Price: {latest_price.price}
Average Sentiment Score (0 to 1): {avg_sentiment:.2f}

Recent News Headlines:
"""
    prompt += "\n".join([f"- {h}" for h in headlines])
    prompt += "\nProvide your recommendation and reasoning."

    return prompt, avg_sentiment, headlines, None


def get_gemini_recommendation(prompt):
    # Call Gemini API
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


def save_recommendation_to_db(stock_price, avg_sentiment, recommendation_text, headlines):
    # Create record and commit to DB
    record = StockSentimentRecommendation(
        timestamp=datetime.utcnow(),
        stock_price=stock_price,
        average_sentiment=avg_sentiment,
        recommendation=recommendation_text,
    )
    record.set_headlines(headlines)
    session.add(record)
    session.commit()
    print("Recommendation saved to database.")


if __name__ == "__main__":
    prompt, avg_sentiment, headlines, error = prepare_prompt()
    if error:
        print("Error:", error)
    else:
        recommendation = get_gemini_recommendation(prompt)
        print("Gemini Recommendation:\n", recommendation)
        # Save recommendation to DB
        latest_price = session.query(StockPrice).order_by(StockPrice.timestamp.desc()).first()
        save_recommendation_to_db(latest_price.price, avg_sentiment, recommendation, headlines)
