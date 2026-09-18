import os
import pandas as pd

ROOT_DIR = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
MASTER_CSV = os.path.join(ROOT_DIR, "src", "macro_engine", "pan_india_28_state_statutory_master.csv")

# Clean, deduplicated, and strictly typed 28-state statutory baseline dataset
clean_data = [
    {"State": "Kerala", "Cement Base (INR/MT)": 6150.0, "Steel Fe-500 (INR/MT)": 56000.0, "Aggregates (INR/cum)": 1400.0, "Handling Labor (INR/day)": 750.0, "PrimaryAnchor": "DES AuditedSeries"},
    {"State": "Tamil Nadu", "Cement Base (INR/MT)": 5602.5, "Steel Fe-500 (INR/MT)": 55665.0, "Aggregates (INR/cum)": 1578.8, "Handling Labor (INR/day)": 628.0, "PrimaryAnchor": "TN SoR 2025-26"},
    {"State": "Karnataka", "Cement Base (INR/MT)": 5400.0, "Steel Fe-500 (INR/MT)": 55200.0, "Aggregates (INR/cum)": 1100.0, "Handling Labor (INR/day)": 580.0, "PrimaryAnchor": "KPWD SR 2024-25"},
    {"State": "Maharashtra", "Cement Base (INR/MT)": 6100.0, "Steel Fe-500 (INR/MT)": 59000.0, "Aggregates (INR/cum)": 1400.0, "Handling Labor (INR/day)": 550.0, "PrimaryAnchor": "MH PWD SSR 2024-25"},
    {"State": "Odisha", "Cement Base (INR/MT)": 5200.0, "Steel Fe-500 (INR/MT)": 52800.0, "Aggregates (INR/cum)": 520.0, "Handling Labor (INR/day)": 450.0, "PrimaryAnchor": "Odisha Works SoR"},
    {"State": "Chhattisgarh", "Cement Base (INR/MT)": 5150.0, "Steel Fe-500 (INR/MT)": 51500.0, "Aggregates (INR/cum)": 490.0, "Handling Labor (INR/day)": 425.0, "PrimaryAnchor": "CG PWD Unified SoR"},
    {"State": "Rajasthan", "Cement Base (INR/MT)": 4950.0, "Steel Fe-500 (INR/MT)": 54000.0, "Aggregates (INR/cum)": 460.0, "Handling Labor (INR/day)": 480.0, "PrimaryAnchor": "Rajasthan PWD BSR"},
    {"State": "Andhra Pradesh", "Cement Base (INR/MT)": 5300.0, "Steel Fe-500 (INR/MT)": 54500.0, "Aggregates (INR/cum)": 620.0, "Handling Labor (INR/day)": 520.0, "PrimaryAnchor": "AP BOCE CSOR 2024-25"},
    {"State": "Telangana", "Cement Base (INR/MT)": 5250.0, "Steel Fe-500 (INR/MT)": 54200.0, "Aggregates (INR/cum)": 680.0, "Handling Labor (INR/day)": 540.0, "PrimaryAnchor": "TS BOCE CSOR 2024-25"},
    {"State": "Uttar Pradesh", "Cement Base (INR/MT)": 5350.0, "Steel Fe-500 (INR/MT)": 54800.0, "Aggregates (INR/cum)": 780.0, "Handling Labor (INR/day)": 460.0, "PrimaryAnchor": "UP PWD SoR 2024-25"},
    {"State": "Delhi NCR", "Cement Base (INR/MT)": 5450.0, "Steel Fe-500 (INR/MT)": 56200.0, "Aggregates (INR/cum)": 1050.0, "Handling Labor (INR/day)": 680.0, "PrimaryAnchor": "CPWD DSR 2023/24"},
    {"State": "Madhya Pradesh", "Cement Base (INR/MT)": 5100.0, "Steel Fe-500 (INR/MT)": 53500.0, "Aggregates (INR/cum)": 540.0, "Handling Labor (INR/day)": 440.0, "PrimaryAnchor": "MP PWD SoR 2024-25"},
    {"State": "Gujarat", "Cement Base (INR/MT)": 5250.0, "Steel Fe-500 (INR/MT)": 55400.0, "Aggregates (INR/cum)": 690.0, "Handling Labor (INR/day)": 510.0, "PrimaryAnchor": "Gujarat R&B SoR"},
    {"State": "Bihar", "Cement Base (INR/MT)": 5400.0, "Steel Fe-500 (INR/MT)": 54200.0, "Aggregates (INR/cum)": 980.0, "Handling Labor (INR/day)": 435.0, "PrimaryAnchor": "Bihar PWD SoR"},
    {"State": "West Bengal", "Cement Base (INR/MT)": 5350.0, "Steel Fe-500 (INR/MT)": 53600.0, "Aggregates (INR/cum)": 890.0, "Handling Labor (INR/day)": 470.0, "PrimaryAnchor": "WB PWD SoR"},
    {"State": "Haryana", "Cement Base (INR/MT)": 5400.0, "Steel Fe-500 (INR/MT)": 55800.0, "Aggregates (INR/cum)": 920.0, "Handling Labor (INR/day)": 590.0, "PrimaryAnchor": "Haryana HSR"},
    {"State": "Punjab", "Cement Base (INR/MT)": 5500.0, "Steel Fe-500 (INR/MT)": 53900.0, "Aggregates (INR/cum)": 720.0, "Handling Labor (INR/day)": 520.0, "PrimaryAnchor": "Punjab CSR"},
    {"State": "Himachal Pradesh", "Cement Base (INR/MT)": 5150.0, "Steel Fe-500 (INR/MT)": 56400.0, "Aggregates (INR/cum)": 580.0, "Handling Labor (INR/day)": 475.0, "PrimaryAnchor": "HPPWD SoR"},
    {"State": "Uttarakhand", "Cement Base (INR/MT)": 5420.0, "Steel Fe-500 (INR/MT)": 56100.0, "Aggregates (INR/cum)": 610.0, "Handling Labor (INR/day)": 500.0, "PrimaryAnchor": "Uttarakhand SoR"},
    {"State": "Jammu and Kashmir", "Cement Base (INR/MT)": 5650.0, "Steel Fe-500 (INR/MT)": 57500.0, "Aggregates (INR/cum)": 640.0, "Handling Labor (INR/day)": 525.0, "PrimaryAnchor": "JK PWD SoR"},
    {"State": "Jharkhand", "Cement Base (INR/MT)": 5220.0, "Steel Fe-500 (INR/MT)": 52400.0, "Aggregates (INR/cum)": 480.0, "Handling Labor (INR/day)": 440.0, "PrimaryAnchor": "Jharkhand SoR"},
    {"State": "Goa", "Cement Base (INR/MT)": 5850.0, "Steel Fe-500 (INR/MT)": 56800.0, "Aggregates (INR/cum)": 880.0, "Handling Labor (INR/day)": 560.0, "PrimaryAnchor": "Goa GSR"},
    {"State": "Meghalaya", "Cement Base (INR/MT)": 5180.0, "Steel Fe-500 (INR/MT)": 57200.0, "Aggregates (INR/cum)": 620.0, "Handling Labor (INR/day)": 480.0, "PrimaryAnchor": "Meghalaya SoR"},
    {"State": "Assam", "Cement Base (INR/MT)": 5380.0, "Steel Fe-500 (INR/MT)": 56500.0, "Aggregates (INR/cum)": 740.0, "Handling Labor (INR/day)": 460.0, "PrimaryAnchor": "Assam SoR"},
    {"State": "Tripura", "Cement Base (INR/MT)": 5900.0, "Steel Fe-500 (INR/MT)": 59800.0, "Aggregates (INR/cum)": 1150.0, "Handling Labor (INR/day)": 490.0, "PrimaryAnchor": "Tripura SoR"},
    {"State": "Sikkim", "Cement Base (INR/MT)": 5850.0, "Steel Fe-500 (INR/MT)": 58200.0, "Aggregates (INR/cum)": 980.0, "Handling Labor (INR/day)": 520.0, "PrimaryAnchor": "Sikkim SoR"},
    {"State": "Manipur", "Cement Base (INR/MT)": 6050.0, "Steel Fe-500 (INR/MT)": 60200.0, "Aggregates (INR/cum)": 1050.0, "Handling Labor (INR/day)": 500.0, "PrimaryAnchor": "Manipur SoR"},
    {"State": "Nagaland", "Cement Base (INR/MT)": 5750.0, "Steel Fe-500 (INR/MT)": 58900.0, "Aggregates (INR/cum)": 880.0, "Handling Labor (INR/day)": 480.0, "PrimaryAnchor": "Nagaland SoR"}
]

df_clean = pd.DataFrame(clean_data)
df_clean.to_csv(MASTER_CSV, index=False)
print(f"[RE-LOCKED] Cleaned 28-State CSV saved to {MASTER_CSV}")
