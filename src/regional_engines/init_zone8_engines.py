import os, json

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

zone8_corridors = {
    "himachal_pradesh": {
        "state_name": "Himachal Pradesh",
        "zone": "Zone 8 (Himalayan Northern Belt)",
        "statutory_sources": [
            "HPPWD Schedule of Rates (HPSOR Road & Bridge/Building)",
            "HP Department of Industries Geological Wing Lease Circulars",
            "HP Labour Department Minimum Wage Orders"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.041, "iron_ore_share": 0.000},
        "lead_clusters": ["Barmana/Darlaghat Clinker Hubs", "Baddi Industrial Corridor", "Kangra Aggregate Belts"],
        "default_terrain": "mountainous"
    },
    "uttarakhand": {
        "state_name": "Uttarakhand",
        "zone": "Zone 8 (Himalayan Northern Belt)",
        "statutory_sources": [
            "Uttarakhand PWD Schedule of Rates",
            "Uttarakhand Mining Directorate Riverbed RBM Auction Gazettes",
            "Uttarakhand Labour Commissioner Minimum Wages"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.010, "iron_ore_share": 0.000},
        "lead_clusters": ["Haridwar/Roorkee Industrial Sinks", "Gaula/Haldwani Boulder Basins", "Dehradun-Rishikesh Terminals"],
        "default_terrain": "mountainous"
    },
    "jammu_kashmir": {
        "state_name": "Jammu and Kashmir",
        "zone": "Zone 8 (Himalayan Northern Belt)",
        "statutory_sources": [
            "JK PWD Schedule of Rates",
            "J&K Geology and Mining Department Minor Mineral Rules",
            "UT of J&K Labour & Employment Department Wage Orders"
        ],
        "ibm_anchor_weight": {"limestone_share": 0.008, "iron_ore_share": 0.000},
        "lead_clusters": ["Bari Brahmana/Samba Industrial Steel Mandis", "Khrew/Pulwama Clinker Belt", "Jhelum Sand/Shingle Basins"],
        "default_terrain": "mountainous"
    }
}

for state_key, config in zone8_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    with open(os.path.join(state_dir, "engine_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

print("=" * 85)
print("INITIALIZED ZONE 8 ENGINES: HIMACHAL PRADESH, UTTARAKHAND, JAMMU & KASHMIR")
print("=" * 85)
for s in zone8_corridors.keys():
    print(f" - Initialized: src/regional_engines/{s}/engine_config.json")
