import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
MACRO_DIR = SRC_DIR / "macro_engine"
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
    scheduler.shutdown(wait=False)

app = FastAPI(title="Pan-India MTA Multi-Attribute Engine", version="2.6.0", lifespan=lifespan)
engine = NationalMaterialPricingEngine(base_dir=ROOT_DIR)
escalation_engine = Clause10CAEscalationEngine(str(DB_PATH))

class MultiQuoteRequest(BaseModel):
    state: str
    city: Optional[str] = None
    commodity: str
    lead_km: float = 40.0
    brand: Optional[str] = None
    grade: Optional[str] = None
    size: Optional[str] = None
    packaging: Optional[str] = None
    mode: str = "calibrated_spot"
    terrain: Optional[str] = None

class EscalationRequest(BaseModel):
    base_contract_value: float
    base_wpi: float
    current_wpi: float
    material_coefficient: float = 0.85
    forecast_months: int = 12
    monthly_inflation_drift_pct: float = 0.45

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "MTA Pricing Engine", "version": "2.6.0"}

@app.get("/api/states")
def list_states():
    return {"states": sorted(list(engine.df_baselines.index))}

@app.get("/api/cities")
def list_cities(state: str):
    clean_st = state.strip() if state else "Maharashtra"
    return {"state": clean_st, "cities": list(get_cities_for_state(clean_st).keys())}

@app.post("/api/quote")
def calculate_quote(req: MultiQuoteRequest):
    try:
        quote = engine.estimate_site_gate_delivered_price(
            state=req.state,
            city=req.city,
            commodity=req.commodity,
            lead_km=req.lead_km,
            brand=req.brand,
            grade=req.grade,
            size=req.size,
            packaging=req.packaging,
            mode=req.mode,
            terrain=req.terrain
        )
        return quote
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/escalation/calculate")
def calculate_escalation(req: EscalationRequest):
    try:
        calc = escalation_engine.calculate_price_variation(
            base_contract_value=req.base_contract_value,
            base_wpi=req.base_wpi,
            current_wpi=req.current_wpi,
            material_coefficient=req.material_coefficient
        )
        forecast = escalation_engine.project_future_escalation(
            current_contract_value=calc["Adjusted Contract Value (INR)"],
            current_wpi=req.current_wpi,
            historical_monthly_drift_pct=req.monthly_inflation_drift_pct,
            months_ahead=req.forecast_months
        )
        return {
            "Clause 10CA Calculation": calc,
            "Future Projections": forecast
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/trends")
def get_price_trends(state: str, commodity: str, brand: Optional[str] = None):
    clean_st = state.strip() if state else "Maharashtra"
    clean_com = commodity.lower().strip() if commodity else "steel"
    
    conn = get_connection()
    cur = conn.cursor()
    
    if brand:
        cur.execute("""
            SELECT scraped_at, normalized_price_inr, statutory_sor_inr, spread_delta_inr, spread_delta_pct
            FROM material_price_audit_log
            WHERE state = ? AND LOWER(commodity) = ? AND brand = ?
            ORDER BY scraped_at ASC
            LIMIT 30
        """, (clean_st, clean_com, brand))
    else:
        cur.execute("""
            SELECT scraped_at, normalized_price_inr, statutory_sor_inr, spread_delta_inr, spread_delta_pct
            FROM material_price_audit_log
            WHERE state = ? AND LOWER(commodity) = ?
            ORDER BY scraped_at ASC
            LIMIT 30
        """, (clean_st, clean_com))
        
    rows = cur.fetchall()
    conn.close()

    labels = []
    spot_series = []
    sor_series = []
    delta_pct_series = []

    for r in rows:
        ts = str(r[0]).split("T")[1][:5] if "T" in str(r[0]) else str(r[0])[-8:-3]
        labels.append(ts)
        spot_series.append(float(r[1]))
        sor_series.append(float(r[2]))
        delta_pct_series.append(float(r[4]))

    if not labels or len(labels) < 2:
        labels = ["D-6", "D-5", "D-4", "D-3", "D-2", "D-1", "Live Spot"]
        quote = engine.estimate_site_gate_delivered_price(clean_st, clean_com, 40.0, brand=brand)
        base = quote["Material Base (INR)"]
        stat_base = float(engine.df_baselines.loc[clean_st]["Steel Fe-500 (INR/MT)" if "steel" in clean_com else ("Cement Base (INR/MT)" if "cement" in clean_com else "Aggregates (INR/cum)")])
        
        spot_series = [round(base * (1.0 + (i * 0.003) - 0.009), 2) for i in range(7)]
        sor_series = [round(stat_base, 2)] * 7
        delta_pct_series = [round(((s - stat_base) / stat_base) * 100, 2) for s in spot_series]

    return {
        "state": clean_st,
        "commodity": clean_com.upper(),
        "brand": brand or "All Observed Hubs",
        "labels": labels,
        "spot_prices": spot_series,
        "sor_ceiling": sor_series,
        "delta_percentages": delta_pct_series
    }

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    states_opts = "".join([f"<option value='{s}'>{s}</option>" for s in sorted(list(engine.df_baselines.index))])
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pan-India Material Analytics & Pricing Suite</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
            .form-control, .form-select { background-color: #0d1117; border: 1px solid #30363d; color: #c9d1d9; }
            .form-control:focus, .form-select:focus { background-color: #0d1117; border-color: #58a6ff; color: #fff; box-shadow: none; }
            .metric-box { background-color: #21262d; border-radius: 6px; padding: 15px; text-align: center; border-left: 4px solid #58a6ff; }
            .metric-val { font-size: 1.5rem; font-weight: 700; color: #58a6ff; }
            .badge-stat { background-color: #238636; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; }
            #errorBanner { display: none; background-color: #8b1818; color: #fff; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-weight: 500; }
        </style>
    </head>
    <body class="py-4">
        <div class="container-fluid px-4">
            <div class="row mb-3 text-center">
                <h2 class="fw-bold text-light">MTA Multi-Attribute Material Pricing & Analytics Engine</h2>
                <p class="text-secondary">Diameter Gauges, BIS Mass Standardizations, Granular Densities & Real-Time Spot vs SoR Delta</p>
            </div>

            <div id="errorBanner"></div>
            
            <div class="row g-4 mb-4">
                <div class="col-lg-4 col-md-5">
                    <div class="card p-4 shadow-sm h-100">
                        <h5 class="text-light mb-3">Procurement Matrix</h5>
                        
                        <div class="mb-3">
                            <label class="form-label">State Jurisdiction</label>
                            <select id="stateSelect" class="form-select" onchange="onStateChange()">
                                __STATES__
                            </select>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">City / Consumption Hub</label>
                            <select id="citySelect" class="form-select" onchange="runQuote()">
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Commodity</label>
                            <select id="commoditySelect" class="form-select" onchange="onCommodityChange()">
                                <option value="steel" selected>Reinforcement Steel (TMT Fe-500D/550D)</option>
                                <option value="cement">Cement (OPC / PPC / Slag)</option>
                                <option value="aggregates">Coarse Aggregates & Manufactured Sand</option>
                            </select>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Brand & Material Fraction</label>
                            <select id="brandSelect" class="form-select" onchange="onBrandChange()">
                            </select>
                        </div>

                        <div class="mb-3" id="gradeGroup">
                            <label class="form-label">Technical Specification / Grade</label>
                            <select id="gradeSelect" class="form-select" onchange="runQuote()">
                            </select>
                        </div>

                        <div class="mb-3" id="sizeGroup">
                            <label class="form-label d-flex justify-content-between">
                                <span>TMT Bar Diameter (Gauge)</span>
                                <span class="badge bg-primary" id="sizeBadge">12mm Base</span>
                            </label>
                            <select id="sizeSelect" class="form-select" onchange="runQuote()">
                                <option value="8mm">8mm (+₹1,500/MT - Slab & Stirrups)</option>
                                <option value="10mm">10mm (+₹1,000/MT - Slabs & Beams)</option>
                                <option value="12mm" selected>12mm (Base Benchmark - Beams/Columns)</option>
                                <option value="16mm">16mm (Base Benchmark - Columns)</option>
                                <option value="20mm">20mm (-₹400/MT - Footings/Foundations)</option>
                                <option value="25mm">25mm (-₹400/MT - Heavy Raft/Piling)</option>
                                <option value="32mm">32mm (+₹1,200/MT - Heavy Flyover/Piers)</option>
                            </select>
                        </div>

                        <div class="mb-3" id="packagingGroup" style="display: none;">
                            <label class="form-label">Packaging / Despatch Mode</label>
                            <select id="packagingSelect" class="form-select" onchange="runQuote()">
                                <option value="50kg HDPE Bag" selected>50kg HDPE Bag (Retail / Wholesale)</option>
                                <option value="Commercial Bulk Tanker">Commercial Bulk Tanker (-₹600/MT Loose Silo)</option>
                            </select>
                        </div>

                        <div class="mb-3" id="leadGroup">
                            <label class="form-label d-flex justify-content-between">
                                <span>Transit Lead (km)</span>
                                <span id="leadVal" class="text-info fw-bold">40 km</span>
                            </label>
                            <input type="range" id="leadRange" class="form-range" min="5" max="250" step="5" value="40" oninput="onLeadChange(this.value)">
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Pricing Regime</label>
                            <select id="modeSelect" class="form-select" onchange="runQuote()">
                                <option value="calibrated_spot" selected>Calibrated Market Spot (Live Feeds)</option>
                                <option value="statutory_nominal">Statutory Nominal (State SoR Baselines)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="col-lg-8 col-md-7">
                    <div class="card p-4 shadow-sm mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="text-light mb-0">Delivered Site-Gate Breakdown</h5>
                            <span id="priceOriginBadge" class="badge-stat">CONNECTING...</span>
                        </div>
                        
                        <div class="row g-3 mb-3">
                            <div class="col-md-4">
                                <div class="metric-box">
                                    <div class="text-secondary small">Base Ex-Plant</div>
                                    <div id="baseRate" class="metric-val">₹0.00</div>
                                    <div id="baseUnit" class="text-secondary small">per MT</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="metric-box" style="border-left-color: #d29922;">
                                    <div class="text-secondary small">Prescribed Conveyance</div>
                                    <div id="freightRate" class="metric-val" style="color: #d29922;">₹0.00</div>
                                    <div class="text-secondary small">Nonlinear Logistics Drag</div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="metric-box" style="border-left-color: #2ea043;">
                                    <div class="text-secondary small">Handling & Royalties</div>
                                    <div id="handlingRate" class="metric-val" style="color: #2ea043;">₹0.00</div>
                                    <div class="text-secondary small">Cess & Mining Seigniorage</div>
                                </div>
                            </div>
                        </div>

                        <div class="p-3 mb-3" style="background-color: #21262d; border-radius: 6px;">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-0 text-light font-monospace" id="totalDelivered">₹0.00</h4>
                                    <small class="text-secondary" id="brandSpecOut">Delivered Rate</small>
                                </div>
                                <span class="badge bg-primary fs-6" id="commodityUnit">INR / MT</span>
                            </div>
                        </div>

                        <div class="p-3 mb-3" id="pieceRateBox" style="background-color: #1a2332; border: 1px solid #1f6feb; border-radius: 6px;">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="text-secondary small">12m Single Bar Rate (IS 1786 Mass Formula)</div>
                                    <h4 class="mb-0 text-info font-monospace" id="perPieceRate">₹0.00 / Piece</h4>
                                </div>
                                <span class="badge bg-info text-dark" id="pieceSizeTag">12mm Gauge</span>
                            </div>
                        </div>

                        <div class="table-responsive">
                            <table class="table table-dark table-sm border-secondary mb-0">
                                <tbody>
                                    <tr><td class="text-secondary">Selected Brand / Fraction</td><td class="text-end fw-bold text-info" id="brandOut">-</td></tr>
                                    <tr><td class="text-secondary">Technical Specification</td><td class="text-end fw-bold text-light" id="gradeOut">-</td></tr>
                                    <tr><td class="text-secondary">Consumption Hub & Tier</td><td class="text-end fw-bold text-warning" id="cityTierOut">-</td></tr>
                                    <tr><td class="text-secondary">Trade Origin Benchmark</td><td class="text-end text-success" id="originOut">-</td></tr>
                                    <tr><td class="text-secondary">Freight Share</td><td class="text-end" id="freightShare">-</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="card p-4 shadow-sm">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h5 class="text-light mb-0">Market Trend vs Statutory SoR Baseline</h5>
                            <span class="badge bg-secondary" id="trendDeltaBadge">Δ 0.0% vs SoR</span>
                        </div>
                        <div style="height: 260px; position: relative;">
                            <canvas id="trendChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let trendChartInstance = null;

            const attributeCatalog = {
                steel: {
                    brands: {
                        "Tata Tiscon (Primary)": ["IS 1786 Fe-500D (Super Ductile)", "IS 1786 Fe-550D High Tensile"],
                        "JSW Neosteel (Primary)": ["IS 1786 Fe-500D", "IS 1786 Fe-550D Pure TMT"],
                        "SAIL / RINL Vizag (PSU)": ["IS 1786 Fe-500D PSU Spec"],
                        "Kamdhenu Nxt (Tier-2)": ["IS 1786 Fe-500 Interlock Power Grid"],
                        "Local Mandi Secondary Re-roller": ["IS 1786 Commercial Re-rolled Grade"]
                    }
                },
                cement: {
                    brands: {
                        "UltraTech Cement (Tier-1 Premium)": ["IS 1489 (Part 1) PPC", "IS 269:2015 OPC-53", "Super Composite"],
                        "Ambuja / ACC (Tier-1 Standard)": ["IS 1489 (Part 1) PPC", "IS 269 OPC-43"],
                        "Shree Cement / Bangur (Tier-1 Commercial)": ["IS 1489 (Part 1) PPC Commercial"],
                        "Dalmia / Ramco (Peninsular/Eastern Tier-1)": ["IS 455 PSC (Slag Cement)", "IS 1489 PPC"]
                    }
                },
                aggregates: {
                    brands: {
                        "Machine Crushed Blue Metal (20mm Grade-A)": ["IS 383:2016 3-Stage Cone Crushed (1.55 MT/cum)"],
                        "10mm Blue Metal Screenings": ["IS 383 Clean Chips (1.45 MT/cum)"],
                        "40mm Blue Metal (Sub-base / Mass)": ["IS 383 Sub-base/Mass PCC (1.58 MT/cum)"],
                        "VSI M-Sand (Zone-II Concrete)": ["IS 383 Zone-II Concrete Sand (1.60 MT/cum)"],
                        "VSI Plaster Sand (P-Sand)": ["IS 383 Fine Plaster Sand (1.48 MT/cum)"],
                        "Quarry Dust / Crusher Fines": ["Crusher Run Fines (<4.75mm | 1.65 MT/cum)"],
                        "Granular Sub-Base (GSB / Wet Mix)": ["MoRTH Dense Graded Sub-base (1.75 MT/cum)"]
                    }
                }
            };

            function showError(msg) {
                const b = document.getElementById('errorBanner');
                b.innerText = msg;
                b.style.display = 'block';
            }

            function clearError() {
                const b = document.getElementById('errorBanner');
                b.style.display = 'none';
            }

            function onLeadChange(val) {
                document.getElementById('leadVal').innerText = val + ' km';
                runQuote();
            }

            async function onStateChange() {
                await updateCityDropdown();
                await runQuote();
                await renderTrendChart();
            }

            async function onCommodityChange() {
                const com = document.getElementById('commoditySelect').value;
                const sizeGrp = document.getElementById('sizeGroup');
                const pieceBox = document.getElementById('pieceRateBox');
                const pkgGrp = document.getElementById('packagingGroup');

                if (com === 'steel') {
                    sizeGrp.style.display = 'block';
                    pieceBox.style.display = 'block';
                    pkgGrp.style.display = 'none';
                } else if (com === 'cement') {
                    sizeGrp.style.display = 'none';
                    pieceBox.style.display = 'none';
                    pkgGrp.style.display = 'block';
                } else {
                    sizeGrp.style.display = 'none';
                    pieceBox.style.display = 'none';
                    pkgGrp.style.display = 'none';
                }
                updateBrandAndGradeDropdowns();
                await runQuote();
                await renderTrendChart();
            }

            function onBrandChange() {
                updateGradeDropdown();
                runQuote();
                renderTrendChart();
            }

            function updateBrandAndGradeDropdowns() {
                const com = document.getElementById('commoditySelect').value;
                const brandsObj = attributeCatalog[com].brands || {};
                const bSelect = document.getElementById('brandSelect');
                bSelect.innerHTML = Object.keys(brandsObj).map(b => `<option value="${b}">${b}</option>`).join('');
                updateGradeDropdown();
            }

            function updateGradeDropdown() {
                const com = document.getElementById('commoditySelect').value;
                const bVal = document.getElementById('brandSelect').value;
                const grades = (attributeCatalog[com].brands[bVal]) || ["Standard Spec"];
                const gSelect = document.getElementById('gradeSelect');
                gSelect.innerHTML = grades.map(g => `<option value="${g}">${g}</option>`).join('');
            }

            async function updateCityDropdown() {
                const state = document.getElementById('stateSelect').value;
                try {
                    const res = await fetch(`/api/cities?state=${encodeURIComponent(state)}`);
                    const data = await res.json();
                    const cSelect = document.getElementById('citySelect');
                    cSelect.innerHTML = data.cities.map(c => `<option value="${c}">${c}</option>`).join('');
                } catch (e) {
                    console.error('City fetch error:', e);
                }
            }

            async function renderTrendChart() {
                const state = document.getElementById('stateSelect').value;
                const com = document.getElementById('commoditySelect').value;
                const brand = document.getElementById('brandSelect').value;

                try {
                    const res = await fetch(`/api/analytics/trends?state=${encodeURIComponent(state)}&commodity=${encodeURIComponent(com)}&brand=${encodeURIComponent(brand)}`);
                    const data = await res.json();

                    const ctx = document.getElementById('trendChart').getContext('2d');
                    if (trendChartInstance) {
                        trendChartInstance.destroy();
                    }

                    const latestSpot = data.spot_prices[data.spot_prices.length - 1];
                    const latestSoR = data.sor_ceiling[data.sor_ceiling.length - 1];
                    const deltaPct = (((latestSpot - latestSoR) / latestSoR) * 100).toFixed(1);
                    
                    const deltaBadge = document.getElementById('trendDeltaBadge');
                    deltaBadge.innerText = `${deltaPct > 0 ? '+' : ''}${deltaPct}% vs SoR Baseline`;
                    deltaBadge.className = deltaPct > 0 ? 'badge bg-danger' : 'badge bg-success';

                    trendChartInstance = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.labels,
                            datasets: [
                                {
                                    label: 'Live Mandi / Spot Market (INR)',
                                    data: data.spot_prices,
                                    borderColor: '#58a6ff',
                                    backgroundColor: 'rgba(88, 166, 255, 0.1)',
                                    fill: true,
                                    tension: 0.35,
                                    borderWidth: 2
                                },
                                {
                                    label: 'Statutory SoR Ceiling Baseline (INR)',
                                    data: data.sor_ceiling,
                                    borderColor: '#f85149',
                                    borderDash: [6, 4],
                                    borderWidth: 2,
                                    pointRadius: 0,
                                    fill: false
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                x: { grid: { color: '#21262d' }, ticks: { color: '#8b949e' } },
                                y: { grid: { color: '#21262d' }, ticks: { color: '#8b949e' } }
                            },
                            plugins: {
                                legend: { labels: { color: '#c9d1d9', font: { size: 11 } } }
                            }
                        }
                    });
                } catch (e) {
                    console.error('Trend chart render failure:', e);
                }
            }

            async function runQuote() {
                clearError();
                const state = document.getElementById('stateSelect').value;
                const city = document.getElementById('citySelect').value;
                const commodity = document.getElementById('commoditySelect').value;
                const brand = document.getElementById('brandSelect').value;
                const grade = document.getElementById('gradeSelect').value;
                const size = (commodity === 'steel') ? document.getElementById('sizeSelect').value : null;
                const packaging = (commodity === 'cement') ? document.getElementById('packagingSelect').value : null;
                const lead_km = parseFloat(document.getElementById('leadRange').value);
                const mode = document.getElementById('modeSelect').value;

                if (commodity === 'steel' && size) {
                    document.getElementById('sizeBadge').innerText = size;
                }

                const payload = { 
                    state: state || 'Maharashtra', 
                    city: city || null, 
                    commodity: commodity || 'steel', 
                    brand: brand || null, 
                    grade: grade || null, 
                    size: size || '12mm', 
                    packaging: packaging || null, 
                    lead_km: lead_km || 40.0, 
                    mode: mode || 'calibrated_spot' 
                };

                try {
                    const res = await fetch('/api/quote', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    if (!res.ok) {
                        const err = await res.json().catch(() => ({ detail: 'HTTP Error ' + res.status }));
                        showError('Quote API Error: ' + (err.detail || 'Request rejected'));
                        return;
                    }

                    const data = await res.json();
                    document.getElementById('baseRate').innerText = '₹' + data['Material Base (INR)'].toLocaleString();
                    document.getElementById('baseUnit').innerText = 'per ' + data['Unit'];
                    document.getElementById('freightRate').innerText = '₹' + data['State Prescribed Freight (INR)'].toLocaleString();
                    document.getElementById('handlingRate').innerText = '₹' + data['Handling & Cess (INR)'].toLocaleString();
                    document.getElementById('totalDelivered').innerText = '₹' + data['Total Delivered Gate (INR)'].toLocaleString();
                    document.getElementById('commodityUnit').innerText = 'INR / ' + data['Unit'];

                    if (commodity === 'steel') {
                        document.getElementById('perPieceRate').innerText = '₹' + data['Estimated Per-Piece (12m Bar)'].toLocaleString() + ' / piece';
                        document.getElementById('pieceSizeTag').innerText = data['Section Size'] + ' Bar (12m)';
                    }

                    document.getElementById('brandOut').innerText = data['Brand / Tier'];
                    document.getElementById('gradeOut').innerText = data['Size Specification'];
                    document.getElementById('cityTierOut').innerText = `${data['City / Hub']} [${data['City Tier']}]`;
                    document.getElementById('brandSpecOut').innerText = data['Brand Specification'];
                    document.getElementById('originOut').innerText = data['Price Origin'];

                    const total = data['Total Delivered Gate (INR)'];
                    const freight = data['State Prescribed Freight (INR)'];
                    const pct = total > 0 ? ((freight / total) * 100).toFixed(1) : 0;
                    document.getElementById('freightShare').innerText = `${data['State']} (${pct}% Freight)`;

                    const badge = document.getElementById('priceOriginBadge');
                    badge.innerText = data['Price Origin'].toUpperCase();
                    badge.style.backgroundColor = data['Price Origin'].includes('LIVE') ? '#a371f7' : '#238636';

                } catch (err) {
                    showError('Network Exception: ' + err.message);
                }
            }

            window.onload = async () => {
                document.getElementById('stateSelect').value = 'Maharashtra';
                document.getElementById('commoditySelect').value = 'steel';
                await updateCityDropdown();
                updateBrandAndGradeDropdowns();
                await runQuote();
                await renderTrendChart();
            };
        </script>
    </body>
    </html>
    """
    return html.replace("__STATES__", states_opts)

if __name__ == "__main__":
    import uvicorn
    # When deployed on Render, PORT is provided as an env var.
    # Locally, bind to 127.0.0.1 so clicking links works out-of-the-box.
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    
    print(f"\n🚀 Server running at http://127.0.0.1:{port}/ (or http://localhost:{port}/)\n")
    uvicorn.run("app:app", host=host, port=port, reload=False)
