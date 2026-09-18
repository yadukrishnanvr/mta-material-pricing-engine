import os
import re
import glob
import sqlite3
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis"
FINDINGS_DIR = os.path.join(ROOT_DIR, "findings-docs")
DB_PATH = os.path.join(ROOT_DIR, "src", "macro_engine", "mta_market_live.db")

def init_statutory_inventory_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Dedicated table for granular statutory schedules, quarry permits, and carriage books
    cur.execute("""
        CREATE TABLE IF NOT EXISTS statutory_document_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_extension TEXT NOT NULL,
            file_size_kb REAL NOT NULL,
            jurisdiction TEXT NOT NULL,
            document_type TEXT NOT NULL,
            target_commodity TEXT NOT NULL,
            quarry_royalty_seigniorage_inr REAL,
            base_conveyance_first_km_inr REAL,
            subsequent_km_rate_inr REAL,
            density_compaction_factor REAL,
            escalation_clause_ref TEXT,
            parsed_metadata_json TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def scan_and_extract_findings():
    init_statutory_inventory_schema()
    
    # Locate findings-docs folder across the workspace
    target_dir = FINDINGS_DIR
    if not os.path.exists(target_dir):
        # Fallback probe for findings-docs
        matches = glob.glob(os.path.join(ROOT_DIR, "**", "findings-docs"), recursive=True)
        if matches:
            target_dir = matches[0]
        else:
            logging.warning(f"findings-docs folder not found directly at {FINDINGS_DIR}. Creating scan directory.")
            os.makedirs(FINDINGS_DIR, exist_ok=True)
            target_dir = FINDINGS_DIR

    logging.info(f"[INVENTORY] Scanning folder: {target_dir}")
    all_files = []
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            all_files.append(os.path.join(root, f))

    if not all_files:
        logging.warning(f"No files currently located in {target_dir}.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    extracted_records = []

    for file_path in all_files:
        fname = os.path.basename(file_path)
        ext = os.path.splitext(fname)[1].lower()
        size_kb = round(os.path.getsize(file_path) / 1024, 2)
        
        doc_type = "Unclassified Technical Doc"
        jurisdiction = "National / Pan-India"
        target_commodity = "MULTI-COMMODITY"
        royalty = 0.0
        base_first_km = 120.0
        subsequent_km = 4.85
        density_factor = 1.55
        escalation_ref = "None"
        meta_dict = {}

        # Jurisdiction heuristics
        name_lower = fname.lower()
        if "kerala" in name_lower or "kpwd" in name_lower:
            jurisdiction = "Kerala"
        elif "maharashtra" in name_lower or "pwd" in name_lower and "mh" in name_lower:
            jurisdiction = "Maharashtra"
        elif "delhi" in name_lower or "cpwd" in name_lower or "dsor" in name_lower:
            jurisdiction = "Delhi NCR / CPWD"
        elif "tamil" in name_lower or "tn" in name_lower:
            jurisdiction = "Tamil Nadu"
        elif "karnataka" in name_lower or "kpwd" in name_lower:
            jurisdiction = "Karnataka"

        # Commodity & rulebook classification
        if "carriage" in name_lower or "conveyance" in name_lower or "freight" in name_lower:
            doc_type = "Carriage Schedule / Freight Rulebook"
            base_first_km = 145.0 if jurisdiction == "Kerala" else 120.0
            subsequent_km = 6.20 if jurisdiction == "Kerala" else 4.85
        elif "quarry" in name_lower or "seigniorage" in name_lower or "mineral" in name_lower or "aggregate" in name_lower:
            doc_type = "Quarry Permit & Mining Seigniorage Index"
            target_commodity = "AGGREGATES & SAND"
            royalty = 90.0 if jurisdiction == "Maharashtra" else (110.0 if jurisdiction == "Kerala" else 75.0)
            density_factor = 1.55
        elif "sor" in name_lower or "schedule" in name_lower or "csor" in name_lower:
            doc_type = "Public Works Schedule of Rates (SoR)"
            escalation_ref = "Clause 10CA / RBI WPI Index"
        
        # Read text-based formats for specific regex extraction
        if ext in [".txt", ".csv", ".json", ".md"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as tf:
                    raw_text = tf.read(50000) # Read first 50KB for tokens
                    
                    # Search for seigniorage/royalty rates
                    royalty_match = re.search(r"(?:seigniorage|royalty)[^\d]*([\d,.]+)", raw_text, re.IGNORECASE)
                    if royalty_match:
                        try:
                            royalty = float(royalty_match.group(1).replace(",", ""))
                        except Exception:
                            pass

                    # Search for bulk density
                    density_match = re.search(r"(?:density|bulk density)[^\d]*([\d.]+)", raw_text, re.IGNORECASE)
                    if density_match:
                        try:
                            density_factor = float(density_match.group(1))
                        except Exception:
                            pass

                    # Search for contract escalation clauses
                    if "10ca" in raw_text.lower():
                        escalation_ref = "CPWD Clause 10CA"
                    elif "wpi" in raw_text.lower():
                        escalation_ref = "RBI WPI Wholesale Price Index Escalation"

                    meta_dict["preview"] = raw_text[:200].replace("\n", " ")
            except Exception as e:
                meta_dict["parse_error"] = str(e)

        meta_json = json.dumps(meta_dict)

        # Upsert record into statutory_document_inventory
        cur.execute("""
            INSERT INTO statutory_document_inventory (
                filename, file_extension, file_size_kb, jurisdiction, 
                document_type, target_commodity, quarry_royalty_seigniorage_inr, 
                base_conveyance_first_km_inr, subsequent_km_rate_inr, 
                density_compaction_factor, escalation_clause_ref, parsed_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fname, ext, size_kb, jurisdiction, doc_type, 
            target_commodity, royalty, base_first_km, subsequent_km, 
            density_factor, escalation_ref, meta_json
        ))

        extracted_records.append({
            "File": fname,
            "Type": doc_type,
            "State": jurisdiction,
            "Royalty (₹/cum)": royalty,
            "First-km (₹)": base_first_km,
            "Density (MT/cum)": density_factor,
            "Escalation": escalation_ref
        })

    conn.commit()
    conn.close()

    logging.info(f"[SUCCESS] Scanned and logged {len(extracted_records)} statutory documents into mta_market_live.db")
    
    if extracted_records:
        df_inv = pd.DataFrame(extracted_records)
        print("\n" + "="*110)
        print("                        STATUTORY DOCUMENTS & CARRIAGE RULEBOOK INVENTORY                      ")
        print("="*110)
        print(df_inv.to_string(index=False))
        print("="*110 + "\n")

if __name__ == "__main__":
    scan_and_extract_findings()
