"""
SMART-SHIELD v3.0 Radar Interface Module
Re-exports the LD2450RadarParser and serial reader from esp32_serial.
"""

from .esp32_serial import LD2450RadarParser, ESP32SerialController

__all__ = ["LD2450RadarParser", "ESP32SerialController"]
