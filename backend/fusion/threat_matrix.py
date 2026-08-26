"""
SMART-SHIELD v3.0 Threat Scoring Matrix & Prioritization Engine
Implements multi-variable mathematical threat evaluation and priority target election.
"""

import math
from typing import List, Dict, Any, Optional
from ..config import config

class ThreatEvaluationEngine:
    """Evaluates real-time threat scores (0-100) and elects primary priority targets."""
    
    @staticmethod
    def calculate_threat_score(
        distance_m: float,
        speed_ms: float,
        azimuth_deg: float,
        heading_deg: float,
        optical_confidence: float,
        classification: str,
        behavior_factor: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculates threat score S_threat in [0, 100]:
        S_threat = w1*f_D + w2*f_V + w3*f_theta + w4*C_class + w5*B_err
        """
        weights = config.threat
        
        # 1. Proximity Term f_D (Closer targets have higher threat weight)
        d_norm = max(0.0, min(1.0, distance_m / weights.max_detection_range_m))
        f_D = (1.0 - d_norm) * 100.0

        # 2. Speed / Velocity Term f_V (Faster moving targets increase threat level)
        v_norm = max(0.0, min(1.0, abs(speed_ms) / weights.max_expected_speed_ms))
        f_V = v_norm * 100.0

        # 3. Trajectory / Heading Vector Term f_theta (Heading directly towards base increases risk)
        # alpha is relative angle between target velocity vector and sensor origin
        alpha_rad = math.radians(abs(heading_deg - azimuth_deg))
        cos_alpha = math.cos(alpha_rad)
        f_theta = max(0.0, (cos_alpha + 1.0) / 2.0) * 100.0

        # 4. Classification Confidence Term C_class (Drones/Quadcopters have higher risk multiplier)
        class_multiplier = 1.0 if classification in ["Drone", "Quadcopter"] else (0.8 if classification == "Fixed-Wing" else 0.2)
        f_class = optical_confidence * class_multiplier * 100.0

        # 5. Behavior Anomaly Factor B_err (Erratic maneuvers / non-ballistic high jerk)
        f_behavior = max(0.0, min(1.0, behavior_factor)) * 100.0

        # Total Weighted Score
        raw_score = (
            weights.w_distance * f_D +
            weights.w_speed * f_V +
            weights.w_direction * f_theta +
            weights.w_confidence * f_class +
            weights.w_behavior * f_behavior
        )
        total_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Classify Threat Level
        if total_score >= weights.high_threat_threshold:
            threat_level = "HIGH"
        elif total_score >= weights.medium_threat_threshold:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"

        return {
            "threat_score": total_score,
            "threat_level": threat_level,
            "components": {
                "proximity_score": round(f_D, 1),
                "speed_score": round(f_V, 1),
                "trajectory_score": round(f_theta, 1),
                "classification_score": round(f_class, 1),
                "behavior_score": round(f_behavior, 1)
            }
        }

    @staticmethod
    def prioritize_targets(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts all active targets descending by threat score and flags Priority Target #01."""
        sorted_targets = sorted(targets, key=lambda t: t.get("threat_score", 0.0), reverse=True)
        for idx, t in enumerate(sorted_targets):
            t["priority_rank"] = idx + 1
            t["is_highest_priority"] = (idx == 0)
        return sorted_targets
