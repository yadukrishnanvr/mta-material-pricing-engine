import os, glob, re
import pypdf
import pandas as pd

base_ibm = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis\FINDINGS-DOCS\INDIAN BUREAU OF MINES"
out_dir = r"C:\Users\Yadhu\OneDrive\Documents\price_prediction-analysis\src\macro_engine"
os.makedirs(out_dir, exist_ok=True)

march_files = glob.glob(os.path.join(base_ibm, "**", "*Mar*.pdf"), recursive=True)
target_states = [
    "Rajasthan", "Madhya Pradesh", "Andhra Pradesh", "Chhattisgarh", 
    "Karnataka", "Odisha", "Tamil Nadu", "Gujarat", "Jharkhand", "Maharashtra"
]

clean_records = []

for pdf_path in sorted(march_files):
    fname = os.path.basename(pdf_path)
    year_match = re.search(r"20\d{2}", fname) or re.search(r"20\d{2}", os.path.dirname(pdf_path))
    fiscal_year = int(year_match.group(0)) if year_match else None
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)
        active_mineral = None
        
        for p_idx in range(5, min(65, num_pages)):
            text = reader.pages[p_idx].extract_text()
            if not text:
                continue
            
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines:
                lower = line.lower()
                
                if "table" in lower and "mineral" in lower:
                    active_mineral = None
                if ("limestone" in lower or "pwuk irfkj" in lower) and not any(s.lower() in lower for s in target_states):
                    active_mineral = "Limestone"
                elif ("iron ore" in lower or "yksg v;ld" in lower) and not any(s.lower() in lower for s in target_states):
                    active_mineral = "Iron Ore"
                elif any(other in lower for other in ["bauxite", "chromite", "copper ore", "lead & zinc", "manganese ore"]):
                    active_mineral = None
                
                if not active_mineral:
                    continue
                
                matched_state = next((st for st in target_states if re.search(r"\b" + st + r"\b", line, re.I)), None)
                if matched_state:
                    line_no_state = re.sub(matched_state, "", line, flags=re.I)
                    cleaned_line = re.sub(r"[#%;\"*@–—]", " ", line_no_state)
                    tokens = [t.replace(",", "") for t in cleaned_line.split() if re.match(r"^\d+(\.\d+)?$", t.replace(",", ""))]
                    
                    if len(tokens) >= 4:
                        qty_cumulative = float(tokens[-2])
                        val_cumulative = float(tokens[-1])
                        
                        if qty_cumulative > 0:
                            clean_records.append({
                                "fiscal_year": fiscal_year,
                                "commodity": active_mineral,
                                "state": matched_state,
                                "cumulative_qty_mt": qty_cumulative,
                                "cumulative_val_inr_crores": val_cumulative,
                                "source_file": fname
                            })
    except Exception:
        continue

df = pd.DataFrame(clean_records).drop_duplicates(subset=["fiscal_year", "commodity", "state", "cumulative_qty_mt"])
out_path = os.path.join(out_dir, "ibm_msmp_limestone_ironore_cleaned.csv")
df.to_csv(out_path, index=False)

print("=" * 85)
print(f"PARSED & CLEANED {len(df)} VALID STATE-COMMODITY ANNUAL ROWS")
print("=" * 85)
if not df.empty:
    print(df.groupby(["commodity", "state"])["fiscal_year"].count().unstack(fill_value=0))
    print("\nSAMPLE NORMALIZED ROWS:")
    print(df[["fiscal_year", "commodity", "state", "cumulative_qty_mt", "cumulative_val_inr_crores"]].head(10).to_string(index=False))
else:
    print("No records parsed. Run diagnostics.")
