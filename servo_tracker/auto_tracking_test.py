"""
VayuNetra — Automatic Tracking Test (Simulated + Live)
=======================================================
Tests the ServoTracker closed-loop controller by:
  1. Simulating a drone moving across the frame (LEFT → CENTER → RIGHT → CENTER)
  2. Printing the live debug state at each step

This does NOT use YOLO or any AI model.
It only tests the servo controller logic and serial communication.

Usage:
    python servo_tracker/auto_tracking_test.py
"""

import time
import sys
import os

# Add parent directory to path so we can import servo_controller
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_controller import ServoTracker


def print_state(tracker: ServoTracker, label: str = ""):
    """Print the current tracking debug state."""
    s = tracker.get_state()
    det = "YES" if s["target_detected"] else "NO"
    tx = f'{s["target_x"]:.0f}' if s["target_x"] is not None else "---"
    cx = f'{s["frame_center_x"]:.0f}'
    err = f'{s["error_px"]:.0f}' if s["target_detected"] else "---"
    direction = s["direction"]
    angle = f'{s["servo_angle"]:.1f}'

    print(f"  {label:>12s} | TARGET: {det:3s} | X: {tx:>5s} | CENTER: {cx} | ERROR: {err:>5s} | DIR: {direction:<15s} | SERVO: {angle}°")


def main():
    print("=" * 90)
    print("  VayuNetra — Automatic Servo Tracking Test")
    print("=" * 90)
    print()
    print("This test simulates a drone moving across a 640px-wide frame.")
    print("The servo should follow it: LEFT when drone is left, RIGHT when right.")
    print()

    tracker = ServoTracker(
        port="COM5",
        baudrate=115200,
        center_angle=90.0,
        min_angle=70.0,
        max_angle=120.0,
        deadband_px=30,
        max_step_deg=3.0,
        gain=0.04,
        update_interval_ms=150,
        hold_on_lost=True,
    )

    tracker.start()
    time.sleep(1.0)

    frame_width = 640

    # ── Test 1: Drone at center (should hold) ──
    print("\n--- Test 1: Drone at CENTER (x=320) → Servo should HOLD at 90° ---")
    tracker.update_target(target_center_x=320, frame_width=frame_width)
    for i in range(5):
        time.sleep(0.3)
        print_state(tracker, f"t={i*0.3:.1f}s")

    # ── Test 2: Drone moves LEFT ──
    print("\n--- Test 2: Drone moves LEFT (x=100) → Servo should go BELOW 90° ---")
    tracker.update_target(target_center_x=100, frame_width=frame_width)
    for i in range(12):
        time.sleep(0.3)
        print_state(tracker, f"t={i*0.3:.1f}s")

    # ── Test 3: Drone moves to far RIGHT ──
    print("\n--- Test 3: Drone moves RIGHT (x=550) → Servo should go ABOVE 90° ---")
    tracker.update_target(target_center_x=550, frame_width=frame_width)
    for i in range(12):
        time.sleep(0.3)
        print_state(tracker, f"t={i*0.3:.1f}s")

    # ── Test 4: Drone returns to center ──
    print("\n--- Test 4: Drone returns to CENTER (x=315) → Servo should settle at ~90° ---")
    tracker.update_target(target_center_x=315, frame_width=frame_width)
    for i in range(8):
        time.sleep(0.3)
        print_state(tracker, f"t={i*0.3:.1f}s")

    # ── Test 5: Target lost ──
    print("\n--- Test 5: Target LOST → Servo should HOLD last position ---")
    tracker.clear_target()
    for i in range(5):
        time.sleep(0.3)
        print_state(tracker, f"t={i*0.3:.1f}s")

    # ── Test 6: Smooth sweep simulation ──
    print("\n--- Test 6: Smooth sweep (drone moving left-to-right-to-left) ---")
    positions = list(range(50, 600, 30)) + list(range(600, 50, -30))
    for x in positions:
        tracker.update_target(target_center_x=x, frame_width=frame_width)
        time.sleep(0.2)
        print_state(tracker, f"x={x}")

    print("\n--- All tests complete. Returning servo to 90° center. ---")
    tracker.stop()
    print("Done.\n")


if __name__ == "__main__":
    main()
