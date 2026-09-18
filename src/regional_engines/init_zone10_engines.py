import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

zone10_corridors = {
    "assam": {
        "state_name": "Assam",
        "zone": "Zone 10 (North-Eastern Gateway)",
        "statutory_sources": [
            "Assam PWD Schedule of Rates (APWD Building & Road SOR)",
            "Assam Minor Mineral Concession Rules Gazettes",
            "Assam Labour Commissioner Minimum Wage Notifications"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.015, "iron_ore_share": 0.000},
        "lead_clusters": ["Guwahati-Amingaon Steel Mandis", "Brahmaputra River Sand Basins", "Bokajan Clinker Belt"],
        "default_terrain": "rolling"
    },
    "meghalaya": {
        "state_name": "Meghalaya",
        "zone": "Zone 10 (North-Eastern Limestone Anchor)",
        "statutory_sources": [
            "Meghalaya PWD Schedule of Rates (MPWD SOR)",
            "Meghalaya Directorate of Mineral Resources Gazettes",
            "Meghalaya Labour Department Minimum Wage Orders"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.038, "iron_ore_share": 0.000},
        "lead_clusters": ["Lumshnong/Jaintia Hills Clinker Hub", "Cherrapunji/East Khasi Quartzite Leases", "Byrnihat Industrial Corridor"],
        "default_terrain": "mountainous"
    },
    "tripura": {
        "state_name": "Tripura",
        "zone": "Zone 10 (North-Eastern Transit Deficit Sink)",
        "statutory_sources": [
            "Tripura PWD Schedule of Rates (TPWD SOR)",
            "Tripura Department of Industries and Mines Mineral Rules",
            "Tripura Labour Department Minimum Wage Notifications"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.000, "iron_ore_share": 0.000},
        "lead_clusters": ["Agartala Railhead Terminal", "Gomati River Sand Basins", "Bodhjungnagar Industrial Growth Centre"],
        "default_terrain": "plain"
    }
}

for state_key, config in zone10_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    with open(os.path.join(state_dir, "engine_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 10: ASSAM, MEGHALAYA, TRIPURA")
print("=" * 85)
for s in zone10_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
