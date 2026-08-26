"""
SMART-SHIELD v3.0 Pan/Tilt Gimbal Closed-Loop PID Controller
Calculates servo angle adjustments to center the highest priority target in optical feed.
"""

import time
from typing import Tuple
from ..config import config

class PIDGimbalController:
    """Dual-axis PID controller for PCA9685 pan/tilt servos."""
    def __init__(self):
        cfg = config.gimbal
        self.pan_angle = cfg.pan_center_deg
        self.tilt_angle = cfg.tilt_center_deg

        self.kp_pan = cfg.kp_pan
        self.ki_pan = cfg.ki_pan
        self.kd_pan = cfg.kd_pan

        self.kp_tilt = cfg.kp_tilt
        self.ki_tilt = cfg.ki_tilt
        self.kd_tilt = cfg.kd_tilt

        self.prev_error_x = 0.0
        self.integral_x = 0.0
        self.prev_error_y = 0.0
        self.integral_y = 0.0
        self.last_time = time.time()
        self.auto_track_enabled = True

    def reset_integrators(self):
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0

    def compute_tracking_angles(
        self,
        target_center_u: float,
        target_center_v: float,
        frame_width: int = 640,
        frame_height: int = 460
    ) -> Tuple[float, float]:
        """Calculates updated Pan and Tilt angles based on optical pixel offset from center."""
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_time))
        self.last_time = now

        if not self.auto_track_enabled:
            return self.pan_angle, self.tilt_angle

        # Pixel error relative to optical center
        error_x = target_center_u - (frame_width / 2.0)
        error_y = (frame_height / 2.0) - target_center_v  # Inverted for elevation

        # Pan axis PID
        self.integral_x += error_x * dt
        derivative_x = (error_x - self.prev_error_x) / dt
        self.prev_error_x = error_x
        pan_correction = (self.kp_pan * error_x) + (self.ki_pan * self.integral_x) + (self.kd_pan * derivative_x)

        # Tilt axis PID
        self.integral_y += error_y * dt
        derivative_y = (error_y - self.prev_error_y) / dt
        self.prev_error_y = error_y
        tilt_correction = (self.kp_tilt * error_y) + (self.ki_tilt * self.integral_y) + (self.kd_tilt * derivative_y)

        # Apply corrections to current angles (constrained by hardware limits)
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, self.pan_angle + pan_correction))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, self.tilt_angle + tilt_correction))

        return round(self.pan_angle, 1), round(self.tilt_angle, 1)

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        """Allows direct operator manual joystick control."""
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, pan_deg))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, tilt_deg))
        self.reset_integrators()
