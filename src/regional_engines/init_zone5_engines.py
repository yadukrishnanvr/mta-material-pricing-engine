import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

zone5_corridors = {
    "madhya_pradesh": {
        "state_name": "Madhya Pradesh",
        "zone": "Zone 5 (Central Limestone & Thermal Corridor)",
        "statutory_sources": [
            "MP PWD Schedule of Rates (SOR Buildings & Bridges)",
            "MP Mineral Resources Department Minor Mineral Rules",
            "Labour Commissioner MP Gazette Minimum Wages"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.139, "iron_ore_share": 0.025},
        "lead_clusters": ["Rewa-Satna Clinker Belt", "Jabalpur Aggregates", "Pithampur/Indore Industrial Stockyards"]
    },
    "gujarat": {
        "state_name": "Gujarat",
        "zone": "Zone 5 (Western Maritime & Industrial Basin)",
        "statutory_sources": [
            "Gujarat Roads & Buildings (R&B) Department SOR",
            "Gujarat Mineral Development Corporation (GMDC) Gazettes",
            "Office of the Commissioner of Labour Gujarat Wage Orders"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.067, "iron_ore_share": 0.000},
        "lead_clusters": ["Saurashtra/Kutch Coastal Clinker", "Sevaliya Basalt Traps", "Ahmedabad/Hazira Re-rolling Clusters"]
    }
}

for state_key, config in zone5_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    
    cfg_file = os.path.join(state_dir, "engine_config.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 5: MADHYA PRADESH & GUJARAT")
print("=" * 85)
for s in zone5_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
