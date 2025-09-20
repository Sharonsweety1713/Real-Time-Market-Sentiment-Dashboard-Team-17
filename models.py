from sqlalchemy import Column, Integer, Float, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json
from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockSentimentRecommendation(Base):
    __tablename__ = "stock_sentiment_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    stock_price = Column(Float, nullable=False)
    average_sentiment = Column(Float, nullable=False)
    

    recommendation = Column(Text, nullable=False)

    headlines = Column(Text)  # store JSON string of headlines

    def set_headlines(self, headlines_list):
        self.headlines = json.dumps(headlines_list)

    def get_headlines(self):
        return json.loads(self.headlines) if self.headlines else []

class StockPrice(Base):
    __tablename__ = "stock_price"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10))
    price = Column(Float)
    price_change = Column(Float)    # Added: price change from previous close
    percent_change = Column(Float)  # Added: percentage change from previous close
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    previous_close = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    title = Column(Text)
    description = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime)
    url = Column(Text)  # store article link

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey("news_articles.id"))
    sentiment_score = Column(Float)   # 0 = negative, 1 = positive
    sentiment_rating = Column(Integer)  # 1 to 5
    news = relationship("NewsArticle", backref="sentiments")
    
class NewsSourceDistribution(Base):
    __tablename__ = "news_source_distribution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))
    count = Column(Integer)
    percentage = Column(Float)