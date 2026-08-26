"""
SMART SHIELD - Trajectory Prediction Module

Predicts the future 2D image-space position of a tracked drone.
This module is intentionally independent of YOLO/ByteTrack so the
main engine can feed it the latest StateEstimator state.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


class TrajectoryPredictor:
    """Constant-velocity trajectory predictor."""

    def __init__(self, horizon: float = 3.0, step: float = 0.2):
        if horizon <= 0:
            raise ValueError("horizon must be greater than 0.")
        if step <= 0:
            raise ValueError("step must be greater than 0.")

        self.horizon = float(horizon)
        self.step = float(step)

    def predict(
        self,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
    ) -> List[Dict[str, float]]:
        """Return future positions in image coordinates."""
        x, y = float(position[0]), float(position[1])
        vx, vy = float(velocity[0]), float(velocity[1])

        points = []
        t = self.step

        while t <= self.horizon + 1e-9:
            points.append({
                "time": round(t, 3),
                "x": x + vx * t,
                "y": y + vy * t,
            })
            t += self.step

        return points

    def predict_from_state(self, state: Dict) -> List[Dict[str, float]]:
        """Accept the dictionary returned by StateEstimator.get_state()."""
        return self.predict(
            tuple(state["position"]),
            tuple(state["velocity"]),
        )


if __name__ == "__main__":
    predictor = TrajectoryPredictor()
    result = predictor.predict((100, 200), (10, 5))
    print("Trajectory prediction:")
    for point in result:
        print(point)
