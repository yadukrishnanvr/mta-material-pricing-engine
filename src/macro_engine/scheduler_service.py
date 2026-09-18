import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from macro_engine.database_manager import get_connection, save_scraped_rate
from macro_engine.bourse_scrapers import (
    fetch_live_diesel_drift,
    fetch_steel_spot_feeds,
    fetch_cement_spot_feeds
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SchedulerService")

scheduler = BackgroundScheduler()

def run_periodic_market_settlement():
    """
    Executes automated settlement:
    1. Scrapes latest OMC Diesel retail drift benchmarks.
    2. Collects TMT Mandi ex-plant indices and Cement wholesale feeds.
    3. Normalizes units to metric standard (INR/MT or INR/Ltr).
    4. Computes statutory SoR spread deltas and logs permanent audit ticks in Supabase PostgreSQL.
    """
    logger.info("[CRON] Executing scheduled multi-bourse market settlement cycle...")
    conn = None
    try:
        # 1. Update State Fuel Drift Ledger
        diesel_records = fetch_live_diesel_drift()
        conn = get_connection()
        cur = conn.cursor()
        for d in diesel_records:
            cur.execute("""
                INSERT INTO fuel_drift_ledger (state, diesel_inr_per_ltr, drift_factor, scraped_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (state) DO UPDATE SET
                    diesel_inr_per_ltr = excluded.diesel_inr_per_ltr,
                    drift_factor = excluded.drift_factor,
                    scraped_at = excluded.scraped_at
            """, (d["state"], d["diesel_inr_per_ltr"], d["drift_factor"], d["scraped_at"]))
        conn.commit()
        logger.info(f"[CRON] Successfully synchronized {len(diesel_records)} state diesel benchmarks.")

        # 2. Update Steel Feeds
        steel_records = fetch_steel_spot_feeds()
        for s in steel_records:
            save_scraped_rate(
                state=s["state"],
                commodity=s["commodity"],
                brand=s["brand"],
                tier=s["tier"],
                standard=s["standard"],
                spot_base_inr=s["spot_base_inr"],
                source_name=s["source_name"],
                source_url=s["source_url"],
                statutory_sor=s["statutory_sor"],
                raw_price=s["raw_price"],
                raw_unit=s["raw_unit"],
                notes=s["notes"]
            )
        logger.info(f"[CRON] Processed {len(steel_records)} live steel Mandi spot quotes.")

        # 3. Update Cement Feeds
        cement_records = fetch_cement_spot_feeds()
        for c in cement_records:
            save_scraped_rate(
                state=c["state"],
                commodity=c["commodity"],
                brand=c["brand"],
                tier=c["tier"],
                standard=c["standard"],
                spot_base_inr=c["spot_base_inr"],
                source_name=c["source_name"],
                source_url=c["source_url"],
                statutory_sor=c["statutory_sor"],
                raw_price=c["raw_price"],
                raw_unit=c["raw_unit"],
                notes=c["notes"]
            )
        logger.info(f"[CRON] Processed {len(cement_records)} live cement wholesale quotes.")
        logger.info("[CRON] Settlement cycle finished with zero errors. All audits committed to PostgreSQL.")

    except Exception as e:
        logger.error(f"[CRON ERROR] Settlement cycle encountered an exception: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def start_background_scheduler():
    """Starts the APScheduler instance for periodic market settlement."""
    if not scheduler.running:
        scheduler.add_job(
            func=run_periodic_market_settlement,
            trigger=IntervalTrigger(minutes=60),
            id="multi_bourse_settlement",
            name="Update commodity spot feeds and diesel drift",
            replace_existing=True
        )
        scheduler.start()
        logger.info("[SCHEDULER] Background APScheduler initialized and running on 60-min cadence.")

# Alias for backward compatibility
init_scheduler = start_background_scheduler
