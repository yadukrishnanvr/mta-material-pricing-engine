import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_20_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Himachal Pradesh",
        "Cement Base (INR/MT)": 5150.00,
        "Steel Fe-500 (INR/MT)": 56400.00,
        "Aggregates (INR/cum)": 580.00,
        "Handling Labor (INR/day)": 475.00,
        "Primary Anchor": "HPPWD SoR 2024-25"
    },
    {
        "State": "Uttarakhand",
        "Cement Base (INR/MT)": 5420.00,
        "Steel Fe-500 (INR/MT)": 56100.00,
        "Aggregates (INR/cum)": 610.00,
        "Handling Labor (INR/day)": 500.00,
        "Primary Anchor": "Uttarakhand PWD SoR 2024-25"
    },
    {
        "State": "Jammu and Kashmir",
        "Cement Base (INR/MT)": 5650.00,
        "Steel Fe-500 (INR/MT)": 57500.00,
        "Aggregates (INR/cum)": 640.00,
        "Handling Labor (INR/day)": 525.00,
        "Primary Anchor": "JK PWD SoR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)
df_updated.to_csv(master_csv, index=False)

print("=" * 115)
print("UPDATED PAN-INDIA 20-STATE STATUTORY BASELINE MATRIX (ZONE 8 HIMALAYAN EXPANSION)")
print("=" * 115)
print(df_updated.to_string(index=False))
print(f"\nLocked 20-state baseline to: {updated_csv}")
