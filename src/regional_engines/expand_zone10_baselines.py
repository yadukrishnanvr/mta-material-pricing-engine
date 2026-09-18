import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_25_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Meghalaya",
        "Cement Base (INR/MT)": 5180.00,
        "Steel Fe-500 (INR/MT)": 57200.00,
        "Aggregates (INR/cum)": 620.00,
        "Handling Labor (INR/day)": 480.00,
        "Primary Anchor": "Meghalaya PWD SoR 2024-25"
    },
    {
        "State": "Assam",
        "Cement Base (INR/MT)": 5380.00,
        "Steel Fe-500 (INR/MT)": 56500.00,
        "Aggregates (INR/cum)": 740.00,
        "Handling Labor (INR/day)": 460.00,
        "Primary Anchor": "Assam PWD SoR 2024-25"
    },
    {
        "State": "Tripura",
        "Cement Base (INR/MT)": 5900.00,
        "Steel Fe-500 (INR/MT)": 59800.00,
        "Aggregates (INR/cum)": 1150.00,
        "Handling Labor (INR/day)": 490.00,
        "Primary Anchor": "Tripura PWD SoR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)
df_updated.to_csv(master_csv, index=False)

print("=" * 115)
print("UPDATED PAN-INDIA 25-STATE STATUTORY BASELINE MATRIX (ZONE 10 NORTH-EAST EXPANSION)")
print("=" * 115)
print(df_updated.to_string(index=False))
print(f"\nLocked 25-state baseline to: {updated_csv}")
