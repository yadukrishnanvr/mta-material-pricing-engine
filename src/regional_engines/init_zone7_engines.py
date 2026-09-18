import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

zone7_corridors = {
    "haryana": {
        "state_name": "Haryana",
        "zone": "Zone 7 (Northern Industrial Rim)",
        "statutory_sources": [
            "Haryana PWD (B&R) Haryana Schedule of Rates (HSR)",
            "Department of Mines & Geology Haryana Stone/Sand E-Auction Gazettes",
            "Haryana Labour Department Minimum Wage Notifications"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.000, "iron_ore_share": 0.000},
        "lead_clusters": ["Nuh/Aravalli Perimeter Buffer Zones", "Faridabad/Gurugram Inflow Sinks", "Hisar-Panipat Re-rolling Mills"]
    },
    "punjab": {
        "state_name": "Punjab",
        "zone": "Zone 7 (Northern Industrial Rim)",
        "statutory_sources": [
            "Punjab PWD Common Schedule of Rates (CSR)",
            "Department of Mines and Geology Punjab Minor Mineral Concession Rules",
            "Punjab Labour Commissioner Unskilled Wage Circulars"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.000, "iron_ore_share": 0.000},
        "lead_clusters": ["Mandi Gobindgarh Secondary Steel Capital", "Pathankot/Ropar Boulder Mining Basins", "Ludhiana Industrial Terminals"]
    }
}

for state_key, config in zone7_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    
    cfg_file = os.path.join(state_dir, "engine_config.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 7: HARYANA & PUNJAB")
print("=" * 85)
for s in zone7_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
