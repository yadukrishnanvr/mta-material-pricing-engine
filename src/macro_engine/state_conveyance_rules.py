import os
import pandas as pd

# State-wise codified statutory freight decay curves (INR/t-km)
STATE_FREIGHT_RULES = {
    "Kerala": [
        (5, 11.20), (10, 9.40), (20, 8.10), (50, 7.20), (float("inf"), 6.80)
    ],
    "Tamil Nadu": [
        (10, 7.36), (20, 6.30), (40, 5.42), (80, 4.66), (float("inf"), 4.26)
    ],
    "Karnataka": [
        (10, 7.80), (25, 6.50), (50, 5.20), (float("inf"), 4.50)
    ],
    "Maharashtra": [
        (10, 8.20), (30, 6.70), (60, 5.60), (float("inf"), 4.80)
    ],
    "Rajasthan": [
        (10, 6.80), (30, 5.40), (70, 4.40), (float("inf"), 3.90)
    ],
    "Odisha": [
        (10, 5.80), (30, 4.80), (80, 3.90), (float("inf"), 3.20)
    ],
    "Chhattisgarh": [
        (10, 5.50), (30, 4.60), (80, 3.80), (float("inf"), 3.20)
    ],
    "Delhi NCR": [
        (10, 8.50), (20, 7.10), (40, 6.00), (float("inf"), 5.10)
    ],
    # Default CPWD Lead Scale for all other states
    "DEFAULT": [
        (10, 7.36), (20, 6.30), (40, 5.42), (80, 4.66), (float("inf"), 4.26)
    ]
}

def get_state_prescribed_freight(state, lead_km):
    brackets = STATE_FREIGHT_RULES.get(state, STATE_FREIGHT_RULES["DEFAULT"])
    total_freight = 0.0
    rem_lead = lead_km
    prev_limit = 0.0
    
    for limit, rate in brackets:
        interval = min(rem_lead, limit - prev_limit)
        if interval > 0:
            total_freight += interval * rate
            rem_lead -= interval
            prev_limit = limit
        if rem_lead <= 0:
            break
    return round(total_freight, 2)

if __name__ == "__main__":
    test_lead = 30.0
    print("=" * 70)
    print(f"STATE-SPECIFIC PRESCRIBED CONVEYANCE COMPARISON ({test_lead} KM LEAD)")
    print("=" * 70)
    for st in ["Kerala", "Tamil Nadu", "Rajasthan", "Odisha", "Delhi NCR"]:
        f_cost = get_state_prescribed_freight(st, test_lead)
        print(f" {st:<22}: INR {f_cost:.2f} / MT")
