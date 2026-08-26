"""
SMART-SHIELD v3.0 Flight Kinematics & Multi-Target Scenario Simulator
Generates realistic multi-drone 3D trajectories for testing without live field targets.
"""

import math
import time
import random
from typing import List, Dict, Any

class ScenarioSimulator:
    """Simulates 3D kinematic drone trajectories matching SMART-SHIELD specifications."""
    def __init__(self):
        self.targets = [
            {
                "id": "DRONE-01",
                "classification": "Quadcopter",
                "x_m": 45.0,
                "y_m": 72.0,
                "z_m": 18.0,
                "vx_ms": 6.0,
                "vy_ms": -10.0,
                "vz_ms": 0.2,
                "optical_confidence": 0.94,
                "radar_snr": 85.0,
                "behavior_factor": 0.2
            },
            {
                "id": "DRONE-02",
                "classification": "Drone",
                "x_m": -85.0,
                "y_m": 95.0,
                "z_m": 25.0,
                "vx_ms": 14.0,
                "vy_ms": -12.0,
                "vz_ms": -0.4,
                "optical_confidence": 0.88,
                "radar_snr": 78.0,
                "behavior_factor": 0.4
            },
            {
                "id": "DRONE-03",
                "classification": "Drone (Hostile)",
                "x_m": -15.0,
                "y_m": 63.0,
                "z_m": 12.0,
                "vx_ms": 4.0,
                "vy_ms": -21.5,
                "vz_ms": -0.8,
                "optical_confidence": 0.98,
                "radar_snr": 96.0,
                "behavior_factor": 0.85
            }
        ]
        self.last_update = time.time()
        self.next_drone_idx = 4

    def update_simulation(self) -> List[Dict[str, Any]]:
        now = time.time()
        dt = max(0.01, min(0.1, now - self.last_update))
        self.last_update = now

        for t in self.targets:
            # Kinematic position update
            t["x_m"] += t["vx_ms"] * dt
            t["y_m"] += t["vy_ms"] * dt
            t["z_m"] += t["vz_ms"] * dt

            # Slight erratic noise for behavior factor
            if t["behavior_factor"] > 0.5:
                t["vx_ms"] += random.uniform(-1.5, 1.5) * dt
                t["vy_ms"] += random.uniform(-1.0, 1.0) * dt

            # Boundary turnaround to keep drones within monitored envelope
            dist = math.sqrt(t["x_m"]**2 + t["y_m"]**2)
            if dist > 180.0:
                t["vx_ms"] *= -0.9
                t["vy_ms"] *= -0.9
            elif t["y_m"] < 15.0:  # Base proximity rebound
                t["vy_ms"] = abs(t["vy_ms"])

            # Compute derived polar values
            r_horizontal = math.sqrt(t["x_m"]**2 + t["y_m"]**2)
            distance_3d = math.sqrt(t["x_m"]**2 + t["y_m"]**2 + t["z_m"]**2)
            azimuth_deg = math.degrees(math.atan2(t["x_m"], t["y_m"]))
            speed_3d = math.sqrt(t["vx_ms"]**2 + t["vy_ms"]**2 + t["vz_ms"]**2)
            heading_deg = math.degrees(math.atan2(t["vx_ms"], t["vy_ms"]))

            t["distance_m"] = round(distance_3d, 1)
            t["azimuth_deg"] = round(azimuth_deg, 1)
            t["speed_ms"] = round(speed_3d, 1)
            t["heading_deg"] = round(heading_deg, 1)

        return self.targets

    def add_intruder(self) -> Dict[str, Any]:
        """Injects a new simulated intruder into the perimeter."""
        new_target = {
            "id": f"DRONE-0{self.next_drone_idx}",
            "classification": random.choice(["Drone", "Quadcopter", "Fixed-Wing"]),
            "x_m": random.uniform(-120.0, 120.0),
            "y_m": random.uniform(110.0, 160.0),
            "z_m": random.uniform(15.0, 35.0),
            "vx_ms": random.uniform(-10.0, 10.0),
            "vy_ms": random.uniform(-18.0, -8.0),
            "vz_ms": random.uniform(-0.5, 0.5),
            "optical_confidence": round(random.uniform(0.85, 0.96), 2),
            "radar_snr": round(random.uniform(70.0, 95.0), 1),
            "behavior_factor": round(random.uniform(0.3, 0.8), 2)
        }
        self.next_drone_idx += 1
        self.targets.append(new_target)
        return new_target
