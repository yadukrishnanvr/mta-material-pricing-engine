import os, json
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
engines_root = os.path.join(base_dir, "src", "regional_engines")

statutory_profiles = {
    "odisha": {
        "state_name": "Odisha",
        "zone": "Eastern Mineral Heartland",
        "cement_base_inr_mt": 5200.00,
        "steel_rebar_inr_mt": 52800.00,
        "coarse_metal_20mm_cum": 520.00,
        "river_sand_m_sand_cum": 410.00,
        "handling_labor_floor_day": 450.00,
        "conveyance_model": "Non-linear decay (Base 6.20 INR/t-km down to 3.80 INR/t-km)",
        "terrain_friction": 1.15
    },
    "chhattisgarh": {
        "state_name": "Chhattisgarh",
        "zone": "Eastern Mineral Heartland",
        "cement_base_inr_mt": 5150.00,
        "steel_rebar_inr_mt": 51500.00,
        "coarse_metal_20mm_cum": 490.00,
        "river_sand_m_sand_cum": 440.00,
        "handling_labor_floor_day": 425.00,
        "conveyance_model": "Unified PWD Scale (Base 6.50 INR/t-km down to 3.90 INR/t-km)",
        "terrain_friction": 1.20
    },
    "rajasthan": {
        "state_name": "Rajasthan",
        "zone": "Northern Gangetic / Western Ridge",
        "cement_base_inr_mt": 4950.00,
        "steel_rebar_inr_mt": 54000.00,
        "coarse_metal_20mm_cum": 460.00,
        "river_sand_m_sand_cum": 580.00,
        "handling_labor_floor_day": 480.00,
        "conveyance_model": "Rajasthan BSR Lead Matrix (Base 6.80 INR/t-km down to 4.10 INR/t-km)",
        "terrain_friction": 1.10
    }
}

for state_key, profile in statutory_profiles.items():
    cfg_file = os.path.join(engines_root, state_key, "engine_config.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(profile)
    else:
        data = profile
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Consolidated 7-State Statutory Summary
summary_records = [
    {"State": "Kerala", "Cement Base (INR/MT)": 6150.00, "Steel Fe-500 (INR/MT)": 56000.00, "Aggregates (INR/cum)": 1400.00, "Handling Labor (INR/day)": 750.00, "Primary Anchor": "DES Audited Series"},
    {"State": "Tamil Nadu", "Cement Base (INR/MT)": 5602.50, "Steel Fe-500 (INR/MT)": 55665.00, "Aggregates (INR/cum)": 1578.80, "Handling Labor (INR/day)": 628.00, "Primary Anchor": "TN SoR 2025-26 (M-0001/2)"},
    {"State": "Karnataka", "Cement Base (INR/MT)": 5400.00, "Steel Fe-500 (INR/MT)": 55200.00, "Aggregates (INR/cum)": 1100.00, "Handling Labor (INR/day)": 580.00, "Primary Anchor": "KPWD SR 2024-25"},
    {"State": "Maharashtra", "Cement Base (INR/MT)": 6100.00, "Steel Fe-500 (INR/MT)": 59000.00, "Aggregates (INR/cum)": 1400.00, "Handling Labor (INR/day)": 550.00, "Primary Anchor": "MH PWD SSR 2024-25"},
    {"State": "Odisha", "Cement Base (INR/MT)": 5200.00, "Steel Fe-500 (INR/MT)": 52800.00, "Aggregates (INR/cum)": 520.00, "Handling Labor (INR/day)": 450.00, "Primary Anchor": "Odisha Works SoR"},
    {"State": "Chhattisgarh", "Cement Base (INR/MT)": 5150.00, "Steel Fe-500 (INR/MT)": 51500.00, "Aggregates (INR/cum)": 490.00, "Handling Labor (INR/day)": 425.00, "Primary Anchor": "CG PWD Unified SoR"},
    {"State": "Rajasthan", "Cement Base (INR/MT)": 4950.00, "Steel Fe-500 (INR/MT)": 54000.00, "Aggregates (INR/cum)": 460.00, "Handling Labor (INR/day)": 480.00, "Primary Anchor": "Rajasthan PWD BSR"}
]

df_all = pd.DataFrame(summary_records)
out_csv = os.path.join(base_dir, "src", "macro_engine", "pan_india_7_state_statutory_baselines.csv")
df_all.to_csv(out_csv, index=False)

print("=" * 95)
print("CONSOLIDATED 7-STATE PAN-INDIA STATUTORY BASELINE MATRIX")
print("=" * 95)
print(df_all.to_string(index=False))
print(f"\nSaved consolidated matrix to: {out_csv}")
