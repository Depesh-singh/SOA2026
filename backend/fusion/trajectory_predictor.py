"""
SMART-SHIELD v3.0 Trajectory & Intercept Predictor
Projects future 3D multi-target flight paths, Closest Point of Approach (CPA), and Time-to-Impact (TTI).
"""

import math
from typing import List, Dict, Any, Tuple, Optional

class TrajectoryPredictor:
    """Predicts future target positions and computes tactical intercept / threat metrics."""
    def __init__(self, default_horizon_seconds: float = 3.0, step_dt: float = 0.5):
        self.default_horizon = default_horizon_seconds
        self.step_dt = step_dt

    def predict_future_trajectory(
        self,
        x_m: float,
        y_m: float,
        z_m: float,
        vx_ms: float,
        vy_ms: float,
        vz_ms: float = 0.0,
        horizon_s: Optional[float] = None,
        base_uncertainty_m: float = 2.0
    ) -> List[Dict[str, float]]:
        """
        Projects future (x, y, z) waypoints over time using a Constant Velocity (CV) kinematic motion model.
        Returns a list of timestamped waypoints {t_sec, x_m, y_m, z_m, distance_m, azimuth_deg, uncertainty_m}.
        """
        horizon = horizon_s or self.default_horizon
        waypoints = []
        num_steps = max(1, int(round(horizon / self.step_dt)))

        for step in range(1, num_steps + 1):
            t = round(step * self.step_dt, 2)
            fut_x = x_m + (vx_ms * t)
            fut_y = y_m + (vy_ms * t)
            fut_z = max(0.0, z_m + (vz_ms * t))
            fut_dist = math.sqrt(fut_x**2 + fut_y**2 + fut_z**2)
            fut_az = math.degrees(math.atan2(fut_x, fut_y))
            # Uncertainty expands linearly with prediction time
            uncertainty = round(base_uncertainty_m + (0.5 * t), 2)

            waypoints.append({
                "t_sec": t,
                "x_m": round(fut_x, 2),
                "y_m": round(fut_y, 2),
                "z_m": round(fut_z, 2),
                "distance_m": round(fut_dist, 2),
                "azimuth_deg": round(fut_az, 2),
                "uncertainty_m": uncertainty
            })

        return waypoints

    def check_protected_zone_approach(
        self,
        waypoints: List[Dict[str, float]],
        zone_radius_m: float = 50.0
    ) -> Dict[str, Any]:
        """
        Evaluates whether the projected future trajectory penetrates the protected base perimeter.
        """
        for wp in waypoints:
            ground_dist = math.sqrt(wp["x_m"]**2 + wp["y_m"]**2)
            if ground_dist <= zone_radius_m:
                return {
                    "is_breaching": True,
                    "tti_sec": wp["t_sec"],
                    "breach_distance_m": round(ground_dist, 1),
                    "zone_radius_m": zone_radius_m
                }

        return {
            "is_breaching": False,
            "tti_sec": None,
            "breach_distance_m": None,
            "zone_radius_m": zone_radius_m
        }

    def calculate_closest_point_of_approach(
        self,
        x_m: float,
        y_m: float,
        z_m: float,
        vx_ms: float,
        vy_ms: float,
        vz_ms: float = 0.0
    ) -> Dict[str, float]:
        """
        Computes Closest Point of Approach (CPA):
        t_CPA = - (r . v) / ||v||^2
        d_CPA = || r + v * t_CPA ||
        """
        v_sq = vx_ms**2 + vy_ms**2 + vz_ms**2
        speed = math.sqrt(v_sq)

        if speed < 0.1:
            curr_dist = math.sqrt(x_m**2 + y_m**2 + z_m**2)
            return {
                "t_cpa_sec": 0.0,
                "d_cpa_m": round(curr_dist, 2),
                "is_inbound": False,
                "closure_rate_ms": 0.0
            }

        # Dot product r . v
        r_dot_v = (x_m * vx_ms) + (y_m * vy_ms) + (z_m * vz_ms)
        curr_dist = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        closure_rate = r_dot_v / curr_dist  # Negative means closing in

        t_cpa = - r_dot_v / v_sq
        is_inbound = (t_cpa > 0.0)

        if is_inbound:
            cpa_x = x_m + (vx_ms * t_cpa)
            cpa_y = y_m + (vy_ms * t_cpa)
            cpa_z = z_m + (vz_ms * t_cpa)
            d_cpa = math.sqrt(cpa_x**2 + cpa_y**2 + cpa_z**2)
        else:
            t_cpa = 0.0
            d_cpa = curr_dist

        return {
            "t_cpa_sec": round(t_cpa, 2),
            "d_cpa_m": round(d_cpa, 2),
            "is_inbound": is_inbound,
            "closure_rate_ms": round(closure_rate, 2)
        }
