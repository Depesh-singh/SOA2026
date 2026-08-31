"""
SMART-SHIELD v3.0 Configuration Parameters
Contains hardware pin mappings, threat equation weights, radar specs, AI engine settings, and server settings.
"""

import os
from pathlib import Path
from typing import Optional, Union, List
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent

class AIEngineConfig(BaseModel):
    model_path: str = os.getenv(
        "SMART_SHIELD_MODEL",
        str(BASE_DIR / "smart_shield_ai" / "models" / "best.pt")
    )
    camera_source: str = os.getenv("SMART_SHIELD_CAMERA", "1")
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    meters_per_pixel: Optional[float] = None
    yolo_confidence: float = 0.50
    yolo_iou: float = 0.45
    yolo_imgsz: int = 416
    device: str = "cuda:0"
    tracker_config: str = "bytetrack.yaml"
    speed_smoothing: int = 5
    prediction_horizon: float = 3.0
    prediction_step: float = 0.2
    low_confidence_threshold: float = 0.45
    medium_risk_threshold: float = 40.0
    high_risk_threshold: float = 70.0
    log_dir: str = str(BASE_DIR / "outputs" / "logs")

class ThreatWeights(BaseModel):
    w_distance: float = 0.30     # w1: Proximity weight
    w_speed: float = 0.25        # w2: Approach velocity weight
    w_direction: float = 0.20    # w3: Trajectory vector heading weight
    w_confidence: float = 0.15   # w4: Visual classification confidence weight
    w_behavior: float = 0.10     # w5: Erratic behavior / acceleration anomaly weight

    max_detection_range_m: float = 200.0
    max_expected_speed_ms: float = 30.0
    high_threat_threshold: float = 70.0
    medium_threat_threshold: float = 40.0

class RadarConfig(BaseModel):
    enabled: bool = os.getenv("SMART_SHIELD_RADAR_ENABLED", "false").lower() in ("true", "1", "yes")
    serial_port: str = os.getenv("SMART_SHIELD_RADAR_PORT", "COM5")
    baud_rate: int = int(os.getenv("SMART_SHIELD_RADAR_BAUD", "115200"))
    frame_header: bytes = bytes([0xAA, 0xFF, 0x03, 0x00])
    frame_tail: bytes = bytes([0x55, 0xCC])
    max_targets: int = 3
    fov_azimuth_deg: float = 120.0
    update_rate_hz: int = 10

class GimbalConfig(BaseModel):
    pan_min_deg: float = 0.0
    pan_max_deg: float = 180.0
    tilt_min_deg: float = 15.0
    tilt_max_deg: float = 90.0
    pan_center_deg: float = 90.0
    tilt_center_deg: float = 45.0
    
    # PID gains for visual servoing
    kp_pan: float = 0.08
    ki_pan: float = 0.002
    kd_pan: float = 0.015
    
    kp_tilt: float = 0.08
    ki_tilt: float = 0.002
    kd_tilt: float = 0.015

    # ESP32 MG996R Servo Tracking
    servo_enabled: bool = os.getenv("SMART_SHIELD_SERVO_ENABLED", "true").lower() in ("true", "1", "yes")
    servo_update_hz: int = 10  # Command send rate to ESP32 (10 = every 100ms)
    invert_pan: bool = False   # Standard direct optical mapping (Right in frame -> Pan > 90 deg)

class CyberRFConfig(BaseModel):
    baseline_noise_floor_dbm: float = -88.5
    jamming_delta_threshold_db: float = 18.0
    monitored_channels: list = [1, 6, 11, 36, 149]
    default_c2_channel: int = 6
    backup_channels: list = [1, 11, 40, 153]

class SystemConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    db_dsn: str = os.getenv("DATABASE_URL", "")
    simulation_mode: bool = False
    ai_inference_fps: int = 30
    ai: AIEngineConfig = AIEngineConfig()
    threat: ThreatWeights = ThreatWeights()
    radar: RadarConfig = RadarConfig()
    gimbal: GimbalConfig = GimbalConfig()
    cyber_rf: CyberRFConfig = CyberRFConfig()

config = SystemConfig()
