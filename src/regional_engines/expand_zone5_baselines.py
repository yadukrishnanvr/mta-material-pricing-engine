import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_13_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Madhya Pradesh",
        "Cement Base (INR/MT)": 5100.00,
        "Steel Fe-500 (INR/MT)": 53500.00,
        "Aggregates (INR/cum)": 540.00,
        "Handling Labor (INR/day)": 440.00,
        "Primary Anchor": "MP PWD SoR 2024-25"
    },
    {
        "State": "Gujarat",
        "Cement Base (INR/MT)": 5250.00,
        "Steel Fe-500 (INR/MT)": 55400.00,
        "Aggregates (INR/cum)": 690.00,
        "Handling Labor (INR/day)": 510.00,
        "Primary Anchor": "Gujarat R&B SoR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)

# Sync with the active engine pointer
df_updated.to_csv(master_csv, index=False)

print("=" * 105)
print("UPDATED PAN-INDIA 13-STATE STATUTORY BASELINE MATRIX (ZONE 5 CENTRAL & WEST EXPANSION)")
print("=" * 105)
print(df_updated.to_string(index=False))
print(f"\nLocked 13-state baseline to: {updated_csv}")
