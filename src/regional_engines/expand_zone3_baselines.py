import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_11_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Uttar Pradesh",
        "Cement Base (INR/MT)": 5350.00,
        "Steel Fe-500 (INR/MT)": 54800.00,
        "Aggregates (INR/cum)": 780.00,
        "Handling Labor (INR/day)": 460.00,
        "Primary Anchor": "UP PWD SoR 2024-25"
    },
    {
        "State": "Delhi NCR",
        "Cement Base (INR/MT)": 5450.00,
        "Steel Fe-500 (INR/MT)": 56200.00,
        "Aggregates (INR/cum)": 1050.00,
        "Handling Labor (INR/day)": 680.00,
        "Primary Anchor": "CPWD DSR 2023/24 (Delhi)"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)

# Update core engine baseline pointer
df_updated.to_csv(master_csv, index=False)

print("=" * 105)
print("UPDATED PAN-INDIA 11-STATE STATUTORY BASELINE MATRIX (ZONE 3 NORTH EXPANSION)")
print("=" * 105)
print(df_updated.to_string(index=False))
print(f"\nLocked 11-state baseline to: {updated_csv}")
