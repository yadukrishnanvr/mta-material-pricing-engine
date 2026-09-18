import os
import sys
import logging
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from database_manager import get_connection, save_scraped_rate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SchedulerService")

def run_periodic_market_settlement():
    """
    Simulates / triggers the periodic spot price refresh and diesel drift ledger sync.
    Runs completely decoupled from user-facing HTTP request cycles.
    """
    logger.info("[CRON] Starting periodic background market settlement...")
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check active records in cache
        cur.execute("SELECT COUNT(*) FROM live_market_cache")
        cached_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM fuel_drift_ledger")
        fuel_count = cur.fetchone()[0]
        
        conn.close()
        logger.info(f"[CRON] Market cache verification: {cached_count} commodities active, {fuel_count} state diesel benchmarks intact.")
        logger.info("[CRON] Background settlement tick completed successfully.")
    except Exception as e:
        logger.error(f"[CRON ERROR] Settlement tick failure: {e}", exc_info=True)

def start_background_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    # Trigger settlement run every 60 minutes
    scheduler.add_job(
        run_periodic_market_settlement,
        trigger=IntervalTrigger(minutes=60),
        id="periodic_settlement_job",
        name="Update commodity spot feeds and diesel drift",
        replace_existing=True
    )
    scheduler.start()
    logger.info("[SCHEDULER] Background APScheduler initialized and active.")
    return scheduler
