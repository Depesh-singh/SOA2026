"""
SMART SHIELD AI Engine Package

This package contains the core AI algorithms for:
- Sensor fusion (camera + radar velocity fusion)
- State estimation (Kalman filter)
- Trajectory prediction
- Risk/threat assessment
- Alert management
- Event logging

These modules are imported and used AS-IS by the backend.
DO NOT MODIFY the algorithm logic in these files.
"""

from .sensor_fusion import fuse_velocity, calculate_camera_speed
from .state_estimator import StateEstimator
from .trajectory_predictor import TrajectoryPredictor
from .risk_engine import RiskEngine, RiskResult
from .alert_manager import AlertManager, AlertState
from .event_logger import EventLogger

__all__ = [
    "fuse_velocity",
    "calculate_camera_speed",
    "StateEstimator",
    "TrajectoryPredictor",
    "RiskEngine",
    "RiskResult",
    "AlertManager",
    "AlertState",
    "EventLogger",
]
