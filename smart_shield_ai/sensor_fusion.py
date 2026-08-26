"""
sensor_fusion.py

Smart Shield sensor-fusion module.

Combines:
    1. Camera-derived drone speed
    2. Radar-derived drone speed

Features:
    - Camera speed calculation
    - Radar + camera fusion
    - Confidence-weighted averaging
    - Missing-sensor handling
    - Sensor disagreement detection
    - Outlier rejection
    - Simple test mode
"""

import math


# ============================================================
# CAMERA SPEED
# ============================================================

def calculate_camera_speed(
    x1,
    y1,
    t1,
    x2,
    y2,
    t2,
    meters_per_pixel
):
    """
    Calculate drone speed from two camera observations.

    Position:
        (x1, y1) at time t1
        (x2, y2) at time t2

    meters_per_pixel:
        Camera calibration factor.

    Returns:
        Speed in meters/second.
    """

    # --------------------------------------------------------
    # Validate calibration
    # --------------------------------------------------------

    if meters_per_pixel <= 0:
        raise ValueError(
            "meters_per_pixel must be greater than 0."
        )

    # --------------------------------------------------------
    # Calculate elapsed time
    # --------------------------------------------------------

    delta_time = float(t2) - float(t1)

    if delta_time <= 0:
        raise ValueError(
            "Time difference must be greater than 0."
        )

    # --------------------------------------------------------
    # Pixel displacement
    # --------------------------------------------------------

    dx = float(x2) - float(x1)
    dy = float(y2) - float(y1)

    pixel_distance = math.sqrt(
        dx ** 2 + dy ** 2
    )

    # --------------------------------------------------------
    # Convert pixels to meters
    # --------------------------------------------------------

    distance_meters = (
        pixel_distance * float(meters_per_pixel)
    )

    # --------------------------------------------------------
    # Speed = distance / time
    # --------------------------------------------------------

    speed = distance_meters / delta_time

    return float(speed)


# ============================================================
# CONFIDENCE VALIDATION
# ============================================================

def _validate_confidence(confidence):
    """
    Keep confidence inside the valid range [0, 1].
    """

    if confidence is None:
        return 0.0

    confidence = float(confidence)

    if math.isnan(confidence):
        return 0.0

    return max(
        0.0,
        min(1.0, confidence)
    )


# ============================================================
# SENSOR FUSION
# ============================================================

def fuse_velocity(
    radar_velocity=None,
    radar_confidence=0.0,
    camera_velocity=None,
    camera_confidence=0.0,
    disagreement_threshold=10.0
):
    """
    Fuse radar and camera velocity estimates.

    Parameters
    ----------
    radar_velocity : float or None
        Radar velocity in m/s.

    radar_confidence : float
        Radar confidence from 0.0 to 1.0.

    camera_velocity : float or None
        Camera-derived velocity in m/s.

    camera_confidence : float
        Camera confidence from 0.0 to 1.0.

    disagreement_threshold : float
        Maximum acceptable difference between
        radar and camera velocities in m/s.

    Returns
    -------
    dict
        Contains:

        fused_velocity
        source
        radar_velocity
        camera_velocity
        disagreement
        radar_confidence
        camera_confidence
    """

    # --------------------------------------------------------
    # Validate confidence
    # --------------------------------------------------------

    radar_confidence = _validate_confidence(
        radar_confidence
    )

    camera_confidence = _validate_confidence(
        camera_confidence
    )

    disagreement_threshold = float(
        disagreement_threshold
    )

    if disagreement_threshold < 0:
        raise ValueError(
            "disagreement_threshold cannot be negative."
        )

    # --------------------------------------------------------
    # Convert available velocities to float
    # --------------------------------------------------------

    if radar_velocity is not None:
        radar_velocity = float(radar_velocity)

        if math.isnan(radar_velocity):
            radar_velocity = None

    if camera_velocity is not None:
        camera_velocity = float(camera_velocity)

        if math.isnan(camera_velocity):
            camera_velocity = None

    # ========================================================
    # CASE 1
    # Both sensors missing
    # ========================================================

    if (
        radar_velocity is None
        and camera_velocity is None
    ):

        return {
            "fused_velocity": None,
            "source": "NO_DATA",
            "radar_velocity": None,
            "camera_velocity": None,
            "disagreement": None,
            "radar_confidence": 0.0,
            "camera_confidence": 0.0
        }

    # ========================================================
    # CASE 2
    # Radar unavailable
    # ========================================================

    if radar_velocity is None:

        if camera_confidence <= 0:

            return {
                "fused_velocity": None,
                "source": "NO_DATA",
                "radar_velocity": None,
                "camera_velocity": camera_velocity,
                "disagreement": None,
                "radar_confidence": 0.0,
                "camera_confidence": camera_confidence
            }

        return {
            "fused_velocity": camera_velocity,
            "source": "CAMERA_ONLY",
            "radar_velocity": None,
            "camera_velocity": camera_velocity,
            "disagreement": None,
            "radar_confidence": 0.0,
            "camera_confidence": camera_confidence
        }

    # ========================================================
    # CASE 3
    # Camera unavailable
    # ========================================================

    if camera_velocity is None:

        if radar_confidence <= 0:

            return {
                "fused_velocity": None,
                "source": "NO_DATA",
                "radar_velocity": radar_velocity,
                "camera_velocity": None,
                "disagreement": None,
                "radar_confidence": radar_confidence,
                "camera_confidence": 0.0
            }

        return {
            "fused_velocity": radar_velocity,
            "source": "RADAR_ONLY",
            "radar_velocity": radar_velocity,
            "camera_velocity": None,
            "disagreement": None,
            "radar_confidence": radar_confidence,
            "camera_confidence": 0.0
        }

    # ========================================================
    # CASE 4
    # Both sensors available
    # ========================================================

    disagreement = abs(
        radar_velocity - camera_velocity
    )

    # ========================================================
    # CASE 5
    # Sensors disagree too much
    # ========================================================

    if disagreement > disagreement_threshold:

        # Radar has greater/equal confidence
        if radar_confidence >= camera_confidence:

            return {
                "fused_velocity": radar_velocity,
                "source": "RADAR_OUTLIER_REJECTED",
                "radar_velocity": radar_velocity,
                "camera_velocity": camera_velocity,
                "disagreement": disagreement,
                "radar_confidence": radar_confidence,
                "camera_confidence": camera_confidence
            }

        # Camera has greater confidence
        return {
            "fused_velocity": camera_velocity,
            "source": "CAMERA_OUTLIER_REJECTED",
            "radar_velocity": radar_velocity,
            "camera_velocity": camera_velocity,
            "disagreement": disagreement,
            "radar_confidence": radar_confidence,
            "camera_confidence": camera_confidence
        }

    # ========================================================
    # CASE 6
    # Sensors agree
    # ========================================================

    total_confidence = (
        radar_confidence +
        camera_confidence
    )

    # --------------------------------------------------------
    # No usable confidence
    # --------------------------------------------------------

    if total_confidence <= 0:

        return {
            "fused_velocity": None,
            "source": "NO_CONFIDENCE",
            "radar_velocity": radar_velocity,
            "camera_velocity": camera_velocity,
            "disagreement": disagreement,
            "radar_confidence": radar_confidence,
            "camera_confidence": camera_confidence
        }

    # --------------------------------------------------------
    # Confidence-weighted fusion
    # --------------------------------------------------------

    fused_velocity = (
        radar_velocity * radar_confidence
        +
        camera_velocity * camera_confidence
    ) / total_confidence

    return {
        "fused_velocity": float(fused_velocity),
        "source": "FUSED",
        "radar_velocity": radar_velocity,
        "camera_velocity": camera_velocity,
        "disagreement": float(disagreement),
        "radar_confidence": radar_confidence,
        "camera_confidence": camera_confidence
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("SMART SHIELD - SENSOR FUSION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # TEST 1: Camera speed
    # --------------------------------------------------------

    print("\n[TEST 1] Camera speed")

    speed = calculate_camera_speed(
        x1=100,
        y1=200,
        t1=0.0,
        x2=110,
        y2=200,
        t2=1.0,
        meters_per_pixel=0.05
    )

    print(
        f"Camera speed: {speed:.2f} m/s"
    )

    # Expected:
    # 10 pixels * 0.05 m/pixel = 0.5 m
    # 0.5 m / 1 sec = 0.5 m/s

    # --------------------------------------------------------
    # TEST 2: Radar only
    # --------------------------------------------------------

    print("\n[TEST 2] Radar only")

    result = fuse_velocity(
        radar_velocity=12.0,
        radar_confidence=0.9,
        camera_velocity=None,
        camera_confidence=0.0
    )

    print(result)

    # --------------------------------------------------------
    # TEST 3: Camera only
    # --------------------------------------------------------

    print("\n[TEST 3] Camera only")

    result = fuse_velocity(
        radar_velocity=None,
        radar_confidence=0.0,
        camera_velocity=10.0,
        camera_confidence=0.8
    )

    print(result)

    # --------------------------------------------------------
    # TEST 4: Both sensors agree
    # --------------------------------------------------------

    print("\n[TEST 4] Radar + Camera agree")

    result = fuse_velocity(
        radar_velocity=12.0,
        radar_confidence=0.9,
        camera_velocity=10.0,
        camera_confidence=0.8
    )

    print(result)

    # --------------------------------------------------------
    # TEST 5: Sensors strongly disagree
    # --------------------------------------------------------

    print("\n[TEST 5] Sensor disagreement")

    result = fuse_velocity(
        radar_velocity=30.0,
        radar_confidence=0.9,
        camera_velocity=10.0,
        camera_confidence=0.5,
        disagreement_threshold=10.0
    )

    print(result)

    # --------------------------------------------------------
    # TEST 6: No sensor
    # --------------------------------------------------------

    print("\n[TEST 6] No sensor data")

    result = fuse_velocity()

    print(result)

    print("\n" + "=" * 60)
    print("SENSOR FUSION TEST COMPLETE")
    print("=" * 60)