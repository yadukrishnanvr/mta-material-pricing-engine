import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

new_corridors = {
    "uttar_pradesh": {
        "state_name": "Uttar Pradesh",
        "zone": "Zone 3 Expansion (Northern Gangetic Sink)",
        "statutory_sources": [
            "UP PWD Schedule of Rates (Roads & Bridges / Buildings)",
            "Directorate of Geology & Mining UP Minor Mineral Auction Gazettes",
            "UP Minimum Wages Advisory Board Gazettes"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.012, "iron_ore_share": 0.000},
        "lead_clusters": ["Sonbhadra Clinker/Aggregate Basins", "Kanpur/Lucknow Mandis", "Ghaziabad Secondary Re-rolling Belt"]
    },
    "delhi_ncr": {
        "state_name": "Delhi NCR",
        "zone": "Zone 3 Expansion (Northern Gangetic Sink)",
        "statutory_sources": [
            "Central Public Works Department Delhi Schedule of Rates (CPWD DSR 2023/2024)",
            "Delhi PWD Schedule of Rates",
            "Delhi Gazette Minimum Wage Rates for Unskilled Labour"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.000, "iron_ore_share": 0.000},
        "lead_clusters": ["Kotputli/Alwar Aggregate Sourcing Inflows", "Loni/Ghaziabad Steel Stockyards", "Okhla/Faridabad Grinding Terminals"]
    }
}

for state_key, config in new_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    
    cfg_file = os.path.join(state_dir, "engine_config.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 3 EXPANSION: UTTAR PRADESH & DELHI NCR")
print("=" * 85)
for s in new_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
