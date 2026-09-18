import os, glob

base_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
keywords = [
    "odisha", "pwd_odisha", "osor", "chhattisgarh", "pwd_cg", "rajasthan", 
    "pwd_raj", "bsr", "nimbahera", "bilaspur", "bailadila", "omc", "rsmml"
]

print("=" * 85)
print("AUDITING LOCAL DISK FOR NORTH & EAST STATUTORY ASSETS")
print("=" * 85)

matches = []
for root, dirs, files in os.walk(base_dir):
    for file in files:
        f_lower = file.lower()
        if any(k in f_lower for k in keywords) and file.endswith((".pdf", ".xlsx", ".csv", ".json")):
            full_path = os.path.join(root, file)
            matches.append((full_path, os.path.getsize(full_path) / (1024 * 1024)))

if matches:
    for m, size in matches:
        rel = os.path.relpath(m, base_dir)
        print(f" [FOUND] {rel} ({size:.2f} MB)")
else:
    print("No localized PWD SoRs found for OD / CG / RJ. Statutory extraction will pull directly from primary state gazettes.")
