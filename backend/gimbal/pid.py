"""
SMART-SHIELD v3.0 Servo Tracking Controller
===========================================
Integrated directly from the proven servo_tracker/servo_controller.py module.

Key Features:
- ZERO SPINNING / INSTANT BRAKE: Sends 90.0° when drone is centered (±50px) or lost.
- Smooth Slow Crawl: Calculates gentle speed offset (3.0° to 8.0°) based on drone distance from center.
- Heading Safety Bounds: Tracks software heading within ±90° (180° total travel) to prevent 360°/720° spin.
- Dual Mode: Supports Continuous (360°) and Standard Positional (180°).
"""

import time
from typing import Tuple, Optional, Dict, Any
from ..config import config


class PIDGimbalController:
    """
    Direct integration of the proven ServoTracker controller.
    """

    def __init__(self):
        cfg = config.gimbal
        self.mode: str = "continuous"  # 'continuous' (360 speed/brake) or 'positional' (180 angle)

        # ── INVISIBLE CENTER SQUARE TARGET ZONE (Optical Alignment Window) ──
        # When drone is inside this square, servos hold target in deadband lock
        self.deadband_px: float = 40.0 # ±40px horizontal square boundary (80px wide)
        self.deadband_py: float = 35.0 # ±35px vertical square boundary (70px tall)
        self.invert_pan: bool = getattr(cfg, "invert_pan", False)
        self.invert_tilt: bool = getattr(cfg, "invert_tilt", False)

        # Smooth Slow Continuous Mode (Gentle, Controlled Tracking)
        self.neutral_angle: float = 90.0
        self.min_speed_offset: float = 4.0   # Gentle slow base speed (86 or 94)
        self.max_speed_offset: float = 12.0  # Controlled maximum speed (78 or 102)

        # Software travel protection: 180° right, 180° left (half circles, 360° total travel, no wire wrap)
        self.estimated_heading: float = 0.0
        self.max_travel_deg: float = 180.0
        self.deg_per_sec_at_max: float = 45.0 # Slow 45°/s max slew rate

        # Strict limits for Vertical Tilt: 25° Up, 25° Down from 90° center (50° total travel)
        self.neutral_tilt: float = 90.0
        self.max_tilt_travel_deg: float = 25.0
        self.min_tilt_limit: float = 65.0    # 90° - 25° = 65.0° (25° Up limit)
        self.max_tilt_limit: float = 115.0   # 90° + 25° = 115.0° (25° Down limit)
        self.current_tilt: float = 90.0
        self.estimated_tilt_heading: float = 0.0

        # Positional mode settings (Rapid 180° angle tracking)
        self.current_pos_angle: float = 90.0
        self.min_pos_angle: float = 0.0
        self.max_pos_angle: float = 180.0

        # State
        self.pan_angle: float = 90.0
        self.tilt_angle: float = 90.0
        self._last_diag_time: float = 0.0
        self._last_pan_state: str = ""
        self._last_tilt_state: str = ""
        self.auto_track_enabled: bool = True
        self.locked_track_id: Optional[int] = None
        self.is_locked: bool = False
        self.in_center_square: bool = False
        self.last_time: float = time.time()
        self.last_target_time: float = 0.0

    def lock_target(self, track_id: int):
        self.locked_track_id = int(track_id)
        self.is_locked = True

    def unlock_target(self):
        self.locked_track_id = None
        self.is_locked = False

    def toggle_mode(self) -> str:
        self.mode = "positional" if self.mode == "continuous" else "continuous"
        self.estimated_heading = 0.0
        self.current_pos_angle = 90.0
        self.pan_angle = 90.0
        return self.mode

    def toggle_invert(self) -> bool:
        self.invert_pan = not self.invert_pan
        return self.invert_pan

    def toggle_invert_tilt(self) -> bool:
        self.invert_tilt = not self.invert_tilt
        return self.invert_tilt

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        self.pan_angle = max(0.0, min(180.0, pan_deg))
        self.estimated_heading = 0.0
        self.current_pos_angle = self.pan_angle
        self.tilt_angle = max(self.min_tilt_limit, min(self.max_tilt_limit, tilt_deg))
        self.current_tilt = self.tilt_angle
        self.estimated_tilt_heading = round(self.current_tilt - 90.0, 1)

    def update_tracking(
        self,
        targets: list,
        primary_target: Optional[dict],
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Visual Servoing centering drone into the Invisible Center Square:
        - Drone inside center square (±60px X, ±50px Y) -> HOLD / BRAKE STOP (90.0)
        - Drone Left of square  -> Pan Left fast
        - Drone Right of square -> Pan Right fast
        - Drone Above square    -> Tilt Up fast
        - Drone Below square    -> Tilt Down fast
        """
        now = time.time()
        dt = max(1e-4, min(0.1, now - self.last_time))
        self.last_time = now

        if not self.auto_track_enabled:
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry()

        # 1. Match locked target or fallback to primary target
        target = None
        if self.locked_track_id is not None:
            for t in targets:
                if t.get("track_id") == self.locked_track_id:
                    target = t
                    break

        if target is None and primary_target is not None:
            target = primary_target
            self.locked_track_id = target.get("track_id")

        # ── NO TARGET: Brake to 90.0 center ──
        if target is None or "center_u" not in target:
            self.is_locked = False
            self.in_center_square = False
            if self.mode == "continuous":
                self.pan_angle = self.neutral_angle
            if abs(self.current_tilt - 90.0) > 0.5:
                diff = 90.0 - self.current_tilt
                step = 0.5 if diff > 0 else -0.5
                self.current_tilt += step
            else:
                self.current_tilt = 90.0
            self.tilt_angle = round(self.current_tilt, 1)
            self.estimated_tilt_heading = round(self.current_tilt - 90.0, 1)
            return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry(status="NO_DRONE_STOPPED")

        # ── TARGET FOUND: Calculate displacement from Invisible Center Square ──
        self.is_locked = True
        self.last_target_time = now

        cx = float(target["center_u"])
        cy = float(target.get("center_v", frame_height / 2.0))
        frame_center_x = frame_width / 2.0
        frame_center_y = frame_height / 2.0
        error_px = cx - frame_center_x  # <0: Drone is Left of square, >0: Right of square
        error_py = cy - frame_center_y  # <0: Drone is Above square, >0: Below square

        in_x = abs(error_px) <= self.deadband_px
        in_y = abs(error_py) <= self.deadband_py
        self.in_center_square = (in_x and in_y)
        # Decide which axis to actuate (concurrent tracking when outside deadband):
        pan_active = not in_x   # True if drone is horizontally outside deadband
        tilt_active = not in_y  # True if drone is vertically outside deadband

        # ── 1. HORIZONTAL TRACKING (PAN) ──
        # ESP32 firmware calculates: effectivePan = INVERT_PAN ? (180.0f - pan) : pan; (where INVERT_PAN is true)
        # To turn physical camera RIGHT, ESP32 needs effectivePan > 90.0° -> Python must send (90.0 - speed)
        # To turn physical camera LEFT, ESP32 needs effectivePan < 90.0° -> Python must send (90.0 + speed)
        if pan_active:
            if self.mode == "continuous":
                norm_x = min(1.0, (abs(error_px) - self.deadband_px) / max(1.0, frame_center_x - self.deadband_px))
                speed_x = self.min_speed_offset + (norm_x ** 0.85) * (self.max_speed_offset - self.min_speed_offset)
                speed_x = min(self.max_speed_offset, speed_x)

                if error_px > 0:
                    # Drone on Right -> Send (90 - speed) so ESP32 inverts to (90 + speed) -> Camera turns RIGHT
                    cmd = (self.neutral_angle - speed_x) if not self.invert_pan else (self.neutral_angle + speed_x)
                    rate = self.deg_per_sec_at_max * (speed_x / self.max_speed_offset)
                    pan_status = "FAST_PAN_RIGHT" if not self.invert_pan else "FAST_PAN_LEFT"
                    pan_state = "PAN RIGHT" if not self.invert_pan else "PAN LEFT"
                else:
                    # Drone on Left -> Send (90 + speed) so ESP32 inverts to (90 - speed) -> Camera turns LEFT
                    cmd = (self.neutral_angle + speed_x) if not self.invert_pan else (self.neutral_angle - speed_x)
                    rate = -self.deg_per_sec_at_max * (speed_x / self.max_speed_offset)
                    pan_status = "FAST_PAN_LEFT" if not self.invert_pan else "FAST_PAN_RIGHT"
                    pan_state = "PAN LEFT" if not self.invert_pan else "PAN RIGHT"

                # Update software heading for telemetry (safe bounds clamped without freezing tracking)
                self.estimated_heading = max(-self.max_travel_deg, min(self.max_travel_deg, self.estimated_heading + rate * dt))
                self.pan_angle = round(cmd, 1)
            else:
                # Positional mode
                step = 0.08 * error_px
                if not self.invert_pan:
                    step = step
                else:
                    step = -step
                self.current_pos_angle = max(self.min_pos_angle, min(self.max_pos_angle, self.current_pos_angle + step))
                self.pan_angle = round(self.current_pos_angle, 1)
                pan_status = "TRACKING_PAN"
                pan_state = "PAN POSITIONING"
        else:
            # Centered inside deadband: Active electrical brake stop (90.0°)
            pan_state = "PAN HOLD (CENTERED)"
            if self.mode == "continuous":
                self.pan_angle = self.neutral_angle
            pan_status = "PAN_CENTERED"

        # ── 2. VERTICAL TRACKING (TILT - STRICT ±25° TRAVEL, 50° TOTAL SPAN) ──
        # Physical Travel Bounds: 65.0° (25° Up limit) to 115.0° (25° Down limit)
        # Neutral Level: 90.0°
        if tilt_active:
            norm_y = min(1.0, (abs(error_py) - self.deadband_py) / max(1.0, frame_center_y - self.deadband_py))
            step_y = 0.35 + (norm_y ** 0.85) * 0.90  # Slew rate (~10°/s to ~25°/s smooth ramp)

            # NOTE: On this physical gimbal servo mounting:
            # - Angle < 90° (down to 65.0°) physically tilts the camera UPWARD (25° Up limit)
            # - Angle > 90° (up to 115.0°) physically tilts the camera DOWNWARD (25° Down limit)
            if error_py < 0:
                # Drone is UPWARD in frame (above center) -> Camera must physically tilt UP
                # Physical UP requires decreasing angle towards 65.0°
                if not self.invert_tilt:
                    self.current_tilt = max(self.min_tilt_limit, self.current_tilt - step_y)
                    tilt_state = "TILT UP"
                    tilt_status = "TILT_UP"
                else:
                    self.current_tilt = min(self.max_tilt_limit, self.current_tilt + step_y)
                    tilt_state = "TILT UP (INV)"
                    tilt_status = "TILT_UP"
            else:
                # Drone is DOWNWARD in frame (below center) -> Camera must physically tilt DOWN
                # Physical DOWN requires increasing angle towards 115.0°
                if not self.invert_tilt:
                    self.current_tilt = min(self.max_tilt_limit, self.current_tilt + step_y)
                    tilt_state = "TILT DOWN"
                    tilt_status = "TILT_DOWN"
                else:
                    self.current_tilt = max(self.min_tilt_limit, self.current_tilt - step_y)
                    tilt_state = "TILT DOWN (INV)"
                    tilt_status = "TILT_DOWN"

            # Strict physical travel clamping: NEVER exceeds 65.0° (Up 25°) or 115.0° (Down 25°)
            self.current_tilt = max(self.min_tilt_limit, min(self.max_tilt_limit, self.current_tilt))
            self.tilt_angle = round(self.current_tilt, 1)
            self.estimated_tilt_heading = round(self.current_tilt - 90.0, 1)
        else:
            # Centered inside vertical deadband: Maintain holding torque at current position
            tilt_state = "TILT HOLD (CENTERED)"
            tilt_status = "TILT_CENTERED"
            self.tilt_angle = round(self.current_tilt, 1)
            self.estimated_tilt_heading = round(self.current_tilt - 90.0, 1)

        # Required Diagnostic Telemetry Output (Printed on state transition or throttled to ~4 Hz)
        if (now - self._last_diag_time >= 0.25) or (pan_state != self._last_pan_state) or (tilt_state != self._last_tilt_state):
            print(
                f"\nDrone Center X: {cx:.1f}\n"
                f"Drone Center Y: {cy:.1f}\n\n"
                f"Frame Center X: {frame_center_x:.1f}\n"
                f"Frame Center Y: {frame_center_y:.1f}\n\n"
                f"Horizontal Error: {error_px:+.1f}\n"
                f"Vertical Error: {error_py:+.1f}\n\n"
                f"Pan State:\n{pan_state}\n\n"
                f"Tilt State:\n{tilt_state}\n\n"
                f"Current Pan Position: {self.pan_angle:.1f}\n"
                f"Current Tilt Command: {self.tilt_angle:.1f}\n\n"
                f"Estimated Tilt Heading: {self.estimated_tilt_heading:+.1f}° (Limit: ±25.0°, 50° span)\n"
                f"----------------------------------------"
            )
            self._last_diag_time = now
            self._last_pan_state = pan_state
            self._last_tilt_state = tilt_state

        final_status = "TARGET_LOCKED_IN_SQUARE" if self.in_center_square else f"{pan_status}_{tilt_status}"
        return round(self.pan_angle, 1), round(self.tilt_angle, 1), self._telemetry(target, status=final_status)

    def _telemetry(self, target: Optional[dict] = None, status: Optional[str] = None) -> Dict[str, Any]:
        return {
            "pan_deg": round(self.pan_angle, 1),
            "tilt_deg": round(self.tilt_angle, 1),
            "heading_deg": round(self.estimated_heading, 1) if self.mode == "continuous" else round(self.current_pos_angle, 1),
            "tilt_heading_deg": round(self.estimated_tilt_heading, 1),
            "mode": self.mode,
            "invert_pan": self.invert_pan,
            "invert_tilt": self.invert_tilt,
            "is_locked": self.is_locked,
            "locked_track_id": self.locked_track_id,
            "tracking_status": status or ("LOCKED" if self.is_locked else "BRAKED"),
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
