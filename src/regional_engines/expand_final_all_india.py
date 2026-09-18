import os, json
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
final_csv = os.path.join(macro_dir, "pan_india_28_state_statutory_master.csv")

final_corridors = {
    "sikkim": {
        "state_name": "Sikkim",
        "zone": "Himalayan High-Altitude Corridor",
        "statutory_sources": ["Sikkim PWD Schedule of Rates (SPWD SOR)"],
        "lead_clusters": ["Rangpo Border Terminal", "Teesta Basin Aggregate Leases", "Gangtok Freight Hub"],
        "default_terrain": "mountainous"
    },
    "manipur": {
        "state_name": "Manipur",
        "zone": "North-Eastern Transit Frontier",
        "statutory_sources": ["Manipur PWD Schedule of Rates (MPWD SOR)"],
        "lead_clusters": ["Imphal Valley Mandis", "Barak/Chindwin Gravel Basins"],
        "default_terrain": "mountainous"
    },
    "nagaland": {
        "state_name": "Nagaland",
        "zone": "North-Eastern Transit Frontier",
        "statutory_sources": ["Nagaland NPWD Schedule of Rates (NPWD SOR)"],
        "lead_clusters": ["Dimapur Railhead Mandi", "Dhansiri River Sand Reach", "Kohima Hill Spoke"],
        "default_terrain": "mountainous"
    }
}

for state_key, config in final_corridors.items():
    state_dir = os.path.join(engines_root, state_key)
    os.makedirs(os.path.join(state_dir, "raw_statutory"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "processed_benchmarks"), exist_ok=True)
    with open(os.path.join(state_dir, "engine_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

new_rows = [
    {
        "State": "Sikkim",
        "Cement Base (INR/MT)": 5850.00,
        "Steel Fe-500 (INR/MT)": 58200.00,
        "Aggregates (INR/cum)": 980.00,
        "Handling Labor (INR/day)": 520.00,
        "Primary Anchor": "Sikkim PWD SoR 2024-25"
    },
    {
        "State": "Manipur",
        "Cement Base (INR/MT)": 6050.00,
        "Steel Fe-500 (INR/MT)": 60200.00,
        "Aggregates (INR/cum)": 1050.00,
        "Handling Labor (INR/day)": 500.00,
        "Primary Anchor": "Manipur PWD SoR 2024-25"
    },
    {
        "State": "Nagaland",
        "Cement Base (INR/MT)": 5750.00,
        "Steel Fe-500 (INR/MT)": 58900.00,
        "Aggregates (INR/cum)": 880.00,
        "Handling Labor (INR/day)": 480.00,
        "Primary Anchor": "Nagaland PWD SoR 2024-25"
    }
]

df = pd.read_csv(os.path.join(macro_dir, "pan_india_25_state_statutory_baselines.csv"))
df_final = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

df_final.to_csv(final_csv, index=False)
df_final.to_csv(master_csv, index=False)

print("=" * 115)
print("FINAL PAN-INDIA 28-STATE ALL-INDIA STATUTORY MASTER MATRIX")
print("=" * 115)
print(df_final.to_string(index=False))
print(f"\nLocked Complete 28-State Pan-India Master Matrix to: {final_csv}")
