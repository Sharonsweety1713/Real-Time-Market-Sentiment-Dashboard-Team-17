from db import get_engine
from sqlalchemy.orm import sessionmaker
from models import NewsArticle, NewsSourceDistribution
from sqlalchemy import func
from datetime import datetime

engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

def update_news_source_distribution():
    results = (session.query(NewsArticle.source, func.count(NewsArticle.id))
               .group_by(NewsArticle.source)
               .all())
    total = sum(count for _, count in results)

    # Optional: Clear old records to keep only current snapshot
    session.query(NewsSourceDistribution).delete()

    for source, count in results:
        percentage = (count / total) * 100 if total > 0 else 0
        record = NewsSourceDistribution(
            timestamp=datetime.utcnow(),
            source=source,
            count=count,
            percentage=percentage
        )
        session.add(record)
    session.commit()
    print("News source distribution updated in DB.")

if __name__ == "__main__":
    update_news_source_distribution()
