"""
SMART-SHIELD v3.0 Pan/Tilt Gimbal & Active Target Lock Controller
Implements:
1. CAMERA_MOUNTED Active Visual Servoing (Default for webcam mounted on servo):
   - Continuously centers the locked drone in the optical crosshairs (cx=320, cy=240).
   - If the drone moves right, the camera pans right to follow it frame-by-frame.
   - Damped PD controller with velocity coasting: if detection drops for a few frames,
     maintains rotation speed in the drone's direction of flight until re-acquired.
   - When target is centered (within deadband), holds steady with zero motor jitter.
2. TURRET_POINTER Mode (For stationary camera with external pointer).
"""

import time
import math
from typing import Tuple, Optional, Dict, Any
from ..config import config

class PIDGimbalController:
    """Active Drone Target Lock & Visual Servoing Controller."""
    def __init__(self):
        cfg = config.gimbal
        self.pan_angle: float = cfg.pan_center_deg
        self.tilt_angle: float = cfg.tilt_center_deg
        self.target_pan: float = cfg.pan_center_deg
        self.target_tilt: float = cfg.tilt_center_deg

        # Tracking Mode: "CAMERA_MOUNTED" (closed-loop auto-centering) or "TURRET_POINTER" (absolute mapping)
        self.mode: str = "CAMERA_MOUNTED"
        self.auto_track_enabled: bool = True
        self.invert_pan: bool = getattr(cfg, "invert_pan", False)

        # Target Lock State
        self.locked_track_id: Optional[int] = None
        self.is_locked: bool = False
        self.last_target_time: float = 0.0
        self.lost_frames: int = 0
        self.max_coast_frames: int = 25  # Coast for up to ~0.8s during occlusions
        self.last_cx: float = 320.0
        self.last_cy: float = 240.0
        self.velocity_cx: float = 0.0  # Pixels/sec

        # Visual Servoing Tuning (for webcam mounted on MG996R servo)
        self.kp_pan: float = 0.038    # Proportional gain: degrees per pixel error
        self.kd_pan: float = 0.009    # Derivative damping: suppresses overshoot
        self.ki_pan: float = 0.0004   # Integral gain for steady alignment
        self.max_slew_rate: float = 3.5  # Max degrees per 50ms update (~70 deg/s max)

        self.prev_error_x: float = 0.0
        self.integral_x: float = 0.0
        self.deadband_px: float = 8.0  # Precision deadband: within +/-8px, hold steady
        self.last_update_time: float = time.time()

    def reset_integrators(self):
        self.integral_x = 0.0
        self.prev_error_x = 0.0
        self.velocity_cx = 0.0
        self.lost_frames = 0

    def lock_target(self, track_id: int):
        """Explicitly lock onto a specific track ID."""
        self.locked_track_id = int(track_id)
        self.is_locked = True
        self.reset_integrators()

    def unlock_target(self):
        """Release target lock to allow auto-selecting the highest threat target."""
        self.locked_track_id = None
        self.is_locked = False
        self.reset_integrators()

    def toggle_mode(self) -> str:
        """Toggle between CAMERA_MOUNTED and TURRET_POINTER modes."""
        self.mode = "TURRET_POINTER" if self.mode == "CAMERA_MOUNTED" else "CAMERA_MOUNTED"
        self.reset_integrators()
        return self.mode

    def toggle_invert(self) -> bool:
        """Toggle pan rotation direction."""
        self.invert_pan = not self.invert_pan
        return self.invert_pan

    def update_tracking(
        self,
        targets: list,
        primary_target: Optional[dict],
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Main tracking loop called on every video frame.
        Calculates optimal servo pan angle to keep the drone locked and centered.
        Returns: (pan_deg, tilt_deg, lock_telemetry_dict)
        """
        now = time.time()
        dt = max(0.005, min(0.1, now - self.last_update_time))
        self.last_update_time = now
        cfg = config.gimbal

        if not self.auto_track_enabled:
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self.get_telemetry_state()

        # 1. Select the active target to track
        target_to_track = None
        if self.locked_track_id is not None:
            # Look for the user-locked target
            for t in targets:
                if t.get("track_id") == self.locked_track_id:
                    target_to_track = t
                    break
        
        # Fallback to primary / highest threat target
        if target_to_track is None and primary_target is not None:
            target_to_track = primary_target
            self.locked_track_id = target_to_track.get("track_id")

        # -------------------------------------------------------------
        # CASE A: TARGET IS VISIBLE IN CURRENT FRAME
        # -------------------------------------------------------------
        if target_to_track is not None and "center_u" in target_to_track:
            self.is_locked = True
            self.last_target_time = now
            self.lost_frames = 0
            cx = float(target_to_track["center_u"])
            cy = float(target_to_track.get("center_v", 240.0))

            # Compute horizontal pixel velocity
            if dt > 0.001:
                self.velocity_cx = (cx - self.last_cx) / dt
            self.last_cx = cx
            self.last_cy = cy

            center_x = frame_width / 2.0
            error_x = cx - center_x

            # Deadband check: if centered within deadband, keep current angle steady
            if abs(error_x) <= self.deadband_px:
                error_x = 0.0

            if self.invert_pan:
                error_x = -error_x

            # --- MODE 1: CAMERA_MOUNTED (Closed-Loop Visual Servoing) ---
            if self.mode == "CAMERA_MOUNTED":
                # Integral with anti-windup clamp
                self.integral_x += error_x * dt
                self.integral_x = max(-40.0, min(40.0, self.integral_x))

                # Derivative
                derivative_x = (error_x - self.prev_error_x) / dt if dt > 0 else 0.0
                self.prev_error_x = error_x

                # Visual servoing adjustment: pan step to center the target
                delta_pan = (self.kp_pan * error_x) + (self.ki_pan * self.integral_x) + (self.kd_pan * derivative_x)

                # Clamp max speed to ensure smooth motor movement
                delta_pan = max(-self.max_slew_rate, min(self.max_slew_rate, delta_pan))

                # Apply adjustment to current servo angle
                self.pan_angle = max(cfg.pan_min_deg + 5.0, min(cfg.pan_max_deg - 5.0, self.pan_angle + delta_pan))

            # --- MODE 2: TURRET_POINTER (Direct Absolute Mapping) ---
            else:
                normalized_x = error_x / center_x
                raw_target = cfg.pan_center_deg + (normalized_x * 50.0)
                self.pan_angle = (0.35 * raw_target) + (0.65 * self.pan_angle)

            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self.get_telemetry_state(target_to_track)

        # -------------------------------------------------------------
        # CASE B: TARGET LOST / OCCLUDED (Coast with Velocity Memory)
        # -------------------------------------------------------------
        self.lost_frames += 1
        if self.is_locked and self.lost_frames <= self.max_coast_frames and abs(self.velocity_cx) > 15.0:
            # Target is temporarily occluded - coast in the direction of flight
            coast_direction = 1.0 if self.velocity_cx > 0 else -1.0
            if self.invert_pan:
                coast_direction = -coast_direction
            coast_step = coast_direction * min(1.2, abs(self.velocity_cx) * 0.005)
            self.pan_angle = max(cfg.pan_min_deg + 5.0, min(cfg.pan_max_deg - 5.0, self.pan_angle + coast_step))
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self.get_telemetry_state(status="COASTING")

        # -------------------------------------------------------------
        # CASE C: NO TARGET DETECTED FOR > 1.0 SECOND -> CALM IDLE RETURN
        # -------------------------------------------------------------
        self.is_locked = False
        time_since_target = now - self.last_target_time
        if time_since_target > 0.8:
            if abs(self.pan_angle - cfg.pan_center_deg) > 0.5:
                # Smooth exponential decay back to center
                self.pan_angle = (0.15 * cfg.pan_center_deg) + (0.85 * self.pan_angle)
            else:
                self.pan_angle = cfg.pan_center_deg
            self.reset_integrators()

        return round(self.pan_angle, 1), round(self.tilt_angle, 1), self.get_telemetry_state(status="IDLE")

    def get_telemetry_state(self, target: Optional[dict] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Returns structured gimbal tracking state for telemetry and UI HUD."""
        state_status = status or ("LOCKED" if (self.is_locked and target) else "IDLE")
        return {
            "pan_deg": round(self.pan_angle, 1),
            "tilt_deg": round(self.tilt_angle, 1),
            "mode": self.mode,
            "invert_pan": self.invert_pan,
            "is_locked": self.is_locked,
            "locked_track_id": self.locked_track_id,
            "tracking_status": state_status,
            "auto_track": self.auto_track_enabled
        }

    def compute_proportional_angles(
        self,
        target_center_u: Optional[float],
        target_center_v: Optional[float],
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Tuple[float, float, bool]:
        """Backward compatibility wrapper."""
        fake_target = {"center_u": target_center_u, "center_v": target_center_v} if target_center_u else None
        pan, tilt, meta = self.update_tracking(
            targets=[fake_target] if fake_target else [],
            primary_target=fake_target,
            frame_width=frame_width,
            frame_height=frame_height
        )
        return pan, tilt, meta.get("is_locked", False)

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, pan_deg))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, tilt_deg))
        self.reset_integrators()

