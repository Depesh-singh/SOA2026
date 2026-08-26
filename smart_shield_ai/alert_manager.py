"""
SMART SHIELD - Alert Manager

Handles alert state transitions for the dashboard/backend layer.
It does not directly control a siren, jammer, relay or other hardware.
Hardware actions should be connected only after the threat logic is
validated with real sensor data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class AlertState:
    level: str = "LOW"
    score: float = 0.0
    message: str = "No active threat"
    timestamp: float = 0.0


class AlertManager:
    """Convert risk results into stable alert states."""

    ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

    def __init__(self, hold_seconds: float = 1.0):
        self.hold_seconds = max(0.0, float(hold_seconds))
        self.state = AlertState(timestamp=time.time())
        self._candidate_level = "LOW"
        self._candidate_since = time.time()

    def update(self, level: str, score: float, reasons: Optional[list[str]] = None) -> AlertState:
        level = str(level).upper()
        if level not in self.ORDER:
            raise ValueError("level must be LOW, MEDIUM or HIGH")

        now = time.time()

        if level != self._candidate_level:
            self._candidate_level = level
            self._candidate_since = now

        # Avoid rapid alert oscillation.
        if (
            level == self.state.level
            or now - self._candidate_since >= self.hold_seconds
        ):
            self.state = AlertState(
                level=level,
                score=float(score),
                message=self._message(level, reasons or []),
                timestamp=now,
            )

        return self.state

    @staticmethod
    def _message(level: str, reasons: list[str]) -> str:
        if level == "HIGH":
            return "HIGH THREAT DETECTED"
        if level == "MEDIUM":
            return "MEDIUM THREAT - MONITOR"
        return "NO ACTIVE THREAT"

    def as_dict(self) -> dict:
        return {
            "level": self.state.level,
            "score": round(self.state.score, 2),
            "message": self.state.message,
            "timestamp": self.state.timestamp,
        }


if __name__ == "__main__":
    manager = AlertManager(hold_seconds=0)
    print(manager.update("LOW", 10).as_dict())
    print(manager.update("MEDIUM", 50, ["high_speed"]).as_dict())
    print(manager.update("HIGH", 85, ["close_range", "high_speed"]).as_dict())
