"""
SMART-SHIELD v3.0 Sensor Fusion Engine
Coordinates multi-sensor fusion across mmWave Radar and Optical Camera.
"""

from typing import Dict, List, Any, Optional
from .ekf import TargetEKFFilter
from .threat_matrix import ThreatEvaluationEngine
from .trajectory_predictor import TrajectoryPredictor

class SensorFusionEngine:
    """Orchestrates multi-sensor data fusion combining Radar, Camera, and EKF filtering."""
    def __init__(self):
        self.ekf_filters: Dict[str, TargetEKFFilter] = {}
        self.threat_engine = ThreatEvaluationEngine()
        self.trajectory_predictor = TrajectoryPredictor()

    def get_or_create_filter(self, target_id: str, init_x: float, init_y: float, init_z: float = 15.0, init_vx: float = 0.0, init_vy: float = -10.0, init_vz: float = 0.0) -> TargetEKFFilter:
        if target_id not in self.ekf_filters:
            self.ekf_filters[target_id] = TargetEKFFilter(init_x, init_y, init_z, init_vx, init_vy, init_vz)
        return self.ekf_filters[target_id]

    def fuse_target(self, target_data: Dict[str, Any], dt: float = 0.033) -> Dict[str, Any]:
        """Runs EKF prediction, updates with radar measurements, and returns fused state."""
        tid = target_data.get("id", "DRONE-01")
        ekf = self.get_or_create_filter(
            target_id=tid,
            init_x=target_data.get("x_m", 0.0),
            init_y=target_data.get("y_m", 50.0),
            init_z=target_data.get("z_m", 15.0),
            init_vx=target_data.get("vx_ms", 0.0),
            init_vy=target_data.get("vy_ms", -10.0),
            init_vz=target_data.get("vz_ms", 0.0)
        )

        # 1. State prediction
        ekf.predict(dt=dt)

        # 2. Update with radar if available
        r = target_data.get("distance_m", 50.0)
        theta_rad = target_data.get("azimuth_deg", 0.0) * (3.14159 / 180.0)
        vr = target_data.get("speed_ms", -15.0)
        ekf.update_radar(r_meas=r, theta_rad_meas=theta_rad, vr_meas=vr)

        # 3. Retrieve fused kinematics
        fused = ekf.get_fused_state()

        # 4. Trajectory forward projection & CPA
        cpa = self.trajectory_predictor.calculate_closest_point_of_approach(
            fused["x_m"], fused["y_m"], fused["z_m"],
            fused["vx_ms"], fused["vy_ms"], fused["vz_ms"]
        )

        return {
            **target_data,
            **fused,
            "cpa": cpa
        }

def fuse_velocities_weighted(
    v_camera: Optional[float],
    v_radar: Optional[float],
    w_camera: float = 0.4,
    w_radar: float = 0.6,
    disagreement_threshold: float = 15.0
) -> float:
    """
    Combines radar and camera velocity estimates using a confidence-weighted average:
    V_final = (w_r * V_radar + w_c * V_camera) / (w_r + w_c)
    Includes disagreement detection and handles single-sensor dropouts.
    """
    if v_camera is None and v_radar is None:
        return 0.0
    if v_camera is None:
        return float(v_radar)
    if v_radar is None:
        return float(v_camera)

    # Disagreement / outlier detection
    diff = abs(v_camera - v_radar)
    if diff > disagreement_threshold:
        # Heavily favor radar Doppler velocity as ground-truth when large disparity occurs
        w_radar = 0.9
        w_camera = 0.1

    v_final = (w_radar * v_radar + w_camera * v_camera) / (w_radar + w_camera)
    return round(float(v_final), 2)

