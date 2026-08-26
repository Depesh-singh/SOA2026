"""
SMART-SHIELD v3.0 Backend Core Module Exports
"""

from .vision.velocity_estimator import OpticalVelocityEstimator
from .vision.detector import DroneObjectDetector, CameraStreamManager
from .vision.tracker import ByteTracker
from .vision.calibration import HomographyCalibrator, PinholeCalibrator
from .hardware.radar_interface import LD2450RadarParser, ESP32SerialController
from .fusion.state_estimator import TargetEKFFilter, StateEstimator
from .fusion.sensor_fusion import SensorFusionEngine, fuse_velocities_weighted
from .fusion.threat_matrix import ThreatEvaluationEngine
from .fusion.trajectory_predictor import TrajectoryPredictor
from .gimbal.servo_control import PIDGimbalController, ServoController
from .cyber_defense.rf_monitor import CyberRFMonitor

__all__ = [
    "OpticalVelocityEstimator",
    "DroneObjectDetector",
    "CameraStreamManager",
    "ByteTracker",
    "HomographyCalibrator",
    "PinholeCalibrator",
    "LD2450RadarParser",
    "ESP32SerialController",
    "TargetEKFFilter",
    "StateEstimator",
    "SensorFusionEngine",
    "fuse_velocities_weighted",
    "ThreatEvaluationEngine",
    "TrajectoryPredictor",
    "PIDGimbalController",
    "ServoController",
    "CyberRFMonitor"
]
