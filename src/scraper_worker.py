import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from macro_engine.live_market_scraper import LiveMarketScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WORKER] %(message)s")

def run_job():
    logging.info("Triggering scheduled market scrape...")
    try:
        scraper = LiveMarketScraper()
        scraper.execute_pipeline()
        logging.info("Market scrape complete. Dynamic cache refreshed.")
    except Exception as e:
        logging.error(f"Scraper execution error: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Run once immediately on start
    run_job()
    # Schedule every 6 hours
    scheduler.add_job(run_job, "interval", hours=6)
    logging.info("Scheduler online. Running every 6 hours. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
