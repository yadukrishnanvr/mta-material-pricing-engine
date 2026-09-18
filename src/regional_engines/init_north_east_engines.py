import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

new_states = {
    "odisha": {
        "state_name": "Odisha",
        "zone": "Eastern Mineral Heartland",
        "statutory_sources": [
            "Odisha Works Department Schedule of Rates (Odisha SoR)",
            "Odisha Mining Corporation (OMC) Iron Ore Auction E-Gazettes",
            "Directorate of Geology Minor Mineral Concession Registries"
        ],
        "ibm_anchor_weight": {"iron_ore_share": 0.537, "limestone_share": 0.031},
        "primary_hubs": ["Joda-Barbil Mining Cluster", "Angul-Rourkela Steel Belts", "Cuttack Sand Basins"]
    },
    "chhattisgarh": {
        "state_name": "Chhattisgarh",
        "zone": "Eastern Mineral Heartland",
        "statutory_sources": [
            "Chhattisgarh PWD Unified Schedule of Rates (CG-SoR)",
            "NMDC Bailadila Merchant Mining Bulletins",
            "Chhattisgarh Mineral Resources Dept Quarry Lease Directory"
        ],
        "ibm_anchor_weight": {"iron_ore_share": 0.166, "limestone_share": 0.109},
        "primary_hubs": ["Bailadila Iron Basin", "Raipur-Durg Billet Clusters", "Bilaspur Clinker Belt"]
    },
    "rajasthan": {
        "state_name": "Rajasthan",
        "zone": "Northern Gangetic / Western Ridge",
        "statutory_sources": [
            "Rajasthan PWD Schedule of Rates (BSR Road & Building)",
            "Department of Mines and Geology (DMG Rajasthan) DSRs",
            "Rajasthan State Mines & Minerals Ltd (RSMML) Gazettes"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.230, "iron_ore_share": 0.024},
        "primary_hubs": ["Nimbahera-Chittorgarh Clinker Hub", "Kotputli Extraction Belt", "Alwar Aggregate Clusters"]
    }
}

for state_key, config in new_states.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    
    cfg_file = os.path.join(state_dir, "engine_config.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("SUCCESSFULLY INITIALIZED REGIONAL ENGINES: ODISHA, CHHATTISGARH, RAJASTHAN")
print("=" * 85)
for s in new_states.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
