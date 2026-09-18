import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

new_zones = {
    "andhra_pradesh": {
        "state_name": "Andhra Pradesh",
        "zone": "Zone 1 Expansion (Southern Peninsular)",
        "statutory_sources": [
            "AP Board of Chief Engineers Common Standard Schedule of Rates (AP CSOR)",
            "AP Mineral Development Corporation (APMDC) E-Auction Gazettes",
            "Directorate of Mines and Geology Minor Mineral Concession Registries"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.134, "iron_ore_share": 0.005},
        "lead_clusters": ["YSR Kadapa/Muddanur Clinker Belt", "Palnadu/Macherla Basins", "Visakhapatnam Steel/Port Corridors"]
    },
    "telangana": {
        "state_name": "Telangana",
        "zone": "Zone 1 Expansion (Southern Peninsular)",
        "statutory_sources": [
            "Telangana Board of Chief Engineers Common Standard Schedule of Rates (TS CSOR)",
            "Telangana State Mineral Development Corporation (TSMDC) Sand Streams",
            "Mines and Geology Department Minor Mineral Lease Audits"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.059, "iron_ore_share": 0.001},
        "lead_clusters": ["Nalgonda/Miryalaguda Clinker Belts", "Karimnagar/Godavari Sand Basins", "Hyderabad-Kukatpally Re-rolling Clusters"]
    }
}

for state_key, config in new_zones.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    
    cfg_file = os.path.join(state_dir, "engine_config.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 1 EXPANSION ENGINES: ANDHRA PRADESH & TELANGANA")
print("=" * 85)
for s in new_zones.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
