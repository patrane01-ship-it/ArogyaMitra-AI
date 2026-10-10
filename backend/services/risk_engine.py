"""
ArogyaMitra AI - Risk Scoring Engine
Rule-based health risk computation and contributing factor weighting.
Per FEATURES.md §3 (Feature 3).
"""

from typing import List, Dict, Any, Tuple
from backend.models.risk_score import RiskScore, RiskLevel


class RiskEngine:
    """Computes overall risk and contributing factor analysis from clinical parameters."""

    CONTRIBUTION_WEIGHTS = {
        "CRITICAL": 0.25,
        "HIGH": 0.15,
        "LOW": 0.10,
        "NORMAL": 0.0,
    }

    @classmethod
    def calculate_risk(cls, parameters: List[Dict[str, Any]]) -> Tuple[float, str, List[Dict[str, Any]], List[str]]:
        """
        Calculates:
        - overall_risk: float (0.0 to 1.0)
        - risk_level: str ("LOW", "MODERATE", "HIGH", "CRITICAL")
        - contributing_factors: list of dicts with param details
        - recommendations: list of actionable insights
        """
        if not parameters:
            return 0.0, RiskLevel.LOW.value, [], ["Upload lab reports to generate personalized recommendations."]

        total_score = 0.0
        contributing_factors = []
        recommendations = []

        for p in parameters:
            name = p.get("param_name") or p.get("name", "Unknown")
            status = p.get("status", "NORMAL").upper()
            val = p.get("value")
            unit = p.get("unit", "")
            
            weight = cls.CONTRIBUTION_WEIGHTS.get(status, 0.0)
            if weight > 0:
                total_score += weight
                contributing_factors.append({
                    "param_name": name,
                    "value": val,
                    "unit": unit,
                    "status": status,
                    "weight": weight,
                    "contribution": round(weight, 3),
                })

                # Clinical heuristic recommendation
                if status == "CRITICAL":
                    recommendations.append(f"Immediate medical consultation advised for critically abnormal {name} ({val} {unit}).")
                elif status == "HIGH":
                    recommendations.append(f"Monitor and review elevated {name} ({val} {unit}) with your physician.")
                elif status == "LOW":
                    recommendations.append(f"Low reading noted for {name} ({val} {unit}); consider lifestyle and dietary check.")

        overall_risk = min(round(total_score, 4), 1.0)
        risk_level = RiskScore.compute_risk_level(overall_risk)

        # Sort contributing factors by highest impact
        contributing_factors.sort(key=lambda x: x["weight"], reverse=True)

        if not recommendations:
            recommendations.append("All tracked clinical parameters are currently within normal baseline ranges.")

        return overall_risk, risk_level, contributing_factors, recommendations
