import pandas as pd
import numpy as np
import os

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
ibm_csv = os.path.join(base_dir, "src", "macro_engine", "ibm_msmp_limestone_ironore_cleaned.csv")
out_dir = os.path.join(base_dir, "src", "macro_engine")

df = pd.read_csv(ibm_csv)

# Derive statutory pit-mouth cost per tonne (INR/MT)
# Exclude micro-artifacts where quantity is negligible
df = df[df['cumulative_qty_mt'] > 1000].copy()
# IBM Value is reported in thousand rupees ('000 INR)
df['pit_mouth_rate_inr_mt'] = (df['cumulative_val_inr_crores'] * 1000) / df['cumulative_qty_mt']

print("=" * 85)
print("1. EMPIRICAL PIT-MOUTH EXTRACTION COST (INR / MT) BY STATE (ANNUAL MEDIANS)")
print("=" * 85)
cost_summary = df.groupby(['commodity', 'state'])['pit_mouth_rate_inr_mt'].median().unstack(level=0)
print(cost_summary.round(2))

# Save processed national macro series
macro_out = os.path.join(out_dir, "national_pithead_rates_by_state.csv")
df.to_csv(macro_out, index=False)
print(f"\nSaved processed pit-head baseline to: {macro_out}")
