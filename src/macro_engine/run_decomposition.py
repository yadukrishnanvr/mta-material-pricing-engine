import pandas as pd
import numpy as np
import os

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
macro_csv = os.path.join(base_dir, "src", "macro_engine", "national_pithead_rates_by_state_normalized.csv")

df_macro = pd.read_csv(macro_csv)

# Codified PWD baseline rates for active regional engines
state_schedules = {
    'Tamil Nadu': {'cement_sor': 5602.50, 'rebar_sor': 55665.00, 'anchor_limestone': 'Tamil Nadu', 'anchor_iron': 'Karnataka'},
    'Karnataka':  {'cement_sor': 5400.00, 'rebar_sor': 55200.00, 'anchor_limestone': 'Karnataka',  'anchor_iron': 'Karnataka'},
    'Maharashtra':{'cement_sor': 6100.00, 'rebar_sor': 59000.00, 'anchor_limestone': 'Madhya Pradesh', 'anchor_iron': 'Chhattisgarh'},
    'Kerala':     {'cement_sor': 6150.00, 'rebar_sor': 56000.00, 'anchor_limestone': 'Tamil Nadu', 'anchor_iron': 'Karnataka'}
}

results = []
for state, cfg in state_schedules.items():
    # Retrieve upstream median pit-head baselines
    lime_rate = df_macro[(df_macro['commodity'] == 'Limestone') & (df_macro['state'] == cfg['anchor_limestone'])]['pit_mouth_rate_inr_mt'].median()
    iron_rate = df_macro[(df_macro['commodity'] == 'Iron Ore') & (df_macro['state'] == cfg['anchor_iron'])]['pit_mouth_rate_inr_mt'].median()
    
    # 1.45 MT Limestone per MT Clinker / Cement
    cement_raw_cost = lime_rate * 1.45
    cement_processing_margin = cfg['cement_sor'] - cement_raw_cost
    
    # 1.60 MT Iron Ore per MT Sponge/Billet -> TMT Rebar
    steel_raw_cost = iron_rate * 1.60
    steel_processing_margin = cfg['rebar_sor'] - steel_raw_cost
    
    results.append({
        'Target State Engine': state,
        'Cement Schedule Base (INR/MT)': cfg['cement_sor'],
        'Raw Limestone Floor (INR/MT)': round(cement_raw_cost, 2),
        'Thermal/Grinding/Margin (INR/MT)': round(cement_processing_margin, 2),
        'Rebar Schedule Base (INR/MT)': cfg['rebar_sor'],
        'Raw Iron Ore Floor (INR/MT)': round(steel_raw_cost, 2),
        'Secondary Conversion Margin (INR/MT)': round(steel_processing_margin, 2)
    })

res_df = pd.DataFrame(results)
print("=" * 105)
print("STATUTORY COST DECOMPOSITION & CONVERSION SPREADS ACROSS REGIONAL ENGINES")
print("=" * 105)
print(res_df.to_string(index=False))

out_summary = os.path.join(base_dir, "src", "macro_engine", "regional_cost_decomposition_summary.csv")
res_df.to_csv(out_summary, index=False)
print(f"\nDecomposition matrix saved to: {out_summary}")
