"""
SMART-SHIELD v3.0 Pan/Tilt Gimbal & Servo Tracking Controller
Supports:
1. PROPORTIONAL Mode (Stationary turret / webcam pointer):
   Directly maps the target's horizontal pixel position to an absolute angle (e.g. 40 deg to 140 deg).
   When no drone is detected, smoothly returns to 90.0 deg center and stays completely still.
2. CLOSED_LOOP PID Mode (For camera mounted on moving servo horn).
"""

import time
import math
from typing import Tuple, Optional
from ..config import config

class PIDGimbalController:
    """Gimbal & Servo tracking controller."""
    def __init__(self):
        cfg = config.gimbal
        self.pan_angle = cfg.pan_center_deg
        self.tilt_angle = cfg.tilt_center_deg
        self.target_pan = cfg.pan_center_deg
        self.target_tilt = cfg.tilt_center_deg

        # PID parameters
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
        self.last_target_time = 0.0
        self.auto_track_enabled = True
        self.invert_pan = getattr(cfg, "invert_pan", True)  # True tracks directly towards drone

        # Filter settings
        self.deadband_px = 12.0       # Ignore pixel movement within +/- 12px to stop jitter
        self.smoothing_alpha = 0.35   # Exponential smoothing factor (0.0 to 1.0)
        self.fov_span_deg = 50.0      # Max pan offset from center (+/- 50 deg -> 40 deg to 140 deg)

    def reset_integrators(self):
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0

    def compute_proportional_angles(
        self,
        target_center_u: Optional[float],
        target_center_v: Optional[float],
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Tuple[float, float, bool]:
        """
        Direct absolute mapping for stationary webcam tracking.
        Maps pixel offset -> absolute servo angle (40 deg - 140 deg).
        Returns: (pan_deg, tilt_deg, has_active_target)
        """
        now = time.time()
        cfg = config.gimbal

        if not self.auto_track_enabled:
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), False

        # 1. Target is active in the frame
        if target_center_u is not None and target_center_v is not None:
            self.last_target_time = now
            center_x = frame_width / 2.0
            error_x = target_center_u - center_x

            # Deadband filter: if within deadband, do not alter target angle
            if abs(error_x) < self.deadband_px:
                normalized_x = 0.0
            else:
                # Normalize to range [-1.0, +1.0]
                normalized_x = (error_x / center_x)

            # Apply pan inversion if needed
            if self.invert_pan:
                normalized_x = -normalized_x

            # Absolute target angle: 90.0 +/- (normalized_x * fov_span)
            raw_target_pan = cfg.pan_center_deg + (normalized_x * self.fov_span_deg)
            self.target_pan = max(cfg.pan_min_deg + 10.0, min(cfg.pan_max_deg - 10.0, raw_target_pan))

            # Exponential smoothing to prevent rapid jerky motion
            self.pan_angle = (self.smoothing_alpha * self.target_pan) + ((1.0 - self.smoothing_alpha) * self.pan_angle)
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), True

        # 2. No target detected in frame
        # If no target for > 0.6 seconds, smoothly decay back to 90.0 deg center
        time_since_target = now - self.last_target_time
        if time_since_target > 0.6:
            self.target_pan = cfg.pan_center_deg
            # Smoothly drift back to center
            if abs(self.pan_angle - cfg.pan_center_deg) > 0.5:
                self.pan_angle = (0.2 * cfg.pan_center_deg) + (0.8 * self.pan_angle)
            else:
                self.pan_angle = cfg.pan_center_deg

        return round(self.pan_angle, 1), round(self.tilt_angle, 1), False

    def compute_tracking_angles(
        self,
        target_center_u: float,
        target_center_v: float,
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Tuple[float, float]:
        """Backward compatibility wrapper delegating to proportional tracker."""
        pan, tilt, _ = self.compute_proportional_angles(
            target_center_u, target_center_v, frame_width, frame_height
        )
        return pan, tilt

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        """Allows direct operator manual control."""
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, pan_deg))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, tilt_deg))
        self.target_pan = self.pan_angle
        self.target_tilt = self.tilt_angle
        self.reset_integrators()

    def toggle_invert(self) -> bool:
        self.invert_pan = not self.invert_pan
        return self.invert_pan
