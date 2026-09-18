import os
import sys
import json
import sqlite3
from pathlib import Path
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", MODULE_DIR))
DB_PATH = DATA_DIR / "mta_market_live.db"
CACHE_PATH = DATA_DIR / "dynamic_market_cache.json"
MASTER_CSV = MODULE_DIR / "pan_india_28_state_statutory_master.csv"

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from city_tier_registry import get_city_profile, get_cities_for_state

class NationalMaterialPricingEngine:
    def __init__(self, base_dir=ROOT_DIR):
        self.base_dir = Path(base_dir)
        self.db_path = str(DB_PATH)
        self.master_csv = str(MASTER_CSV)
        self.cache_file = str(CACHE_PATH)
        
        df = pd.read_csv(self.master_csv)
        df.columns = df.columns.str.strip()
        df["State"] = df["State"].astype(str).str.strip()
        self.df_baselines = df.drop_duplicates(subset=["State"], keep="last").set_index("State")
        
        self.terrain_friction = {"plain": 1.00, "rolling": 1.15, "mountainous": 1.60, "ghat_heavy": 2.00}
        self.default_state_terrain = {
            "Kerala": "ghat_heavy", "Himachal Pradesh": "mountainous", "Uttarakhand": "mountainous",
            "Jammu and Kashmir": "mountainous", "Meghalaya": "mountainous", "Sikkim": "mountainous",
            "Manipur": "mountainous", "Nagaland": "mountainous", "Assam": "rolling", "Maharashtra": "rolling"
        }

        self.tmt_size_matrix = {
            "8mm":  {"offset_inr_per_mt": 1500.0, "wt_kg_per_12m": 4.732, "pcs_per_mt": 211, "spec": "Slab & Stirrups (High rolling pass)"},
            "10mm": {"offset_inr_per_mt": 1000.0, "wt_kg_per_12m": 7.404, "pcs_per_mt": 135, "spec": "Beams & Slabs"},
            "12mm": {"offset_inr_per_mt": 0.0,    "wt_kg_per_12m": 10.648, "pcs_per_mt": 94,  "spec": "Benchmark Gauge (Columns/Beams)"},
            "16mm": {"offset_inr_per_mt": 0.0,    "wt_kg_per_12m": 18.940, "pcs_per_mt": 53,  "spec": "Benchmark Gauge (Structural Columns)"},
            "20mm": {"offset_inr_per_mt": -400.0, "wt_kg_per_12m": 29.592, "pcs_per_mt": 34,  "spec": "Heavy Foundations & Retaining Walls"},
            "25mm": {"offset_inr_per_mt": -400.0, "wt_kg_per_12m": 46.236, "pcs_per_mt": 22,  "spec": "Bridge Girders & Deep Basements"},
            "32mm": {"offset_inr_per_mt": 1200.0, "wt_kg_per_12m": 75.756, "pcs_per_mt": 13,  "spec": "Heavy Pier & Flyover Foundations"}
        }

        self.aggregate_density_matrix = {
            "Quarry Dust / Crusher Fines":            {"density_mt_per_cum": 1.65, "compaction_factor": 1.18, "offset_inr": -300.0, "spec": "Crusher run fines (<4.75mm)"},
            "VSI M-Sand (Zone-II Concrete)":          {"density_mt_per_cum": 1.60, "compaction_factor": 1.13, "offset_inr": 450.0,  "spec": "Manufactured Concrete Sand (IS 383 Zone-II)"},
            "VSI Plaster Sand (P-Sand)":              {"density_mt_per_cum": 1.48, "compaction_factor": 1.14, "offset_inr": 600.0,  "spec": "Fine washed sand for plastering (<2.36mm)"},
            "10mm Blue Metal Screenings":             {"density_mt_per_cum": 1.45, "compaction_factor": 1.11, "offset_inr": 150.0,  "spec": "Clean 10mm chips for precast & mix"},
            "Machine Crushed Blue Metal (20mm Grade-A)": {"density_mt_per_cum": 1.55, "compaction_factor": 1.10, "offset_inr": 0.0,    "spec": "Standard 3-Stage Cone Crushed (10-20mm)"},
            "40mm Blue Metal (Sub-base / Mass)":      {"density_mt_per_cum": 1.58, "compaction_factor": 1.11, "offset_inr": -180.0, "spec": "Coarse aggregate for mass PCC / GSB"},
            "Granular Sub-Base (GSB / Wet Mix)":      {"density_mt_per_cum": 1.75, "compaction_factor": 1.15, "offset_inr": -400.0, "spec": "CBR-tested dense graded base"}
        }

        self.brand_tier_matrix = {
            "steel": {
                "Tata Tiscon (Primary)": {"type": "primary", "offset_inr": 5200.0, "description": "Primary Blast Furnace Fe-500D (BF-BOF)"},
                "JSW Neosteel (Primary)": {"type": "primary", "offset_inr": 4600.0, "description": "Primary Blast Furnace Fe-500D (BF-BOF)"},
                "SAIL / RINL Vizag (PSU)": {"type": "primary", "offset_inr": 3200.0, "description": "Primary PSU Mill Fe-500D"},
                "Kamdhenu Nxt (Tier-2)": {"type": "secondary", "offset_inr": 1500.0, "description": "Secondary Franchise IF-LRF Rebar"},
                "Local Mandi Secondary Re-roller": {"type": "secondary", "offset_inr": 0.0, "description": "Commercial Scrap Re-rolled TMT"}
            },
            "cement": {
                "UltraTech Cement (Tier-1 Premium)": {"type": "primary", "offset_inr": 450.0, "description": "High-Grade Clinker PPC/OPC-53"},
                "Ambuja / ACC (Tier-1 Standard)": {"type": "primary", "offset_inr": 250.0, "description": "Standard Commercial Grade PPC"},
                "Shree Cement / Bangur (Tier-1 Commercial)": {"type": "primary", "offset_inr": -200.0, "description": "High-Efficiency Commercial PPC"},
                "Dalmia / Ramco (Peninsular/Eastern Tier-1)": {"type": "primary", "offset_inr": 150.0, "description": "Regional Dominant Brand PPC"}
            },
            "aggregates": {k: {"type": "standard", "offset_inr": v["offset_inr"], "description": v["spec"]} for k, v in self.aggregate_density_matrix.items()}
        }

    def get_statutory_quarry_seigniorage(self, state: str) -> float:
        royalty = 75.0
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("""
                    SELECT AVG(quarry_royalty_seigniorage_inr) 
                    FROM statutory_document_inventory 
                    WHERE jurisdiction = ? AND quarry_royalty_seigniorage_inr > 0
                """, (state,))
                row = cur.fetchone()
                if row and row[0] is not None:
                    royalty = float(row[0])
                conn.close()
        except Exception:
            pass
        return round(royalty, 2)

    def get_fuel_drift_multiplier(self, state: str) -> float:
        drift = 1.00
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("SELECT drift_factor FROM fuel_drift_ledger WHERE state = ?", (state,))
                row = cur.fetchone()
                if row and row[0] is not None:
                    drift = float(row[0])
                conn.close()
        except Exception:
            pass
        return drift

    def compute_conveyance(self, state: str, lead_km: float, terrain: str) -> float:
        lead = max(1.0, float(lead_km))
        base_threshold = 120.00
        alpha = 4.85
        beta = 0.88
        fuel_mult = self.get_fuel_drift_multiplier(state)
        freight_plain = (base_threshold + (alpha * (lead ** beta))) * fuel_mult
        friction = self.terrain_friction.get(str(terrain).lower(), 1.00)
        return round(freight_plain * friction, 2)

    def get_available_brands(self, commodity: str):
        com = str(commodity).lower().strip()
        if "steel" in com:
            return list(self.brand_tier_matrix["steel"].keys())
        elif "cement" in com:
            return list(self.brand_tier_matrix["cement"].keys())
        elif "aggregate" in com:
            return list(self.brand_tier_matrix["aggregates"].keys())
        return []

    def get_live_cached_price(self, state: str, commodity: str, brand: str):
        if not os.path.exists(self.cache_file):
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(state, {}).get(commodity.lower(), {}).get(brand, None)
        except Exception:
            return None

    def estimate_site_gate_delivered_price(self, state: str, commodity: str, lead_km: float, 
                                           city=None, brand=None, grade=None, size=None, packaging=None,
                                           mode="calibrated_spot", terrain=None):
        clean_state = str(state).strip() if state else "Maharashtra"
        if clean_state not in self.df_baselines.index:
            clean_state = "Maharashtra"

        row = self.df_baselines.loc[clean_state]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        city_profile = get_city_profile(clean_state, city)
        tier_mult = city_profile.get("tier_multiplier", 1.00)
        city_cess = city_profile.get("octroi_cess_inr", 0.0)
        city_handling = city_profile.get("local_handling_inr", 0.0)
        city_tier_name = city_profile.get("tier", "Standard Market")

        if not terrain:
            terrain = self.default_state_terrain.get(clean_state, "plain")

        com = str(commodity).lower().strip()
        price_origin = "Statutory Calibrated"
        unit = "MT"
        size_desc = "Standard Specification"
        unit_price_per_piece = 0.0
        conversion_meta = {}

        freight = self.compute_conveyance(clean_state, lead_km, terrain)

        # ---------------- STEEL ----------------
        if "steel" in com:
            if not brand or brand not in self.brand_tier_matrix["steel"]:
                brand = "Tata Tiscon (Primary)"
            if not size or size not in self.tmt_size_matrix:
                size = "12mm"

            spec = self.brand_tier_matrix["steel"][brand]
            size_meta = self.tmt_size_matrix[size]
            size_offset = size_meta["offset_inr_per_mt"]
            size_desc = f"{size} ({size_meta['spec']})"
            grade_offset = 800.0 if (grade and "550" in grade) else 0.0

            live_record = self.get_live_cached_price(clean_state, "steel", brand)
            if mode == "calibrated_spot" and live_record:
                base_mandi = float(live_record["spot_base_inr"])
                base_ex_plant = (base_mandi + size_offset + grade_offset) * tier_mult
                price_origin = f"LIVE API ({live_record.get('source', 'Bourse Ledger')})"
            else:
                sor_raw = float(row["Steel Fe-500 (INR/MT)"])
                base_ex_plant = (sor_raw + spec["offset_inr"] + size_offset + grade_offset) * tier_mult

            handling = (float(row["Handling Labor (INR/day)"]) / 15.0) + city_handling
            delivered = round(base_ex_plant + freight + handling + city_cess, 2)
            unit_price_per_piece = round(delivered / size_meta["pcs_per_mt"], 2)

        # ---------------- CEMENT ----------------
        elif "cement" in com:
            if not brand or brand not in self.brand_tier_matrix["cement"]:
                brand = "UltraTech Cement (Tier-1 Premium)"

            spec = self.brand_tier_matrix["cement"][brand]
            grade_offset = 400.0 if (grade and "OPC-53" in grade) else 0.0
            pack_offset = -600.0 if (packaging and "Bulk" in packaging) else 0.0

            live_record = self.get_live_cached_price(clean_state, "cement", brand)
            if mode == "calibrated_spot" and live_record:
                base_mandi = float(live_record["spot_base_inr"])
                base_ex_plant = (base_mandi + grade_offset + pack_offset) * tier_mult
                price_origin = f"LIVE API ({live_record.get('source', 'Trade Circular')})"
            else:
                sor_raw = float(row["Cement Base (INR/MT)"])
                base_ex_plant = (sor_raw + spec["offset_inr"] + grade_offset + pack_offset) * tier_mult

            handling = (float(row["Handling Labor (INR/day)"]) / 10.0) + city_handling
            delivered = round(base_ex_plant + freight + handling + city_cess, 2)
            size_desc = packaging or "50kg HDPE Bagged"

        # ---------------- AGGREGATES & SAND ----------------
        elif "aggregate" in com:
            unit = "cum"
            if not brand or brand not in self.aggregate_density_matrix:
                brand = "Machine Crushed Blue Metal (20mm Grade-A)"

            density_data = self.aggregate_density_matrix[brand]
            density_factor = density_data["density_mt_per_cum"]
            compaction_factor = density_data["compaction_factor"]
            spec = self.brand_tier_matrix["aggregates"][brand]

            freight = round(freight * (density_factor / 1.0), 2)
            statutory_royalty = self.get_statutory_quarry_seigniorage(clean_state)

            live_record = self.get_live_cached_price(clean_state, "aggregates", brand)
            if mode == "calibrated_spot" and live_record:
                base_mandi = float(live_record["spot_base_inr"])
                base_ex_plant = base_mandi * tier_mult
                price_origin = f"LIVE API ({live_record.get('source', 'Weighbridge Registry')})"
            else:
                sor_raw = float(row["Aggregates (INR/cum)"])
                base_ex_plant = (sor_raw + spec["offset_inr"]) * tier_mult

            handling = (float(row["Handling Labor (INR/day)"]) / 8.0) + (city_handling / 2.0)
            delivered = round(base_ex_plant + freight + handling + (city_cess / 2.0) + statutory_royalty, 2)

            equivalent_tonne_rate = round(delivered / density_factor, 2)
            compacted_cum_rate = round(delivered * compaction_factor, 2)

            conversion_meta = {
                "density_mt_per_cum": density_factor,
                "compaction_factor": compaction_factor,
                "equivalent_price_per_tonne": equivalent_tonne_rate,
                "compacted_in_situ_cum_rate": compacted_cum_rate
            }
            size_desc = f"{density_data['spec']} [Bulk Density: {density_factor} MT/cum | Compaction: {compaction_factor}]"

        return {
            "State": clean_state,
            "City / Hub": city or "Standard State Hub",
            "City Tier": city_tier_name,
            "Commodity": commodity.upper(),
            "Brand / Tier": brand,
            "Section Size": size if "steel" in com else "N/A",
            "Size Specification": size_desc,
            "Estimated Per-Piece (12m Bar)": unit_price_per_piece,
            "Brand Specification": spec["description"],
            "Price Origin": price_origin,
            "Pricing Mode": mode,
            "Unit": unit,
            "Material Base (INR)": round(base_ex_plant, 2),
            "Lead (km)": float(lead_km),
            "Terrain": terrain,
            "State Prescribed Freight (INR)": freight,
            "Handling & Cess (INR)": round(handling + city_cess, 2),
            "Total Delivered Gate (INR)": delivered,
            "Aggregate Volumetric Breakdown": conversion_meta if "aggregate" in com else None
        }
