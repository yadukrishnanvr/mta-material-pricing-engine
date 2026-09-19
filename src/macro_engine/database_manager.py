import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
DB_DIR = Path(os.environ.get("DATA_DIR", MODULE_DIR))
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "mta_market_live.db"
CACHE_PATH = DB_DIR / "dynamic_market_cache.json"

DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatabaseManager")

class DBConnectionWrapper:
    """
    Wraps SQLite or PostgreSQL connections and normalizes '?' placeholders to '%s'
    so all SQL queries remain cross-compatible across both engines.
    """
    def __init__(self, raw_conn, is_postgres=False):
        self.conn = raw_conn
        self.is_postgres = is_postgres

    def cursor(self):
        raw_cur = self.conn.cursor()
        return DBCursorWrapper(raw_cur, self.is_postgres)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

class DBCursorWrapper:
    def __init__(self, raw_cur, is_postgres=False):
        self.cur = raw_cur
        self.is_postgres = is_postgres

    def execute(self, sql, params=None):
        query = sql
        if self.is_postgres:
            query = query.replace("?", "%s")
        if params is not None:
            return self.cur.execute(query, params)
        return self.cur.execute(query)

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    def close(self):
        self.cur.close()

def get_connection():
    if IS_POSTGRES:
        import psycopg2
        # Render provides postgres:// which psycopg2 accepts
        conn = psycopg2.connect(DATABASE_URL)
        return DBConnectionWrapper(conn, is_postgres=True)
    else:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return DBConnectionWrapper(conn, is_postgres=False)

def init_live_db():
    conn = get_connection()
    ensure_schema_compatibility(conn)
    conn.close()
    if IS_POSTGRES:
        logger.info("[DATABASE] Connecting to Production PostgreSQL instance...")
    else:
        logger.info(f"[DATABASE] Initializing SQLite local fallback at: {DB_PATH}")

    conn = get_connection()
    cur = conn.cursor()

    if IS_POSTGRES:
        # PostgreSQL DDL
        cur.execute("""
            CREATE TABLE IF NOT EXISTS live_market_cache (
                state VARCHAR(64) NOT NULL,
                commodity VARCHAR(64) NOT NULL,
                brand VARCHAR(128) NOT NULL,
                tier VARCHAR(64) NOT NULL,
                standard VARCHAR(128) NOT NULL,
                spot_base_inr DOUBLE PRECISION NOT NULL,
                source_name VARCHAR(128) NOT NULL,
                source_url TEXT NOT NULL,
                scraped_at TIMESTAMP NOT NULL,
                notes TEXT,
                PRIMARY KEY (state, commodity, brand)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS material_price_audit_log (
                id SERIAL PRIMARY KEY,
                state VARCHAR(64) NOT NULL,
                commodity VARCHAR(64) NOT NULL,
                brand VARCHAR(128) NOT NULL,
                tier VARCHAR(64) NOT NULL,
                standard VARCHAR(128) NOT NULL,
                raw_price DOUBLE PRECISION NOT NULL,
                raw_unit VARCHAR(32) NOT NULL,
                normalized_price_inr DOUBLE PRECISION NOT NULL,
                statutory_sor_inr DOUBLE PRECISION NOT NULL,
                spread_delta_inr DOUBLE PRECISION NOT NULL,
                spread_delta_pct DOUBLE PRECISION NOT NULL,
                source_name VARCHAR(128) NOT NULL,
                scraped_at TIMESTAMP NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fuel_drift_ledger (
                state VARCHAR(64) PRIMARY KEY,
                diesel_inr_per_ltr DOUBLE PRECISION NOT NULL,
                drift_factor DOUBLE PRECISION NOT NULL,
                scraped_at TIMESTAMP NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS statutory_document_inventory (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_extension VARCHAR(16) NOT NULL,
                file_size_kb DOUBLE PRECISION NOT NULL,
                jurisdiction VARCHAR(64) NOT NULL,
                document_type VARCHAR(128) NOT NULL,
                target_commodity VARCHAR(64) NOT NULL,
                quarry_royalty_seigniorage_inr DOUBLE PRECISION,
                base_conveyance_first_km_inr DOUBLE PRECISION,
                subsequent_km_rate_inr DOUBLE PRECISION,
                density_compaction_factor DOUBLE PRECISION,
                escalation_clause_ref VARCHAR(128),
                parsed_metadata_json TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        # SQLite DDL
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
    logger.info("[DATABASE] Database initialization and schema verified.")

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


def ensure_schema_compatibility(conn):
    try:
        cur = conn.cursor()
        # Check SQLite table columns
        cur.execute("PRAGMA table_info(live_market_cache);")
        cols = [r[1] for r in cur.fetchall()]
        if cols and "notes" not in cols:
            cur.execute("ALTER TABLE live_market_cache ADD COLUMN notes TEXT;")
            conn.commit()
    except Exception:
        pass
