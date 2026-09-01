"""
SMART-SHIELD v3.0 Servo Tracking Controller
CAMERA IS MOUNTED ON THE SERVO (MG996R on ESP32 GPIO 18).

How it works:
- Camera physically moves with the servo.
- When the drone appears RIGHT of center, the servo adjusts to bring it back to center.
- Small proportional steps each frame. No aggressive PID. No oscillation.
- If the servo moves the WRONG direction, click INVERT button once to fix it.
- When no drone is detected, servo smoothly returns to 90° center.
"""

import time
from typing import Tuple, Optional, Dict, Any
from ..config import config


class PIDGimbalController:
    """Camera-on-servo tracking controller."""

    def __init__(self):
        cfg = config.gimbal
        self.pan_angle: float = cfg.pan_center_deg
        self.tilt_angle: float = cfg.tilt_center_deg

        self.auto_track_enabled: bool = True
        self.invert_pan: bool = getattr(cfg, "invert_pan", False)

        # Target lock state
        self.locked_track_id: Optional[int] = None
        self.is_locked: bool = False
        self.last_target_time: float = 0.0

        # Responsive proportional visual servoing
        self.gain: float = 0.045         # Degrees of servo movement per pixel of error (~4.5 deg for 100px error)
        self.max_step: float = 3.0       # Max degrees the servo can move per update cycle
        self.deadband_px: float = 12.0   # If drone is within ±12px of center, hold steady

    def lock_target(self, track_id: int):
        self.locked_track_id = int(track_id)
        self.is_locked = True

    def unlock_target(self):
        self.locked_track_id = None
        self.is_locked = False

    def toggle_mode(self) -> str:
        return "CAMERA_ON_SERVO"

    def toggle_invert(self) -> bool:
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
        Called every frame. Adjusts servo angle to center the drone.
        """
        cfg = config.gimbal
        now = time.time()

        if not self.auto_track_enabled:
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry()

        # 1. Find the target to track
        target = None
        if self.locked_track_id is not None:
            for t in targets:
                if t.get("track_id") == self.locked_track_id:
                    target = t
                    break

        if target is None and primary_target is not None:
            target = primary_target
            self.locked_track_id = target.get("track_id")

        # ── DRONE DETECTED ──
        if target is not None and "center_u" in target:
            self.is_locked = True
            self.last_target_time = now

            cx = float(target["center_u"])
            center_x = frame_width / 2.0
            error_px = cx - center_x   # positive = drone is to the RIGHT

            # Deadband: if drone is already near center, don't move
            if abs(error_px) <= self.deadband_px:
                return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry(target, "LOCKED")

            # Calculate how much to move the servo this frame
            step = self.gain * error_px

            # Flip direction if inverted (default: subtract because of servo mounting)
            if self.invert_pan:
                step = -step

            # Limit max movement per frame to prevent jerky motion
            if step > self.max_step:
                step = self.max_step
            elif step < -self.max_step:
                step = -self.max_step

            # Apply the step — SUBTRACT because for this servo mount,
            # decreasing angle = camera pans right (toward drone on right)
            self.pan_angle -= step
            self.pan_angle = max(cfg.pan_min_deg + 5.0, min(cfg.pan_max_deg - 5.0, self.pan_angle))

            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry(target, "LOCKED")

        # ── NO DRONE → slowly return to center ──
        self.is_locked = False
        time_lost = now - self.last_target_time

        if time_lost > 1.0:
            diff = cfg.pan_center_deg - self.pan_angle
            if abs(diff) > 0.5:
                self.pan_angle += 0.1 * diff   # Slow drift back to 90°
            else:
                self.pan_angle = cfg.pan_center_deg

        return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry(status="IDLE")

    def _telemetry(self, target: Optional[dict] = None, status: Optional[str] = None) -> Dict[str, Any]:
        return {
            "pan_deg": round(self.pan_angle, 1),
            "tilt_deg": round(self.tilt_angle, 1),
            "mode": "CAMERA_ON_SERVO",
            "invert_pan": self.invert_pan,
            "is_locked": self.is_locked,
            "locked_track_id": self.locked_track_id,
            "tracking_status": status or ("LOCKED" if self.is_locked else "IDLE"),
            "auto_track": self.auto_track_enabled
        }

    def compute_proportional_angles(self, target_center_u, target_center_v,
                                     frame_width=640, frame_height=480):
        fake = {"center_u": target_center_u, "center_v": target_center_v} if target_center_u else None
        pan, tilt, meta = self.update_tracking(
            targets=[fake] if fake else [], primary_target=fake,
            frame_width=frame_width, frame_height=frame_height
        )
        return pan, tilt, meta.get("is_locked", False)

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, pan_deg))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, tilt_deg))
