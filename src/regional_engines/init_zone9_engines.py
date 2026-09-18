import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

zone9_corridors = {
    "jharkhand": {
        "state_name": "Jharkhand",
        "zone": "Zone 9 (Eastern Mineral Anchor & Aggregates Basin)",
        "statutory_sources": [
            "Jharkhand PWD (Road Construction Dept) Schedule of Rates (JSR)",
            "Jharkhand State Mineral Development Corporation (JSMDC) E-Sand Gazettes",
            "Jharkhand Labour Commissioner Minimum Wages Notifications"
        ],
        "ibm_anchor_weight": {"iron_ore_share": 0.112, "limestone_share": 0.015},
        "lead_clusters": ["Pakur Black Stone Aggregate Hub", "Ramgarh/Bokaro Induction Furnace Belt", "Chaibasa Clinker Belt"]
    },
    "goa": {
        "state_name": "Goa",
        "zone": "Zone 9 (Western Coastal Enclave)",
        "statutory_sources": [
            "Goa PWD Schedule of Rates (GSR 2023/2024)",
            "Directorate of Mines & Geology Goa Mineral Concession Orders",
            "Goa Labour Welfare Board Minimum Wage Circulars"
        ],
        "ibm_anchor_weight": {"iron_ore_share": 0.021, "limestone_share": 0.000},
        "lead_clusters": ["Mormugao Port Stockyard Hub", "Sanguem-Bicholim Basalt Quarries", "Mandovi River Sand Barging Reaches"]
    }
}

for state_key, config in zone9_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    with open(os.path.join(state_dir, "engine_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 9: JHARKHAND & GOA")
print("=" * 85)
for s in zone9_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
