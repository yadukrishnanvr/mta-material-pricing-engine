import sys, os, argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from macro_engine.national_pricing_engine import NationalMaterialPricingEngine

def main():
    parser = argparse.ArgumentParser(description="Pan-India Material Trend Analysis (MTA) CLI")
    parser.add_argument("--state", type=str, required=True, help="State name (e.g., 'Kerala', 'Rajasthan', 'Chhattisgarh')")
    parser.add_argument("--commodity", type=str, required=True, choices=["cement", "steel", "aggregates"], help="Material commodity")
    parser.add_argument("--lead", type=float, default=25.0, help="Dispatch lead distance in km (default: 25.0)")
    parser.add_argument("--mode", type=str, default="statutory_nominal", choices=["statutory_nominal", "calibrated_spot"], help="Pricing mode")
    parser.add_argument("--terrain", type=str, default=None, choices=["plain", "rolling", "mountainous", "ghat_heavy"], help="Terrain override")

    args = parser.parse_args()
    engine = NationalMaterialPricingEngine()

    try:
        quote = engine.estimate_site_gate_delivered_price(
            state=args.state,
            commodity=args.commodity,
            lead_km=args.lead,
            mode=args.mode,
            terrain=args.terrain
        )
        print("\n" + "=" * 70)
        print(f"       MATERIAL TREND ANALYSIS (MTA) COST SHEET [{args.mode.upper()}]       ")
        print("=" * 70)
        for k, v in quote.items():
            print(f" {k:<30}: {v}")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
