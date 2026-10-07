"""
VayuNetra Servo Tracking Controller — Standalone Module
=======================================================
Supports both:
  1. 360° Continuous Rotation Servos (90° = STOP, <90° = Turn Left, >90° = Turn Right)
  2. Standard 180° Positional Servos (0° = Left, 90° = Center, 180° = Right)

Key Safety Features:
  - ZERO SPINNING: Stops instantly (sends 90°) when drone is centered or lost.
  - Software 180° Span Limit: Stops movement if limit is reached.
  - Proportional Speed: Slows down as drone approaches center for perfect locking.
"""

import time
import threading
import serial


class ServoTracker:
    """
    Precision Servo Tracker with instant braking on center/loss
    and strict 180° maximum travel protection.
    """

    def __init__(
        self,
        port: str = "COM5",
        baudrate: int = 115200,
        mode: str = "continuous",  # 'continuous' (360) or 'positional' (180)
        deadband_px: int = 50,     # Middle zone width: drone in center = STOP
        invert: bool = False,
    ):
        self.port = port
        self.baudrate = baudrate
        self.mode = mode.lower()
        self.deadband_px = deadband_px
        self.invert = invert

        # Continuous 360 settings (Speed control)
        # 90 is STOP. 84-88 is gentle left, 92-96 is gentle right
        self.neutral_angle = 90.0
        self.min_speed_offset = 3.0   # Min speed to overcome friction (e.g. 87 or 93)
        self.max_speed_offset = 8.0   # Max crawl speed (e.g. 82 or 98)

        # Software angle limit tracking (Span: -90° to +90°, total 180°)
        self.estimated_heading = 0.0  # -90 (max left) to +90 (max right)
        self.max_travel_deg = 90.0    # 90 left + 90 right = 180 total
        self.deg_per_sec_at_max = 45.0  # Approx speed of MG996R at max_speed_offset

        # Positional 180 settings
        self.current_pos_angle = 90.0
        self.min_pos_angle = 0.0
        self.max_pos_angle = 180.0

        # State
        self._target_valid = False
        self._target_x = -1.0
        self._frame_width = 640
        self._running = False
        self._thread = None
        self._serial = None
        self._lock = threading.Lock()
        self._last_cmd = 90.0
        self._last_time = time.time()

    def start(self):
        """Open serial port and start loop."""
        if self._running:
            return
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(1.5)
            print(f"[ServoTracker] Connected to {self.port} @ {self.baudrate} ({self.mode.upper()} mode)")
        except Exception as e:
            print(f"[ServoTracker] ERROR opening {self.port}: {e}")
            return

        self._running = True
        self._send_angle(90.0)  # Stop motor immediately on boot
        self._last_time = time.time()

        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop tracking and brake motor."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._send_angle(90.0)  # STOP
        time.sleep(0.1)
        if self._serial and self._serial.is_open:
            self._serial.close()
        print("[ServoTracker] Stopped & motor braked.")

    def update_target(self, target_center_x: float, frame_width: int = 640):
        """Update target coordinates."""
        with self._lock:
            self._target_x = float(target_center_x)
            self._frame_width = int(frame_width)
            self._target_valid = True

    def clear_target(self):
        """No drone seen: stop immediately."""
        with self._lock:
            self._target_valid = False

    def set_mode(self, mode: str):
        """Toggle between 'continuous' (360) and 'positional' (180)."""
        with self._lock:
            self.mode = mode.lower()
            self.estimated_heading = 0.0
            self.current_pos_angle = 90.0
        self._send_angle(90.0)

    def set_invert(self, invert: bool):
        with self._lock:
            self.invert = invert

    def reset_center(self):
        """Reset software heading to origin."""
        with self._lock:
            self.estimated_heading = 0.0
            self.current_pos_angle = 90.0
        self._send_angle(90.0)

    def get_state(self) -> dict:
        """Return live telemetry for HUD."""
        with self._lock:
            frame_center = self._frame_width / 2.0
            if self._target_valid:
                error = self._target_x - frame_center
            else:
                error = 0.0

            if not self._target_valid:
                direction = "NO DRONE (STOPPED)"
            elif abs(error) <= self.deadband_px:
                direction = "DRONE CENTERED (LOCKED STILL)"
            elif error < 0:
                direction = "MOVING LEFT" if not self.invert else "MOVING RIGHT"
            else:
                direction = "MOVING RIGHT" if not self.invert else "MOVING LEFT"

            return {
                "target_detected": self._target_valid,
                "target_x": round(self._target_x, 1) if self._target_valid else None,
                "frame_center_x": round(frame_center, 1),
                "error_px": round(error, 1),
                "direction": direction,
                "servo_angle": round(self._last_cmd, 1),
                "heading_deg": round(self.estimated_heading, 1) if self.mode == "continuous" else round(self.current_pos_angle, 1),
                "mode": self.mode,
                "invert": self.invert,
            }

    def _control_loop(self):
        """Main control loop running at 25 Hz (every 40ms)."""
        while self._running:
            now = time.time()
            dt = max(1e-4, now - self._last_time)
            self._last_time = now

            with self._lock:
                target_valid = self._target_valid
                target_x = self._target_x
                frame_width = self._frame_width
                invert = self.invert
                mode = self.mode

            # ──────────────────────────────────────────────────────────
            # RULE 1: If NO target detected OR in DEAD ZONE → STOP (90.0)
            # ──────────────────────────────────────────────────────────
            if not target_valid:
                if mode == "continuous":
                    self._send_angle(90.0)
                time.sleep(0.04)
                continue

            frame_center = frame_width / 2.0
            error_px = target_x - frame_center

            if abs(error_px) <= self.deadband_px:
                # Drone is right in the middle! HOLD COMPLETELY STILL.
                if mode == "continuous":
                    self._send_angle(90.0)
                time.sleep(0.04)
                continue

            # ──────────────────────────────────────────────────────────
            # Continuous 360 Servo Control (Velocity / Braking)
            # ──────────────────────────────────────────────────────────
            if mode == "continuous":
                # Normalize error (-1.0 to +1.0)
                norm_err = error_px / (frame_width / 2.0)
                if invert:
                    norm_err = -norm_err

                # Soft 180° limit check (-90° to +90°)
                if norm_err < 0 and self.estimated_heading <= -self.max_travel_deg:
                    # Hit Left limit: STOP
                    self._send_angle(90.0)
                    time.sleep(0.04)
                    continue
                elif norm_err > 0 and self.estimated_heading >= self.max_travel_deg:
                    # Hit Right limit: STOP
                    self._send_angle(90.0)
                    time.sleep(0.04)
                    continue

                # Compute gentle crawl speed proportional to error
                speed_mag = self.min_speed_offset + abs(norm_err) * (self.max_speed_offset - self.min_speed_offset)
                speed_mag = min(self.max_speed_offset, speed_mag)

                if norm_err < 0:
                    # Move Left
                    cmd = 90.0 - speed_mag
                    rate = -self.deg_per_sec_at_max * (speed_mag / self.max_speed_offset)
                else:
                    # Move Right
                    cmd = 90.0 + speed_mag
                    rate = self.deg_per_sec_at_max * (speed_mag / self.max_speed_offset)

                # Update estimated heading
                with self._lock:
                    self.estimated_heading = max(-self.max_travel_deg, min(self.max_travel_deg, self.estimated_heading + rate * dt))

                self._send_angle(cmd)

            # ──────────────────────────────────────────────────────────
            # Standard 180 Positional Servo Control
            # ──────────────────────────────────────────────────────────
            else:
                step = 0.035 * error_px
                if invert:
                    step = -step
                step = max(-2.5, min(2.5, step))

                with self._lock:
                    new_pos = max(self.min_pos_angle, min(self.max_pos_angle, self.current_pos_angle + step))
                    self.current_pos_angle = new_pos
                self._send_angle(new_pos)

            time.sleep(0.04)

    def _send_angle(self, angle: float):
        """Send command over serial only if changed."""
        angle = round(angle, 1)
        if abs(angle - self._last_cmd) < 0.2 and angle != 90.0:
            return

        cmd = f"TILT:{angle}\n"
        try:
            if self._serial and self._serial.is_open:
                self._serial.write(cmd.encode("utf-8"))
                self._serial.flush()
                self._last_cmd = angle
        except Exception as e:
            pass
