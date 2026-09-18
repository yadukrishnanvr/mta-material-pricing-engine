import os
import sys
import json
from datetime import datetime

ROOT_DIR = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
CACHE_FILE = os.path.join(ROOT_DIR, "src", "macro_engine", "dynamic_market_cache.json")
COMPARISON_FILE = os.path.join(ROOT_DIR, "src", "macro_engine", "market_price_audit_comparison.json")

# 1. Technical Standards & Brand Hierarchy Master
COMMODITY_STANDARDS_MAP = {
    "steel": {
        "Tata Tiscon Fe-500D": {
            "tier": "Primary Integrated",
            "standard": "IS 1786:2008 Fe-500D (BF-BOF)",
            "unit_multiplier": 1.0  # per MT
        },
        "JSW Neosteel Fe-500D": {
            "tier": "Primary Integrated",
            "standard": "IS 1786:2008 Fe-500D (BF-BOF)",
            "unit_multiplier": 1.0
        },
        "SAIL TMT Fe-500D": {
            "tier": "Primary PSU",
            "standard": "IS 1786:2008 Fe-500D (BF-BOF)",
            "unit_multiplier": 1.0
        },
        "Kamdhenu Nxt Fe-500": {
            "tier": "Secondary National",
            "standard": "IS 1786:2008 Fe-500 (IF-LRF)",
            "unit_multiplier": 1.0
        },
        "Raipur Mandi Commercial Billet TMT": {
            "tier": "Secondary Local Re-roller",
            "standard": "IS 1786 Commercial Re-rolled",
            "unit_multiplier": 1.0
        }
    },
    "cement": {
        "UltraTech Super PPC": {
            "tier": "Tier-1 Premium",
            "standard": "IS 1489 (Part 1): 2015 PPC",
            "unit_multiplier": 20.0  # 50 kg bag -> MT conversion (x20)
        },
        "Ambuja Standard PPC": {
            "tier": "Tier-1 Standard",
            "standard": "IS 1489 (Part 1): 2015 PPC",
            "unit_multiplier": 20.0
        },
        "Dalmia DSP / Ramco Supercrete": {
            "tier": "Tier-1 Regional",
            "standard": "IS 1489 / IS 455 PSC",
            "unit_multiplier": 20.0
        },
        "OPC 53 Grade (Commercial Bulk)": {
            "tier": "Industrial Bulk",
            "standard": "IS 269:2015 OPC 53",
            "unit_multiplier": 20.0
        }
    }
}

# 2. Simulated Daily Scraper Ingestion Stream
# In a production environment, this function queries public wholesale listings or B2B feeds.
def fetch_live_scraped_feeds():
    """Simulates real-world scraped mandi trade points across hubs."""
    return [
        # Steel Scrap & Billet Mandi Feeds (converted to Ex-Mill / Mandi price per MT)
        {"state": "Maharashtra", "commodity": "steel", "brand": "Tata Tiscon Fe-500D", "raw_price": 57800.0, "raw_unit": "MT", "source": "Mumbai Industrial Steel Mandi"},
        {"state": "Maharashtra", "commodity": "steel", "brand": "Raipur Mandi Commercial Billet TMT", "raw_price": 46400.0, "raw_unit": "MT", "source": "Jalna/Raipur Rolling Bourse"},
        {"state": "Punjab", "commodity": "steel", "brand": "Kamdhenu Nxt Fe-500", "raw_price": 48200.0, "raw_unit": "MT", "source": "Mandi Gobindgarh Scrap/Rebar Desk"},
        {"state": "Chhattisgarh", "commodity": "steel", "brand": "Raipur Mandi Commercial Billet TMT", "raw_price": 45600.0, "raw_unit": "MT", "source": "Raipur Daily Spot Board"},

        # Cement Bag Retail / Wholesale Feeds (per 50 kg bag)
        {"state": "Kerala", "commodity": "cement", "brand": "UltraTech Super PPC", "raw_price": 410.0, "raw_unit": "bag_50kg", "source": "Kochi Dealer Association Quote"},
        {"state": "Kerala", "commodity": "cement", "brand": "Ambuja Standard PPC", "raw_price": 385.0, "raw_unit": "bag_50kg", "source": "Ernakulam Wholesale Mandi"},
        {"state": "Rajasthan", "commodity": "cement", "brand": "Ambuja Standard PPC", "raw_price": 315.0, "raw_unit": "bag_50kg", "source": "Jaipur Distributor Circular"},
        {"state": "Delhi NCR", "commodity": "cement", "brand": "UltraTech Super PPC", "raw_price": 385.0, "raw_unit": "bag_50kg", "source": "NCR Warehouse Dispatch List"}
    ]

# 3. Analyze, Normalize, and Compare Scraped vs. Statutory Ceilings
def process_and_compare_feeds():
    master_csv = os.path.join(ROOT_DIR, "src", "macro_engine", "pan_india_28_state_statutory_master.csv")
    import pandas as pd
    df_statutory = pd.read_csv(master_csv).set_index("State")

    scraped_feed = fetch_live_scraped_feeds()
    live_cache = {}
    audit_comparison = []

    for item in scraped_feed:
        state = item["state"]
        com = item["commodity"]
        brand = item["brand"]
        raw_price = item["raw_price"]
        unit = item["raw_unit"]
        src = item["source"]

        # Standardization & Unit Normalization
        spec_meta = COMMODITY_STANDARDS_MAP.get(com, {}).get(brand, {})
        multiplier = spec_meta.get("unit_multiplier", 1.0)
        norm_price_per_mt = raw_price * multiplier

        # Retrieve statutory nominal baseline
        if com == "steel":
            statutory_base = df_statutory.loc[state]["Steel Fe-500 (INR/MT)"]
        else:
            statutory_base = df_statutory.loc[state]["Cement Base (INR/MT)"]

        # Delta analysis: Live spot vs Government SoR ceiling
        spread_inr = round(norm_price_per_mt - statutory_base, 2)
        spread_pct = round((spread_inr / statutory_base) * 100, 2)

        comparison_record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "State": state,
            "Commodity": com.upper(),
            "Brand": brand,
            "Tier": spec_meta.get("tier", "Unknown"),
            "Technical Standard": spec_meta.get("standard", "Standard Specification"),
            "Scraped Raw Price": f"₹{raw_price:,.2f} /{unit}",
            "Normalized Spot (INR/MT)": norm_price_per_mt,
            "Statutory Gov Ceiling (INR/MT)": statutory_base,
            "Spread vs Statutory (INR/MT)": spread_inr,
            "Spread Delta (%)": f"{spread_pct:+}%",
            "Verification Source": src
        }
        audit_comparison.append(comparison_record)

        # Update cache dictionary for runtime use
        if state not in live_cache:
            live_cache[state] = {}
        if com not in live_cache[state]:
            live_cache[state][com] = {}
            
        live_cache[state][com][brand] = {
            "spot_base_inr": norm_price_per_mt,
            "tier": spec_meta.get("tier", "Unknown"),
            "standard": spec_meta.get("standard", "Standard Specification"),
            "source": src,
            "timestamp": datetime.now().isoformat()
        }

    # Save outputs
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(live_cache, f, indent=2)

    with open(COMPARISON_FILE, "w", encoding="utf-8") as f:
        json.dump(audit_comparison, f, indent=2)

    df_comp = pd.DataFrame(audit_comparison)
    print("=" * 135)
    print("LIVE SCRAPED vs STATUTORY GOVERNMENT PRICE AUDIT AND COMPARISON MATRIX")
    print("=" * 135)
    cols_to_print = [
        "State", "Commodity", "Brand", "Tier", "Normalized Spot (INR/MT)", 
        "Statutory Gov Ceiling (INR/MT)", "Spread vs Statutory (INR/MT)", "Spread Delta (%)"
    ]
    print(df_comp[cols_to_print].to_string(index=False))
    print(f"\n[CACHE SYNC] Dynamic cache written to: {CACHE_FILE}")
    print(f"[AUDIT LOG] Complete comparison log saved to: {COMPARISON_FILE}")

if __name__ == "__main__":
    process_and_compare_feeds()
