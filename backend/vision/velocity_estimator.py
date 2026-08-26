"""
SMART-SHIELD v3.0 Optical Velocity Estimator
Computes 2D pixel velocity, optical expansion rates, and metric Cartesian velocity from track history.
"""

import time
import math
from typing import List, Dict, Any, Tuple, Optional

class OpticalVelocityEstimator:
    """Estimates velocity vectors (pixel and metric) from consecutive bounding box track history."""
    def __init__(self, ema_alpha: float = 0.6, focal_length_px: float = 400.0):
        self.ema_alpha = ema_alpha
        self.focal_length_px = focal_length_px
        self.velocity_cache: Dict[str, Dict[str, float]] = {}

    def estimate_velocity_from_history(
        self,
        track_id: str,
        history_bboxes: List[List[float]],
        timestamps: Optional[List[float]] = None,
        estimated_depth_m: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Computes smoothed velocity (du/dt, dv/dt) and metric (vx, vy, vz) from track history.
        history_bboxes: List of [x1, y1, x2, y2] in chronological order (latest is last).
        """
        if not history_bboxes or len(history_bboxes) < 2:
            return {
                "vel_u_px_s": 0.0,
                "vel_v_px_s": 0.0,
                "scale_expansion_rate": 0.0,
                "vx_est_ms": 0.0,
                "vy_est_ms": 0.0,
                "vz_est_ms": 0.0,
                "speed_est_ms": 0.0
            }

        # Use latest two frames
        curr_box = history_bboxes[-1]
        prev_box = history_bboxes[-2]

        curr_cx = (curr_box[0] + curr_box[2]) / 2.0
        curr_cy = (curr_box[1] + curr_box[3]) / 2.0
        curr_size = math.sqrt((curr_box[2] - curr_box[0]) * (curr_box[3] - curr_box[1]))

        prev_cx = (prev_box[0] + prev_box[2]) / 2.0
        prev_cy = (prev_box[1] + prev_box[3]) / 2.0
        prev_size = math.sqrt((prev_box[2] - prev_box[0]) * (prev_box[3] - prev_box[1]))

        # Time delta
        dt = 0.033  # Default ~30Hz
        if timestamps and len(timestamps) >= 2:
            dt = max(0.005, min(0.5, timestamps[-1] - timestamps[-2]))

        # Instantaneous 2D pixel velocities
        raw_du = (curr_cx - prev_cx) / dt
        raw_dv = (curr_cy - prev_cy) / dt
        scale_rate = (curr_size - prev_size) / (max(prev_size, 1.0) * dt)

        # Exponential Moving Average (EMA) smoothing
        cached = self.velocity_cache.get(track_id, {"du": raw_du, "dv": raw_dv})
        smooth_du = self.ema_alpha * raw_du + (1.0 - self.ema_alpha) * cached["du"]
        smooth_dv = self.ema_alpha * raw_dv + (1.0 - self.ema_alpha) * cached["dv"]
        self.velocity_cache[track_id] = {"du": smooth_du, "dv": smooth_dv}

        # Metric velocity projection if distance / depth is provided
        # X = (u - cx) * Z / f  ==>  v_X = (du/dt * Z / f)
        # Y = Z (depth)         ==>  v_Y = - (Z * scale_rate) (approaching if expanding)
        # Z = (cy - v) * Z / f  ==>  v_Z = - (dv/dt * Z / f)
        depth = estimated_depth_m if estimated_depth_m and estimated_depth_m > 0 else 50.0
        vx_metric = (smooth_du * depth) / self.focal_length_px
        vz_metric = -(smooth_dv * depth) / self.focal_length_px
        vy_metric = -scale_rate * depth * 2.0  # Inbound radial rate from optical expansion

        speed_3d = math.sqrt(vx_metric**2 + vy_metric**2 + vz_metric**2)

        return {
            "vel_u_px_s": round(smooth_du, 1),
            "vel_v_px_s": round(smooth_dv, 1),
            "scale_expansion_rate": round(scale_rate, 3),
            "vx_est_ms": round(vx_metric, 2),
            "vy_est_ms": round(vy_metric, 2),
            "vz_est_ms": round(vz_metric, 2),
            "speed_est_ms": round(speed_3d, 2)
        }
