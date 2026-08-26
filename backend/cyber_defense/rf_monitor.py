"""
SMART-SHIELD v3.0 Cyber-Defence & RF Spectrum Monitor
Analyzes electromagnetic spectrum for jamming, signal spoofing, and unauthorized C2 links.
"""

import time
import random
import logging
from typing import Dict, List, Any
from ..config import config

logger = logging.getLogger("SmartShield.CyberRF")

class CyberRFMonitor:
    """Monitors RF spectrum power levels and executes defensive countermeasures."""
    def __init__(self):
        self.cfg = config.cyber_rf
        self.active_channel = self.cfg.default_c2_channel
        self.is_jamming_simulated = False
        self.last_hop_time = 0.0
        self.hop_history = []

    def get_spectrum_scan(self) -> Dict[str, Any]:
        """Generates real-time RF power levels across 2.4GHz - 5.8GHz channels."""
        channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 36, 40, 149, 153]
        power_levels = {}

        for ch in channels:
            # Baseline ambient noise
            noise = self.cfg.baseline_noise_floor_dbm + random.uniform(-2.0, 2.0)
            
            # Legitimate transmission power on active channel
            if ch == self.active_channel:
                noise += 25.0 + random.uniform(-1.0, 1.0)
            
            # Jamming injection across 2.4GHz spectrum
            if self.is_jamming_simulated and ch in [4, 5, 6, 7, 8]:
                noise += random.uniform(32.0, 42.0)  # Severe broadband jamming spike

            power_levels[ch] = round(noise, 1)

        # Anomaly evaluation
        active_noise = power_levels.get(self.active_channel, self.cfg.baseline_noise_floor_dbm)
        delta_db = active_noise - self.cfg.baseline_noise_floor_dbm
        
        jamming_detected = self.is_jamming_simulated or (delta_db > (self.cfg.jamming_delta_threshold_db + 20.0))
        
        if jamming_detected:
            status = "ATTACK_DETECTED"
            severity = "CRITICAL"
            event_type = "JAMMING_ATTEMPT"
            description = f"High broadband RF interference detected (+{round(delta_db, 1)} dB above floor). Control link degraded."
        else:
            status = "SECURE"
            severity = "INFO"
            event_type = "NOMINAL"
            description = f"RF spectrum nominal on CH {self.active_channel}. Noise floor at {round(self.cfg.baseline_noise_floor_dbm, 1)} dBm."

        return {
            "timestamp": time.time(),
            "status": status,
            "severity": severity,
            "event_type": event_type,
            "active_channel": self.active_channel,
            "noise_floor_dbm": round(self.cfg.baseline_noise_floor_dbm, 1),
            "current_rssi_dbm": round(active_noise, 1),
            "delta_db": round(delta_db, 1),
            "description": description,
            "spectrum_data": power_levels,
            "jamming_active": jamming_detected
        }

    def execute_frequency_hop(self) -> Dict[str, Any]:
        """Performs automatic frequency hop to an unjammed backup channel."""
        available_backups = [ch for ch in self.cfg.backup_channels if ch != self.active_channel]
        new_channel = random.choice(available_backups)
        old_channel = self.active_channel
        self.active_channel = new_channel
        self.last_hop_time = time.time()

        # If jamming was on the old channel, clear it
        if self.is_jamming_simulated:
            self.is_jamming_simulated = False

        event = {
            "event_type": "FREQUENCY_HOP",
            "old_channel": old_channel,
            "new_channel": new_channel,
            "timestamp": time.time(),
            "status": "SUCCESS",
            "message": f"Engaged dynamic frequency hopping from CH {old_channel} to CH {new_channel}."
        }
        self.hop_history.append(event)
        logger.info(event["message"])
        return event

    def toggle_jamming_simulation(self) -> bool:
        self.is_jamming_simulated = not self.is_jamming_simulated
        return self.is_jamming_simulated
