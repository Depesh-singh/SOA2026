"""
SMART-SHIELD v3.0 ESP32 & LD2450 mmWave Radar Serial Interface
Decodes binary radar packets and sends actuation commands according to ICD.
"""

import struct
import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SmartShield.Hardware")

class LD2450RadarParser:
    """Parser for Hi-Link LD2450 24GHz mmWave radar target tracking frames."""
    HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])
    TAIL = bytes([0x55, 0xCC])
    FRAME_SIZE = 30  # 4B header + 3 * 8B targets + 2B tail

    @staticmethod
    def parse_frame(data: bytes) -> List[Dict[str, Any]]:
        """Parses a 30-byte binary frame into structured radar target dictionaries."""
        targets = []
        if len(data) < LD2450RadarParser.FRAME_SIZE:
            return targets

        # Check header and tail
        if data[:4] != LD2450RadarParser.HEADER or data[-2:] != LD2450RadarParser.TAIL:
            return targets

        # Parse 3 target slots (8 bytes each)
        for i in range(3):
            offset = 4 + i * 8
            raw_target = data[offset : offset + 8]
            
            x_raw, y_raw, speed_raw, resolution = struct.unpack("<hhhH", raw_target)
            
            # If distance is zero or unpopulated, skip slot
            if y_raw == 0 and x_raw == 0:
                continue

            x_m = x_raw / 1000.0          # Lateral distance in meters (-6m to +6m)
            y_m = y_raw / 1000.0          # Forward distance in meters (0 to 6m or scaled)
            speed_ms = speed_raw / 100.0   # Velocity in m/s (negative = approaching)
            
            # Compute polar coordinates
            distance_m = math.sqrt(x_m**2 + y_m**2)
            azimuth_rad = math.atan2(x_m, y_m)
            azimuth_deg = math.degrees(azimuth_rad)

            targets.append({
                "radar_slot": i + 1,
                "x_m": round(x_m, 2),
                "y_m": round(y_m, 2),
                "distance_m": round(distance_m, 2),
                "azimuth_deg": round(azimuth_deg, 2),
                "speed_ms": round(speed_ms, 2),
                "snr_resolution": resolution
            })

        return targets


class ESP32SerialController:
    """Manages serial communication with ESP32 for sensors and PCA9685 servos."""
    def __init__(self, port: str = "COM3", baudrate: int = 256000):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None

    def connect(self) -> bool:
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            logger.info(f"Connected to ESP32 on {self.port} @ {self.baudrate} bps")
            return True
        except Exception as e:
            logger.warning(f"ESP32 hardware serial not detected ({e}). Using mock/simulated mode.")
            return False

    def send_gimbal_command(self, pan_deg: float, tilt_deg: float, threat_level: str = "LOW", buzzer: bool = False):
        """Encodes and transmits gimbal positioning and alarm commands to ESP32."""
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        cmd_payload = {
            "cmd": "ACTUATE",
            "pan": round(pan_deg, 1),
            "tilt": round(tilt_deg, 1),
            "threat": threat_level,
            "buzzer": buzzer
        }
        try:
            import json
            msg = json.dumps(cmd_payload) + "\n"
            self.serial_conn.write(msg.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error writing to ESP32: {e}")

    def read_radar_data(self) -> List[Dict[str, Any]]:
        """Reads and parses raw incoming LD2450 radar packets from serial buffer."""
        if not self.serial_conn or not self.serial_conn.is_open:
            return []

        try:
            if self.serial_conn.in_waiting >= LD2450RadarParser.FRAME_SIZE:
                raw = self.serial_conn.read(LD2450RadarParser.FRAME_SIZE)
                return LD2450RadarParser.parse_frame(raw)
        except Exception as e:
            logger.error(f"Error reading serial radar data: {e}")
        return []
