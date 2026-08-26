"""
SMART-SHIELD v3.0 Extended Kalman Filter (EKF) Sensor Fusion
Fuses 2D optical bounding box centroids with 3D mmWave radar polar/cartesian vectors.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple

class TargetEKFFilter:
    """
    State vector x = [X, Y, Z, Vx, Vy, Vz]^T
    Fuses:
      - Radar measurements: [Range r, Azimuth theta, Radial Velocity vr]
      - Camera measurements: [Pixel u, Pixel v]
    """
    def __init__(self, init_x: float, init_y: float, init_z: float = 15.0, init_vx: float = 0.0, init_vy: float = -10.0, init_vz: float = 0.0):
        # State vector [X, Y, Z, Vx, Vy, Vz]
        self.x = np.array([init_x, init_y, init_z, init_vx, init_vy, init_vz], dtype=float)
        
        # State covariance P
        self.P = np.diag([5.0, 5.0, 5.0, 2.0, 2.0, 2.0])
        
        # Process noise Q
        self.Q = np.diag([0.2, 0.2, 0.2, 0.5, 0.5, 0.5])
        
        # Measurement noise R for Radar [r, theta, vr]
        self.R_radar = np.diag([1.0, math.radians(2.0)**2, 0.8])
        
        # Measurement noise R for Camera [u, v]
        self.R_cam = np.diag([4.0, 4.0])

    def predict(self, dt: float = 0.033):
        """State transition update: x_k = F * x_{k-1}"""
        F = np.eye(6)
        F[0, 3] = dt
        F[1, 4] = dt
        F[2, 5] = dt
        
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q

    def update_radar(self, r_meas: float, theta_rad_meas: float, vr_meas: float):
        """EKF non-linear update for radar polar coordinates."""
        px, py, pz, vx, vy, vz = self.x
        r_pred = math.sqrt(px**2 + py**2 + pz**2)
        if r_pred < 0.01:
            return

        theta_pred = math.atan2(px, py)
        vr_pred = (px * vx + py * vy + pz * vz) / r_pred

        # Measurement residual y
        z = np.array([r_meas, theta_rad_meas, vr_meas])
        h_x = np.array([r_pred, theta_pred, vr_pred])
        y = z - h_x

        # Jacobian Matrix H
        H = np.zeros((3, 6))
        # dr / d[px, py, pz]
        H[0, 0] = px / r_pred
        H[0, 1] = py / r_pred
        H[0, 2] = pz / r_pred

        # dtheta / d[px, py]
        d_denom = px**2 + py**2
        if d_denom > 0.01:
            H[1, 0] = py / d_denom
            H[1, 1] = -px / d_denom

        # dvr / d[x, v]
        H[2, 0] = (vx * r_pred - (px * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 1] = (vy * r_pred - (py * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 2] = (vz * r_pred - (pz * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 3] = px / r_pred
        H[2, 4] = py / r_pred
        H[2, 5] = pz / r_pred

        # Kalman Gain K
        S = H @ self.P @ H.T + self.R_radar
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(6) - K @ H) @ self.P

    def get_fused_state(self) -> Dict[str, float]:
        px, py, pz, vx, vy, vz = self.x
        distance = math.sqrt(px**2 + py**2 + pz**2)
        azimuth_deg = math.degrees(math.atan2(px, py))
        speed = math.sqrt(vx**2 + vy**2 + vz**2)
        return {
            "x_m": round(float(px), 2),
            "y_m": round(float(py), 2),
            "z_m": round(float(pz), 2),
            "vx_ms": round(float(vx), 2),
            "vy_ms": round(float(vy), 2),
            "vz_ms": round(float(vz), 2),
            "distance_m": round(float(distance), 2),
            "azimuth_deg": round(float(azimuth_deg), 2),
            "speed_ms": round(float(speed), 2)
        }
