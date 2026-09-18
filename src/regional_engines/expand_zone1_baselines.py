import os
import pandas as pd

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_dir = os.path.join(base_dir, "src", "macro_engine")
master_csv = os.path.join(macro_dir, "pan_india_7_state_statutory_baselines.csv")
updated_csv = os.path.join(macro_dir, "pan_india_9_state_statutory_baselines.csv")

df = pd.read_csv(master_csv)

new_rows = [
    {
        "State": "Andhra Pradesh",
        "Cement Base (INR/MT)": 5300.00,
        "Steel Fe-500 (INR/MT)": 54500.00,
        "Aggregates (INR/cum)": 620.00,
        "Handling Labor (INR/day)": 520.00,
        "Primary Anchor": "AP BOCE CSOR 2024-25"
    },
    {
        "State": "Telangana",
        "Cement Base (INR/MT)": 5250.00,
        "Steel Fe-500 (INR/MT)": 54200.00,
        "Aggregates (INR/cum)": 680.00,
        "Handling Labor (INR/day)": 540.00,
        "Primary Anchor": "TS BOCE CSOR 2024-25"
    }
]

df_updated = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_updated.to_csv(updated_csv, index=False)

# Keep the base link updated for national_pricing_engine.py
df_updated.to_csv(master_csv, index=False)

print("=" * 105)
print("UPDATED PAN-INDIA 9-STATE STATUTORY BASELINE MATRIX (ZONE 1 PENINSULA EXPANSION)")
print("=" * 105)
print(df_updated.to_string(index=False))
print(f"\nLocked 9-state baseline to: {updated_csv}")
