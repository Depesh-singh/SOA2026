import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.gimbal.pid import PIDGimbalController

def run_all_tests():
    print("=======================================================")
    print("STARTING PAN-TILT SEQUENTIAL TRACKING TEST SUITE")
    print("=======================================================")

    ctrl = PIDGimbalController()
    ctrl.tilt_angle = 90.0
    ctrl.pan_angle = 90.0

    # TEST 1: DRONE CENTERED
    pan, tilt, meta = ctrl.compute_proportional_angles(320.0, 240.0)
    assert pan == 90.0, f"Test 1 failed: Expected Pan 90.0 (Brake), got {pan}"
    assert tilt == 90.0, f"Test 1 failed: Expected Tilt 90.0 (Hold), got {tilt}"
    print("PASS TEST 1: Drone Centered -> PAN HOLD (90.0), TILT HOLD (90.0)")

    # TEST 2: DRONE MOVES LEFT
    ctrl.tilt_angle = 90.0
    pan, tilt, meta = ctrl.compute_proportional_angles(150.0, 240.0)
    assert pan < 90.0, f"Test 2 failed: Expected Pan < 90.0 (Left), got {pan}"
    assert tilt == 90.0, f"Test 2 failed: Expected Tilt to HOLD at 90.0, got {tilt}"
    print(f"PASS TEST 2: Drone Left -> PAN MOVING ({pan:.1f}), TILT HOLD ({tilt:.1f})")

    # TEST 3: DRONE MOVES RIGHT
    ctrl.tilt_angle = 90.0
    pan, tilt, meta = ctrl.compute_proportional_angles(490.0, 240.0)
    assert pan > 90.0, f"Test 3 failed: Expected Pan > 90.0 (Right), got {pan}"
    assert tilt == 90.0, f"Test 3 failed: Expected Tilt to HOLD at 90.0, got {tilt}"
    print(f"PASS TEST 3: Drone Right -> PAN MOVING ({pan:.1f}), TILT HOLD ({tilt:.1f})")

    # TEST 4: DRONE MOVES UP
    ctrl.tilt_angle = 90.0
    pan, tilt, meta = ctrl.compute_proportional_angles(320.0, 100.0)
    assert pan == 90.0, f"Test 4 failed: Expected Pan to HOLD at 90.0, got {pan}"
    assert tilt < 90.0, f"Test 4 failed: Expected Tilt < 90.0 (Up), got {tilt}"
    print(f"PASS TEST 4: Drone Up -> PAN HOLD ({pan:.1f}), TILT UP ({tilt:.1f})")

    # TEST 5: DRONE MOVES DOWN
    ctrl.tilt_angle = 90.0
    pan, tilt, meta = ctrl.compute_proportional_angles(320.0, 380.0)
    assert pan == 90.0, f"Test 5 failed: Expected Pan to HOLD at 90.0, got {pan}"
    assert tilt > 90.0, f"Test 5 failed: Expected Tilt > 90.0 (Down), got {tilt}"
    print(f"PASS TEST 5: Drone Down -> PAN HOLD ({pan:.1f}), TILT DOWN ({tilt:.1f})")

    # TEST 6: UP -> DOWN TRANSITION
    ctrl.tilt_angle = 90.0
    _, tilt1, _ = ctrl.compute_proportional_angles(320.0, 120.0)
    assert tilt1 < 90.0
    _, tilt2, _ = ctrl.compute_proportional_angles(320.0, 240.0)
    assert tilt2 == tilt1
    _, tilt3, _ = ctrl.compute_proportional_angles(320.0, 360.0)
    assert tilt3 > tilt2
    print(f"PASS TEST 6: Up ({tilt1:.1f}) -> Center ({tilt2:.1f}) -> Down ({tilt3:.1f})")

    # TEST 7: DOWN -> UP TRANSITION
    ctrl.tilt_angle = 90.0
    _, tilt1, _ = ctrl.compute_proportional_angles(320.0, 350.0)
    assert tilt1 > 90.0
    _, tilt2, _ = ctrl.compute_proportional_angles(320.0, 240.0)
    assert tilt2 == tilt1
    _, tilt3, _ = ctrl.compute_proportional_angles(320.0, 120.0)
    assert tilt3 < tilt2
    print(f"PASS TEST 7: Down ({tilt1:.1f}) -> Center ({tilt2:.1f}) -> Up ({tilt3:.1f})")

    # TEST 8: HORIZONTAL-FIRST ALIGNMENT (NEVER SIMULTANEOUS)
    ctrl.tilt_angle = 90.0
    pan8a, tilt8a, _ = ctrl.compute_proportional_angles(100.0, 180.0)
    assert pan8a != 90.0, "Step 8a failed: Expected PAN to find drone"
    assert tilt8a == 90.0, f"Step 8a failed: Expected TILT to HOLD at 90.0 while PAN finding, got {tilt8a}"

    pan8b, tilt8b, _ = ctrl.compute_proportional_angles(320.0, 50.0)
    assert pan8b == 90.0, f"Step 8b failed: Expected PAN to HOLD at 90.0, got {pan8b}"
    assert tilt8b < 90.0, f"Step 8b failed: Expected TILT to move up, got {tilt8b}"
    print("PASS TEST 8: Horizontal finds drone first, then Vertical centers vertically (Never simultaneous)")

    # TEST 9: SMALL MOVEMENT
    ctrl.tilt_angle = 90.0
    pan9a, tilt9a, _ = ctrl.compute_proportional_angles(320.0, 270.0)
    assert tilt9a == 90.0, f"Test 9a failed: Inside deadband should hold, got {tilt9a}"
    pan9b, tilt9b, _ = ctrl.compute_proportional_angles(320.0, 295.0)
    diff = abs(tilt9b - 90.0)
    assert 0.08 <= diff <= 0.45, f"Test 9b failed: Expected small step, got diff {diff}"
    print(f"PASS TEST 9: Small Movement -> Deadband Hold and Gentle Step ({diff:.2f})")

    # TEST 10: LARGE MOVEMENT (CONTROLLED STEP & 60 DEG SPAN CLAMP [60.0 to 120.0] & 180 DEG PAN TRAVEL)
    ctrl.tilt_angle = 90.0
    pan10, tilt10, _ = ctrl.compute_proportional_angles(320.0, 470.0)
    step10 = abs(tilt10 - 90.0)
    assert step10 <= 0.50, f"Test 10 failed: Single step too large ({step10} > 0.50)"

    ctrl.tilt_angle = 119.8
    for _ in range(10):
        _, tilt_clamped, _ = ctrl.compute_proportional_angles(320.0, 470.0)
    assert tilt_clamped <= 120.0, f"Test 10 failed: Exceeded 120.0 max clamp (30° down), got {tilt_clamped}"

    ctrl.tilt_angle = 60.2
    for _ in range(10):
        _, tilt_clamped_low, _ = ctrl.compute_proportional_angles(320.0, 10.0)
    assert tilt_clamped_low >= 60.0, f"Test 10 failed: Exceeded 60.0 min clamp (30° up), got {tilt_clamped_low}"
    print(f"PASS TEST 10: Large Movement gentle step ({step10:.2f}) and clamped in [60.0, 120.0] (30° up, 30° down)")

    print("\n=======================================================")
    print("ALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")

if __name__ == '__main__':
    run_all_tests()
