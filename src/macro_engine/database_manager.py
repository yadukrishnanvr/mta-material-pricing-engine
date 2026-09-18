import os
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

# Dynamic path resolution (Works on Windows, Linux, Docker, Render)
MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
DB_DIR = Path(os.environ.get("DATA_DIR", MODULE_DIR))
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "mta_market_live.db"
CACHE_PATH = DB_DIR / "dynamic_market_cache.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")  # Critical for multi-threaded concurrency
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_live_db():
    logging.info(f"[DATABASE] Initializing database at: {DB_PATH}")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_market_cache (
            state TEXT NOT NULL,
            commodity TEXT NOT NULL,
            brand TEXT NOT NULL,
            tier TEXT NOT NULL,
            standard TEXT NOT NULL,
            spot_base_inr REAL NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            scraped_at TIMESTAMP NOT NULL,
            notes TEXT,
            PRIMARY KEY (state, commodity, brand)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS material_price_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT NOT NULL,
            commodity TEXT NOT NULL,
            brand TEXT NOT NULL,
            tier TEXT NOT NULL,
            standard TEXT NOT NULL,
            raw_price REAL NOT NULL,
            raw_unit TEXT NOT NULL,
            normalized_price_inr REAL NOT NULL,
            statutory_sor_inr REAL NOT NULL,
            spread_delta_inr REAL NOT NULL,
            spread_delta_pct REAL NOT NULL,
            source_name TEXT NOT NULL,
            scraped_at TIMESTAMP NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fuel_drift_ledger (
            state TEXT PRIMARY KEY,
            diesel_inr_per_ltr REAL NOT NULL,
            drift_factor REAL NOT NULL,
            scraped_at TIMESTAMP NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS statutory_document_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_extension TEXT NOT NULL,
            file_size_kb REAL NOT NULL,
            jurisdiction TEXT NOT NULL,
            document_type TEXT NOT NULL,
            target_commodity TEXT NOT NULL,
            quarry_royalty_seigniorage_inr REAL,
            base_conveyance_first_km_inr REAL,
            subsequent_km_rate_inr REAL,
            density_compaction_factor REAL,
            escalation_clause_ref TEXT,
            parsed_metadata_json TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logging.info("[DATABASE] Database initialization verified.")

def save_scraped_rate(state, commodity, brand, tier, standard, spot_base_inr, 
                      source_name, source_url, statutory_sor, raw_price, raw_unit, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    now_iso = datetime.now().isoformat()

    cur.execute("""
        INSERT INTO live_market_cache (
            state, commodity, brand, tier, standard, spot_base_inr, 
            source_name, source_url, scraped_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(state, commodity, brand) DO UPDATE SET
            spot_base_inr = excluded.spot_base_inr,
            tier = excluded.tier,
            standard = excluded.standard,
            source_name = excluded.source_name,
            source_url = excluded.source_url,
            scraped_at = excluded.scraped_at,
            notes = excluded.notes
    """, (state, commodity, brand, tier, standard, spot_base_inr, source_name, source_url, now_iso, notes))

    delta_inr = round(spot_base_inr - statutory_sor, 2)
    delta_pct = round((delta_inr / statutory_sor) * 100.0, 2) if statutory_sor > 0 else 0.0

    cur.execute("""
        INSERT INTO material_price_audit_log (
            state, commodity, brand, tier, standard, raw_price, raw_unit,
            normalized_price_inr, statutory_sor_inr, spread_delta_inr, spread_delta_pct,
            source_name, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (state, commodity, brand, tier, standard, raw_price, raw_unit,
          spot_base_inr, statutory_sor, delta_inr, delta_pct, source_name, now_iso))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_live_db()
