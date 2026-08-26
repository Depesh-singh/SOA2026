"""
SMART-SHIELD v3.0 State Estimator Module
Re-exports the Extended Kalman Filter (EKF) state estimator from ekf.py.
"""

from .ekf import TargetEKFFilter

# Alias for standard naming
StateEstimator = TargetEKFFilter

__all__ = ["TargetEKFFilter", "StateEstimator"]
