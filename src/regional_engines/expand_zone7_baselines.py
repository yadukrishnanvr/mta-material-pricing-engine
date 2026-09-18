import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_17_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Haryana",
        "Cement Base (INR/MT)": 5400.00,
        "Steel Fe-500 (INR/MT)": 55800.00,
        "Aggregates (INR/cum)": 920.00,
        "Handling Labor (INR/day)": 590.00,
        "Primary Anchor": "Haryana PWD (B&R) HSR"
    },
    {
        "State": "Punjab",
        "Cement Base (INR/MT)": 5500.00,
        "Steel Fe-500 (INR/MT)": 53900.00,
        "Aggregates (INR/cum)": 720.00,
        "Handling Labor (INR/day)": 520.00,
        "Primary Anchor": "Punjab PWD CSR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)
df_updated.to_csv(master_csv, index=False)

print("=" * 105)
print("UPDATED PAN-INDIA 17-STATE STATUTORY BASELINE MATRIX (ZONE 7 NORTH EXPANSION)")
print("=" * 105)
print(df_updated.to_string(index=False))
print(f"\nLocked 17-state baseline to: {updated_csv}")
