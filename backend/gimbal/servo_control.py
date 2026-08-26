"""
SMART-SHIELD v3.0 Servo Control Module
Re-exports the closed-loop PID gimbal controller from pid.py.
"""

from .pid import PIDGimbalController

# Standard alias
ServoController = PIDGimbalController

__all__ = ["PIDGimbalController", "ServoController"]
