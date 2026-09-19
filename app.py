import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
MACRO_DIR = SRC_DIR / "macro_engine"
INDEX_HTML = ROOT_DIR / "templates" / "index.html"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(MACRO_DIR) not in sys.path:
    sys.path.insert(0, str(MACRO_DIR))

from macro_engine.national_pricing_engine import NationalMaterialPricingEngine
from macro_engine.database_manager import init_live_db, get_connection, DB_PATH
from macro_engine.city_tier_registry import get_cities_for_state
from macro_engine.escalation_engine import Clause10CAEscalationEngine
from macro_engine.scheduler_service import start_background_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_live_db()
    scheduler = start_background_scheduler()
    yield
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)

app = FastAPI(title="Pan-India MTA Multi-Attribute Engine", version="2.6.0", lifespan=lifespan)
engine = NationalMaterialPricingEngine(base_dir=ROOT_DIR)
escalation_engine = Clause10CAEscalationEngine(str(DB_PATH))

class MultiQuoteRequest(BaseModel):
    state: str
    city: Optional[str] = None
    commodity: str
    tier: Optional[str] = "Tier-1"
    grade: Optional[str] = "Fe500D"
    lead_km: float = 25.0
    diameter_mm: Optional[float] = None
    quarry_distance_km: Optional[float] = None
    source_type: Optional[str] = None

class EscalationRequest(BaseModel):
    state: str
    commodity: str
    base_date: str
    current_date: str
    contract_value: float
    material_weight: Optional[float] = None

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=FileResponse)
def serve_index():
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    return HTMLResponse("<h1>MTA Pricing Engine Live (templates/index.html missing)</h1>")

@app.get("/api/admin/db-status")
def get_db_status():
    has_url = bool(os.environ.get("DATABASE_URL"))
    conn = get_connection()
    cur = conn.cursor()
    if has_url:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [r[0] for r in cur.fetchall()]
        counts = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t};")
            counts[t] = cur.fetchone()[0]
        db_type = "PostgreSQL"
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        counts = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t};")
            counts[t] = cur.fetchone()[0]
        db_type = "SQLite"
    conn.close()
    return {
        "status": "connected",
        "active_database": db_type,
        "has_database_url": has_url,
        "tables_found": tables,
        "row_counts": counts
    }

@app.get("/api/admin/trigger-settlement")
def trigger_settlement_now():
    from macro_engine.scheduler_service import run_periodic_market_settlement
    try:
        run_periodic_market_settlement()
        return {"status": "success", "message": "Immediate multi-bourse settlement executed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/states")
def get_states_list():
    from macro_engine.city_tier_registry import CITY_TIER_DATABASE
    states = sorted([k for k in CITY_TIER_DATABASE.keys() if k != "DEFAULT"])
    return {"states": states}

@app.get("/api/cities")
def get_cities(state: str):
    raw_cities = get_cities_for_state(state)
    if isinstance(raw_cities, dict):
        city_names = list(raw_cities.keys())
        profiles = raw_cities
    elif isinstance(raw_cities, list):
        city_names = raw_cities
        profiles = {c: {"tier": "Tier-2", "tier_multiplier": 1.0} for c in raw_cities}
    else:
        city_names = [f"{state} Central"]
        profiles = {city_names[0]: {"tier": "Tier-2", "tier_multiplier": 1.0}}

    return {
        "state": state,
        "cities": city_names,
        "profiles": profiles
    }


@app.post("/api/quote")
def calculate_quote(req: MultiQuoteRequest):
    try:
        # 1. Normalize commodity
        raw_comm = (req.commodity or "steel").lower()
        if "steel" in raw_comm:
            commodity = "steel"
        elif "cement" in raw_comm:
            commodity = "cement"
        elif "sand" in raw_comm:
            commodity = "sand"
        elif "agg" in raw_comm:
            commodity = "aggregates"
        else:
            commodity = raw_comm

        # 2. Normalize grade
        raw_grade = (req.grade or "").lower().replace(" ", "_").replace("-", "_")
        if "550" in raw_grade:
            grade = "fe550d"
        elif "500" in raw_grade:
            grade = "fe500d"
        elif "opc" in raw_grade:
            grade = "opc_53"
        elif "ppc" in raw_grade:
            grade = "ppc"
        elif "psc" in raw_grade:
            grade = "psc"
        elif "20" in raw_grade:
            grade = "20mm"
        elif "40" in raw_grade:
            grade = "40mm"
        elif "zone" in raw_grade or "m_sand" in raw_grade or "msand" in raw_grade:
            grade = "m_sand"
        else:
            grade = req.grade or "fe550d"

        quote = engine.calculate_multi_attribute_quote(
            state=req.state,
            city=req.city,
            commodity=commodity,
            tier=req.tier or "Tier-1",
            grade=grade,
            lead_km=req.lead_km or 25.0,
            diameter_mm=req.diameter_mm,
            quarry_distance_km=req.quarry_distance_km,
            source_type=req.source_type
        )
        return quote
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/escalation")
def calculate_escalation(req: EscalationRequest):
    try:
        res = escalation_engine.calculate_escalation(
            state=req.state,
            commodity=req.commodity,
            base_date=req.base_date,
            current_date=req.current_date,
            contract_value=req.contract_value,
            material_weight=req.material_weight
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- PHASE 1: CONSUMER & HOUSE BUILDER ENDPOINTS ---
@app.get("/api/market/snapshot")
def get_market_snapshot(state: str = "Kerala"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT commodity, brand, spot_base_inr, standard 
        FROM live_market_cache 
        WHERE state = ?
    """, (state,))
    rows = cur.fetchall()
    conn.close()

    price_map = {r[0]: (r[1], float(r[2]), r[3]) for r in rows}
    items = []

    # 1. Steel: MT -> kg
    if "Steel" in price_map:
        brand, per_mt, std = price_map["Steel"]
        items.append({
            "id": "steel",
            "name": "TMT Rebar (Fe 550D)",
            "brand": brand,
            "unit": "₹ / kg",
            "price": round(per_mt / 1000.0, 2),
            "metric_price": per_mt,
            "signal": "BUY",
            "signal_label": "🟢 Value Zone (Buy Now)",
            "standard": std
        })
    else:
        items.append({
            "id": "steel",
            "name": "TMT Rebar (Fe 550D)",
            "brand": "Tata Tiscon Fe550D",
            "unit": "₹ / kg",
            "price": 54.5,
            "metric_price": 54500.0,
            "signal": "BUY",
            "signal_label": "🟢 Value Zone (Buy Now)",
            "standard": "IS 1786:2008"
        })

    # 2. Cement: MT -> 50kg bag (20 bags/MT)
    if "Cement" in price_map:
        brand, per_mt, std = price_map["Cement"]
        items.append({
            "id": "cement",
            "name": "Structural Cement",
            "brand": brand,
            "unit": "₹ / 50kg bag",
            "price": round(per_mt / 20.0, 2),
            "metric_price": per_mt,
            "signal": "NEUTRAL",
            "signal_label": "🟡 Stable (Procure Normal)",
            "standard": std
        })
    else:
        items.append({
            "id": "cement",
            "name": "Structural Cement",
            "brand": "UltraTech OPC 53",
            "unit": "₹ / 50kg bag",
            "price": 420.0,
            "metric_price": 8400.0,
            "signal": "NEUTRAL",
            "signal_label": "🟡 Stable",
            "standard": "IS 269:2015"
        })

    # 3. M-Sand
    items.append({
        "id": "msand",
        "name": "M-Sand (Concrete / Plastering)",
        "brand": "IS 383 Zone II Crushed",
        "unit": "₹ / cu.ft",
        "price": 54.0 if state == "Kerala" else 46.0,
        "signal": "BUY",
        "signal_label": "🟢 Steady",
        "standard": "IS 383:2016"
    })

    # 4. 20mm Aggregates
    items.append({
        "id": "aggregate",
        "name": "20mm Granite Aggregates",
        "brand": "Machine Crushed Blue Metal",
        "unit": "₹ / cu.ft",
        "price": 48.0 if state == "Kerala" else 42.0,
        "signal": "BUY",
        "signal_label": "🟢 Favorable",
        "standard": "IS 383:2016"
    })

    return {"state": state, "items": items}

@app.get("/api/market/trend-indicator")
def get_trend_indicator(state: str = "Kerala", commodity: str = "Steel"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT scraped_at, normalized_price_inr, statutory_sor_inr, spread_delta_pct 
        FROM material_price_audit_log 
        WHERE state = ? AND commodity = ?
        ORDER BY scraped_at ASC
        LIMIT 60
    """, (state, commodity))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        base = 54000.0 if commodity == "Steel" else 8200.0
        return {
            "state": state,
            "commodity": commodity,
            "labels": ["2026-03-01", "2026-03-05", "2026-03-10", "2026-03-15", "2026-03-18"],
            "spot_prices": [base, base + 200, base - 350, base - 100, base + 50],
            "statutory_sor": [round(base * 0.96, 2)] * 5,
            "latest_spread_pct": 2.1,
            "recommendation": "BUY",
            "recommendation_text": "🟢 Favorable Price Dip — Good Window to Lock Structural Materials"
        }

    dates = [r[0][:10] if r[0] else "" for r in rows]
    spot = [round(float(r[1]), 2) for r in rows]
    sor = [round(float(r[2]), 2) for r in rows]
    latest_spread = float(rows[-1][3]) if rows[-1][3] is not None else 0.0

    if latest_spread < -2.0:
        indicator = "BUY"
        status_text = "🟢 Favorable Price Dip — Good Window to Lock Slab/Footing Steel"
    elif latest_spread > 4.5:
        indicator = "WAIT"
        status_text = "🔴 Overheating — High Dealer Markups. Delay Large Deliveries by 1-2 Weeks"
    else:
        indicator = "NEUTRAL"
        status_text = "🟡 Fair Valuation — Procure in Batches Based on Site Schedule"

    return {
        "state": state,
        "commodity": commodity,
        "labels": dates,
        "spot_prices": spot,
        "statutory_sor": sor,
        "latest_spread_pct": round(latest_spread, 2),
        "recommendation": indicator,
        "recommendation_text": status_text
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    print(f"\n🚀 Server running at http://{host}:{port}/\n")
    uvicorn.run("app:app", host=host, port=port, reload=False)
