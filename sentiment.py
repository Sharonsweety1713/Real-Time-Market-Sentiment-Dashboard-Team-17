# sentiment.py
from db import get_engine
from models import NewsArticle, SentimentAnalysis, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Download VADER lexicon
nltk.download('vader_lexicon')

# Set up DB session
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Initialize VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

def calculate_sentiment(text):
    if not text:
        return 0.5, 3  # neutral if text empty
    score = sia.polarity_scores(text)['compound']  # -1 to 1
    # Normalize to 0–1
    normalized_score = (score + 1) / 2
    # Map to 1–5 scale
    rating = round(normalized_score * 4 + 1)
    return normalized_score, rating

def analyze_news_sentiment():
    # Fetch news without sentiment yet
    news_list = session.query(NewsArticle).all()
    for news in news_list:
        score, rating = calculate_sentiment(news.title + " " + (news.description or ""))
        sentiment = SentimentAnalysis(
            news_id=news.id,
            sentiment_score=score,
            sentiment_rating=rating
        )
        session.add(sentiment)
    session.commit()
    print(f"Sentiment analysis completed for {len(news_list)} articles.")

if __name__ == "__main__":
    analyze_news_sentiment()




# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# import torch

# # Load FinBERT model
# model_name = "ProsusAI/finbert"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)

# # Define labels
# labels = ["negative", "neutral", "positive"]

# def finbert_sentiment(text):
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
#     with torch.no_grad():
#         outputs = model(**inputs)
#         scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
#         predicted_class = scores.argmax().item()
#     return labels[predicted_class], scores.tolist()[0]
