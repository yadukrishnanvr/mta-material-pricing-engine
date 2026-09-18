import os
import sqlite3
import pandas as pd
import numpy as np

class Clause10CAEscalationEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    def calculate_price_variation(self, base_contract_value: float, base_wpi: float, current_wpi: float, material_coefficient: float = 0.85):
        """
        Computes CPWD Clause 10CA material price variation:
        Vm = P * Q * (W - W0) / W0
        where:
        - P = Material cost proportion coefficient (default 0.85 or 85%)
        - Q = Base contract value / work component value
        - W0 = Base Wholesale Price Index at tender receipt
        - W = Current Wholesale Price Index
        """
        if base_wpi <= 0:
            raise ValueError("Base WPI must be greater than zero.")
        
        wpi_drift_pct = ((current_wpi - base_wpi) / base_wpi) * 100.0
        variation_amount = base_contract_value * material_coefficient * ((current_wpi - base_wpi) / base_wpi)
        adjusted_contract_value = base_contract_value + variation_amount

        return {
            "Base Contract Value (INR)": round(base_contract_value, 2),
            "Base WPI": float(base_wpi),
            "Current WPI": float(current_wpi),
            "WPI Drift (%)": round(wpi_drift_pct, 2),
            "Material Component Coefficient": float(material_coefficient),
            "Price Variation Amount (INR)": round(variation_amount, 2),
            "Adjusted Contract Value (INR)": round(adjusted_contract_value, 2)
        }

    def project_future_escalation(self, current_contract_value: float, current_wpi: float, historical_monthly_drift_pct: float, months_ahead: int = 12):
        """
        Projects future contract price adjustments using historical compounding monthly inflation drift.
        """
        projections = []
        projected_wpi = current_wpi
        projected_value = current_contract_value

        for m in range(1, months_ahead + 1):
            projected_wpi *= (1.0 + (historical_monthly_drift_pct / 100.0))
            # Incremental variation projection
            variation = current_contract_value * 0.85 * ((projected_wpi - current_wpi) / current_wpi)
            proj_total = current_contract_value + variation

            projections.append({
                "Month Offset": m,
                "Projected WPI": round(projected_wpi, 2),
                "Projected Drift (%)": round(((projected_wpi - current_wpi) / current_wpi) * 100.0, 2),
                "Projected Escalation Amount (INR)": round(variation, 2),
                "Projected Total Value (INR)": round(proj_total, 2)
            })

        return projections
