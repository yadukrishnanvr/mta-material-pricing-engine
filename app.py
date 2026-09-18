




# --- PHASE 1: CONSUMER & HOUSE BUILDER ENDPOINTS ---

@app.get("/api/market/snapshot")
def get_market_snapshot(state: str = "Kerala"):
    from macro_engine.database_manager import get_connection
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

    # Steel: MT -> kg
    if "Steel" in price_map:
        brand, per_mt, std = price_map["Steel"]
        items.append({
            "id": "steel",
            "name": "TMT Rebar (Fe 550D)",
            "brand": brand,
            "unit": "? / kg",
            "price": round(per_mt / 1000.0, 2),
            "metric_price": per_mt,
            "signal": "BUY",
            "signal_label": "?? Value Zone (Buy Now)",
            "standard": std
        })
    else:
        items.append({
            "id": "steel",
            "name": "TMT Rebar (Fe 550D)",
            "brand": "Tata Tiscon Fe550D",
            "unit": "? / kg",
            "price": 54.5,
            "metric_price": 54500.0,
            "signal": "BUY",
            "signal_label": "?? Value Zone (Buy Now)",
            "standard": "IS 1786:2008"
        })

    # Cement: MT -> 50kg bag (20 bags/MT)
    if "Cement" in price_map:
        brand, per_mt, std = price_map["Cement"]
        items.append({
            "id": "cement",
            "name": "Structural Cement",
            "brand": brand,
            "unit": "? / 50kg bag",
            "price": round(per_mt / 20.0, 2),
            "metric_price": per_mt,
            "signal": "NEUTRAL",
            "signal_label": "?? Stable (Procure Normal)",
            "standard": std
        })
    else:
        items.append({
            "id": "cement",
            "name": "Structural Cement",
            "brand": "UltraTech OPC 53",
            "unit": "? / 50kg bag",
            "price": 420.0,
            "metric_price": 8400.0,
            "signal": "NEUTRAL",
            "signal_label": "?? Stable",
            "standard": "IS 269:2015"
        })

    # M-Sand
    items.append({
        "id": "msand",
        "name": "M-Sand (Concrete / Plastering)",
        "brand": "IS 383 Zone II Crushed",
        "unit": "? / cu.ft",
        "price": 54.0 if state == "Kerala" else 46.0,
        "signal": "BUY",
        "signal_label": "?? Steady",
        "standard": "IS 383:2016"
    })

    # 20mm Aggregates
    items.append({
        "id": "aggregate",
        "name": "20mm Granite Aggregates",
        "brand": "Machine Crushed Blue Metal",
        "unit": "? / cu.ft",
        "price": 48.0 if state == "Kerala" else 42.0,
        "signal": "BUY",
        "signal_label": "?? Favorable",
        "standard": "IS 383:2016"
    })

    return {"state": state, "items": items}

@app.get("/api/market/trend-indicator")
def get_trend_indicator(state: str = "Kerala", commodity: str = "Steel"):
    from macro_engine.database_manager import get_connection
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
            "statutory_sor": [base * 0.96] * 5,
            "latest_spread_pct": 2.1,
            "recommendation": "BUY",
            "recommendation_text": "?? Favorable Price Dip ? Good Window to Lock Structural Materials"
        }

    dates = [r[0][:10] if r[0] else "" for r in rows]
    spot = [round(float(r[1]), 2) for r in rows]
    sor = [round(float(r[2]), 2) for r in rows]
    latest_spread = float(rows[-1][3]) if rows[-1][3] is not None else 0.0

    if latest_spread < -2.0:
        indicator = "BUY"
        status_text = "?? Favorable Price Dip ? Good Window to Lock Slab/Footing Steel"
    elif latest_spread > 4.5:
        indicator = "WAIT"
        status_text = "?? Overheating ? High Dealer Markups. Delay Large Deliveries by 1-2 Weeks"
    else:
        indicator = "NEUTRAL"
        status_text = "?? Fair Valuation ? Procure in Batches Based on Site Schedule"

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
