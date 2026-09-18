import pandas as pd
import numpy as np
import os

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
ibm_csv = os.path.join(base_dir, "src", "macro_engine", "ibm_msmp_limestone_ironore_cleaned.csv")
out_dir = os.path.join(base_dir, "src", "macro_engine")

df = pd.read_csv(ibm_csv)
df = df[df['cumulative_qty_mt'] > 100].copy()

# Commodity-specific unit scaling
def compute_pit_rate(row):
    # Limestone is reported in Tonnes, Value in '000 INR
    if row['commodity'] == 'Limestone':
        return (row['cumulative_val_inr_crores'] * 1000) / row['cumulative_qty_mt']
    # Iron Ore quantity in MSMP is '000 MT, Value in '000 INR -> Direct ratio yields INR/MT
    elif row['commodity'] == 'Iron Ore':
        rate = (row['cumulative_val_inr_crores'] * 1000) / row['cumulative_qty_mt']
        return rate / 1000.0 if rate > 100000 else rate
    return np.nan

df['pit_mouth_rate_inr_mt'] = df.apply(compute_pit_rate, axis=1)

print("=" * 85)
print("1. CORRECTED PIT-MOUTH BASERATE (INR / MT) BY COMMODITY & STATE")
print("=" * 85)
pivot_cost = df.groupby(['commodity', 'state'])['pit_mouth_rate_inr_mt'].median().unstack(level=0)
print(pivot_cost.round(2))

# Save normalized national upstream database
norm_path = os.path.join(out_dir, "national_pithead_rates_by_state_normalized.csv")
df.to_csv(norm_path, index=False)
print(f"\nLocked normalized baseline into: {norm_path}")
