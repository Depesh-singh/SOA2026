"""
SMART SHIELD - Event Logger

Stores AI-engine events as JSON Lines (.jsonl), one event per line.
This is useful for demonstrations, debugging and later model analysis.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class EventLogger:
    def __init__(self, log_dir: str | Path = "outputs/logs", filename: str = "events.jsonl"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / filename

    def log(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        record = {
            "timestamp": time.time(),
            "event_type": str(event_type),
            "data": data or {},
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_detection(
        self,
        track_id: int,
        confidence: float,
        speed_mps: Optional[float],
        risk: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.log(
            "drone_detection",
            {
                "track_id": int(track_id),
                "confidence": float(confidence),
                "speed_mps": None if speed_mps is None else float(speed_mps),
                "risk": risk or {},
            },
        )


if __name__ == "__main__":
    logger = EventLogger()
    logger.log("system_start", {"module": "smart_shield_ai"})
    logger.log_detection(1, 0.91, 12.4, {"score": 61, "level": "MEDIUM"})
    print(f"Log written to: {logger.path}")
