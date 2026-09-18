import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_22_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Jharkhand",
        "Cement Base (INR/MT)": 5220.00,
        "Steel Fe-500 (INR/MT)": 52400.00,
        "Aggregates (INR/cum)": 480.00,
        "Handling Labor (INR/day)": 440.00,
        "Primary Anchor": "Jharkhand PWD SoR 2024-25"
    },
    {
        "State": "Goa",
        "Cement Base (INR/MT)": 5850.00,
        "Steel Fe-500 (INR/MT)": 56800.00,
        "Aggregates (INR/cum)": 880.00,
        "Handling Labor (INR/day)": 560.00,
        "Primary Anchor": "Goa PWD GSR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)
df_updated.to_csv(master_csv, index=False)

print("=" * 115)
print("UPDATED PAN-INDIA 22-STATE STATUTORY BASELINE MATRIX (ZONE 9 MINERAL ANCHORS)")
print("=" * 115)
print(df_updated.to_string(index=False))
print(f"\nLocked 22-state baseline to: {updated_csv}")
