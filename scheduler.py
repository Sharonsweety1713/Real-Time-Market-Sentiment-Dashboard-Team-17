# scheduler.py
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from stock import fetch_stock_price, save_stock_price
from sentiment import analyze_news_sentiment  # Only use existing function

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def scheduled_tasks():
    logging.info("Running scheduled tasks...")

    # Fetch latest stock price (example for AAPL, modify symbol if needed)
    stock_data = fetch_stock_price("AAPL")
    save_stock_price(stock_data)
    logging.info(f"Stock price updated: {stock_data}")

    # Run sentiment analysis on latest news
    analyze_news_sentiment()
    logging.info("Sentiment analysis completed.")

    logging.info("Scheduled tasks completed.")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # Schedule every 30 minutes
    scheduler.add_job(scheduled_tasks, 'interval', seconds=10)
    scheduler.start()
    logging.info("Scheduler started. Press Ctrl+C to exit.")

    # Keep script running
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler stopped.")
