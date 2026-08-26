"""
SMART SHIELD - Threat/Risk Assessment Module

Converts detection confidence, speed and trajectory information into
a 0-100 risk score.

This is a prototype decision layer. Thresholds are configurable and
should be tuned with real test data before deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskResult:
    score: float
    level: str
    reasons: list[str]

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "level": self.level,
            "reasons": self.reasons,
        }


class RiskEngine:
    def __init__(
        self,
        low_confidence_threshold: float = 0.35,
        medium_threshold: float = 40.0,
        high_threshold: float = 70.0,
    ):
        self.low_confidence_threshold = float(low_confidence_threshold)
        self.medium_threshold = float(medium_threshold)
        self.high_threshold = float(high_threshold)

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, float(value)))

    def assess(
        self,
        detection_confidence: float,
        speed_mps: Optional[float] = None,
        radar_speed_mps: Optional[float] = None,
        trajectory_risk: float = 0.0,
        range_m: Optional[float] = None,
    ) -> RiskResult:
        confidence = self._clamp(detection_confidence, 0.0, 1.0)
        score = 0.0
        reasons = []

        # Detection confidence contributes to trust in the observation.
        score += confidence * 20.0

        if confidence < self.low_confidence_threshold:
            reasons.append("low_detection_confidence")

        # Speed contribution: capped at 30 m/s for this prototype.
        if speed_mps is not None:
            speed = abs(float(speed_mps))
            speed_component = self._clamp(speed / 30.0 * 30.0)
            score += speed_component
            if speed >= 15.0:
                reasons.append("high_speed")

        # Radar speed is an independent sensor contribution.
        if radar_speed_mps is not None:
            radar_speed = abs(float(radar_speed_mps))
            radar_component = self._clamp(radar_speed / 30.0 * 25.0)
            score += radar_component
            if radar_speed >= 15.0:
                reasons.append("radar_high_speed")

        # Trajectory module can provide a 0-100 risk estimate.
        trajectory_component = self._clamp(trajectory_risk) * 0.25
        score += trajectory_component
        if trajectory_risk >= 70.0:
            reasons.append("trajectory_risk")

        # Near range increases urgency.
        if range_m is not None:
            distance = max(0.0, float(range_m))
            if distance <= 10.0:
                score += 15.0
                reasons.append("close_range")
            elif distance <= 25.0:
                score += 7.0

        score = self._clamp(score)

        if score >= self.high_threshold:
            level = "HIGH"
        elif score >= self.medium_threshold:
            level = "MEDIUM"
        else:
            level = "LOW"

        return RiskResult(score=score, level=level, reasons=reasons)


if __name__ == "__main__":
    engine = RiskEngine()
    print(engine.assess(
        detection_confidence=0.9,
        speed_mps=18.0,
        radar_speed_mps=17.0,
        trajectory_risk=75.0,
        range_m=8.0,
    ).as_dict())
