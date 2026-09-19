CITY_TIER_DATABASE = {
    "Maharashtra": {
        "Mumbai (MMR)": {"tier": "Tier-1 Metro", "tier_multiplier": 1.045, "octroi_cess_inr": 450.0, "local_handling_inr": 180.0},
        "Pune": {"tier": "Tier-1 Urban", "tier_multiplier": 1.025, "octroi_cess_inr": 250.0, "local_handling_inr": 140.0},
        "Nagpur": {"tier": "Tier-2 Hub", "tier_multiplier": 0.990, "octroi_cess_inr": 100.0, "local_handling_inr": 100.0},
        "Nashik": {"tier": "Tier-2 Hub", "tier_multiplier": 0.995, "octroi_cess_inr": 120.0, "local_handling_inr": 110.0},
        "Jalna (Mandi Hub)": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.960, "octroi_cess_inr": 0.0, "local_handling_inr": 80.0},
    },
    "Kerala": {
        "Kochi / Ernakulam": {"tier": "Tier-1 Urban", "tier_multiplier": 1.035, "octroi_cess_inr": 300.0, "local_handling_inr": 190.0},
        "Thiruvananthapuram": {"tier": "Tier-2 Hub", "tier_multiplier": 1.020, "octroi_cess_inr": 200.0, "local_handling_inr": 160.0},
        "Kozhikode": {"tier": "Tier-2 Hub", "tier_multiplier": 1.015, "octroi_cess_inr": 180.0, "local_handling_inr": 150.0},
        "Thrissur": {"tier": "Tier-2 Hub", "tier_multiplier": 1.005, "octroi_cess_inr": 120.0, "local_handling_inr": 140.0},
        "Palakkad (Corridor)": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.980, "octroi_cess_inr": 50.0, "local_handling_inr": 110.0},
    },
    "Delhi NCR": {
        "Central Delhi / New Delhi": {"tier": "Tier-1 Metro", "tier_multiplier": 1.050, "octroi_cess_inr": 550.0, "local_handling_inr": 220.0},
        "Noida / Greater Noida": {"tier": "Tier-1 Urban", "tier_multiplier": 1.020, "octroi_cess_inr": 200.0, "local_handling_inr": 160.0},
        "Gurugram": {"tier": "Tier-1 Urban", "tier_multiplier": 1.030, "octroi_cess_inr": 280.0, "local_handling_inr": 180.0},
        "Faridabad": {"tier": "Tier-2 Hub", "tier_multiplier": 0.990, "octroi_cess_inr": 120.0, "local_handling_inr": 130.0},
    },
    "Karnataka": {
        "Bengaluru Urban": {"tier": "Tier-1 Metro", "tier_multiplier": 1.040, "octroi_cess_inr": 400.0, "local_handling_inr": 180.0},
        "Mysuru": {"tier": "Tier-2 Hub", "tier_multiplier": 0.995, "octroi_cess_inr": 150.0, "local_handling_inr": 120.0},
        "Hubballi-Dharwad": {"tier": "Tier-2 Hub", "tier_multiplier": 0.985, "octroi_cess_inr": 100.0, "local_handling_inr": 110.0},
        "Mangaluru": {"tier": "Tier-2 Port Hub", "tier_multiplier": 1.010, "octroi_cess_inr": 160.0, "local_handling_inr": 140.0},
    },
    "Tamil Nadu": {
        "Chennai Metro": {"tier": "Tier-1 Metro", "tier_multiplier": 1.040, "octroi_cess_inr": 380.0, "local_handling_inr": 170.0},
        "Coimbatore": {"tier": "Tier-2 Hub", "tier_multiplier": 1.010, "octroi_cess_inr": 160.0, "local_handling_inr": 130.0},
        "Madurai": {"tier": "Tier-2 Hub", "tier_multiplier": 0.990, "octroi_cess_inr": 100.0, "local_handling_inr": 120.0},
        "Salem (Steel Cluster)": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.970, "octroi_cess_inr": 50.0, "local_handling_inr": 90.0},
    },
    "Rajasthan": {
        "Jaipur": {"tier": "Tier-1 Urban", "tier_multiplier": 1.025, "octroi_cess_inr": 220.0, "local_handling_inr": 140.0},
        "Jodhpur": {"tier": "Tier-2 Hub", "tier_multiplier": 0.995, "octroi_cess_inr": 110.0, "local_handling_inr": 110.0},
        "Udaipur": {"tier": "Tier-2 Hub", "tier_multiplier": 1.000, "octroi_cess_inr": 120.0, "local_handling_inr": 120.0},
        "Kota": {"tier": "Tier-2 Hub", "tier_multiplier": 0.985, "octroi_cess_inr": 90.0, "local_handling_inr": 100.0},
        "Chittorgarh (Cement Belt)": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.950, "octroi_cess_inr": 0.0, "local_handling_inr": 70.0},
    },
    "DEFAULT": {
        "State Capital / Metro": {"tier": "Tier-1 Urban", "tier_multiplier": 1.030, "octroi_cess_inr": 250.0, "local_handling_inr": 150.0},
        "Tier-2 Industrial City": {"tier": "Tier-2 Hub", "tier_multiplier": 1.000, "octroi_cess_inr": 100.0, "local_handling_inr": 110.0},
        "Tier-3 District Outpost": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.970, "octroi_cess_inr": 0.0, "local_handling_inr": 80.0},
    }
}

def get_cities_for_state(state):
    clean_st = str(state).strip()
    return CITY_TIER_DATABASE.get(clean_st, CITY_TIER_DATABASE["DEFAULT"])

def get_city_profile(state, city):
    state_cities = get_cities_for_state(state)
    if city in state_cities:
        return state_cities[city]
    return next(iter(state_cities.values()))


# --- EXPANDED ALL-INDIA TIER REGISTRY ---
ALL_INDIA_DEFAULTS = {
    "Andhra Pradesh": {
        "Visakhapatnam": {"tier": "Tier-1 Port Urban", "tier_multiplier": 1.03, "octroi_cess_inr": 250.0, "local_handling_inr": 180.0},
        "Vijayawada": {"tier": "Tier-2 Commercial", "tier_multiplier": 1.015, "octroi_cess_inr": 180.0, "local_handling_inr": 150.0},
        "Guntur": {"tier": "Tier-2 Hub", "tier_multiplier": 1.01, "octroi_cess_inr": 150.0, "local_handling_inr": 140.0},
        "Tirupati (Corridor)": {"tier": "Tier-3 Outpost", "tier_multiplier": 0.99, "octroi_cess_inr": 80.0, "local_handling_inr": 120.0}
    },
    "Telangana": {
        "Hyderabad": {"tier": "Tier-1 Metro", "tier_multiplier": 1.04, "octroi_cess_inr": 300.0, "local_handling_inr": 200.0},
        "Warangal": {"tier": "Tier-2 Regional", "tier_multiplier": 1.01, "octroi_cess_inr": 160.0, "local_handling_inr": 140.0},
        "Nizamabad": {"tier": "Tier-3 Urban", "tier_multiplier": 0.995, "octroi_cess_inr": 120.0, "local_handling_inr": 130.0},
        "Khammam (Corridor)": {"tier": "Tier-3 Corridor", "tier_multiplier": 0.985, "octroi_cess_inr": 70.0, "local_handling_inr": 110.0}
    },
    "Gujarat": {
        "Ahmedabad": {"tier": "Tier-1 Urban", "tier_multiplier": 1.035, "octroi_cess_inr": 280.0, "local_handling_inr": 190.0},
        "Surat": {"tier": "Tier-1 Industrial", "tier_multiplier": 1.03, "octroi_cess_inr": 270.0, "local_handling_inr": 185.0},
        "Vadodara": {"tier": "Tier-2 Regional", "tier_multiplier": 1.015, "octroi_cess_inr": 180.0, "local_handling_inr": 150.0},
        "Rajkot (Corridor)": {"tier": "Tier-2 Corridor", "tier_multiplier": 1.00, "octroi_cess_inr": 120.0, "local_handling_inr": 130.0}
    },
    "Uttar Pradesh": {
        "Noida / Greater Noida": {"tier": "Tier-1 NCR Metro", "tier_multiplier": 1.045, "octroi_cess_inr": 320.0, "local_handling_inr": 210.0},
        "Lucknow": {"tier": "Tier-1 Capital", "tier_multiplier": 1.025, "octroi_cess_inr": 220.0, "local_handling_inr": 170.0},
        "Kanpur": {"tier": "Tier-2 Industrial", "tier_multiplier": 1.015, "octroi_cess_inr": 190.0, "local_handling_inr": 160.0},
        "Varanasi (Corridor)": {"tier": "Tier-3 Eastern Corridor", "tier_multiplier": 0.99, "octroi_cess_inr": 90.0, "local_handling_inr": 125.0}
    },
    "West Bengal": {
        "Kolkata": {"tier": "Tier-1 Metro", "tier_multiplier": 1.035, "octroi_cess_inr": 300.0, "local_handling_inr": 195.0},
        "Howrah": {"tier": "Tier-2 Industrial", "tier_multiplier": 1.02, "octroi_cess_inr": 210.0, "local_handling_inr": 165.0},
        "Durgapur": {"tier": "Tier-2 Steel City", "tier_multiplier": 1.005, "octroi_cess_inr": 140.0, "local_handling_inr": 140.0},
        "Siliguri (Corridor)": {"tier": "Tier-3 North Corridor", "tier_multiplier": 0.985, "octroi_cess_inr": 80.0, "local_handling_inr": 120.0}
    }
}

for k, v in ALL_INDIA_DEFAULTS.items():
    if k not in CITY_TIER_DATABASE:
        CITY_TIER_DATABASE[k] = v

def get_all_supported_states():
    return sorted(list([k for k in CITY_TIER_DATABASE.keys() if k != "DEFAULT"]))
