# SMART-SHIELD v3.0: Interface Control Document (ICD) & Hardware Integration

---

## 1. Hardware Pinout & Wiring Topology

### 1.1 ESP32 Microcontroller Interconnects

| Subsystem / Device | ESP32 Pin | Interface Type | Electrical Specs | Function |
|:---|:---|:---|:---|:---|
| **LD2450 mmWave Radar** | `GPIO 16 (RX2)`<br>`GPIO 17 (TX2)` | UART (Serial2) | 3.3V TTL, 256000 bps | Radar target point cloud & velocity stream |
| **PCA9685 PWM Driver** | `GPIO 21 (SDA)`<br>`GPIO 22 (SCL)` | I²C (0x40 address) | 3.3V Logic / 5V VCC | 12-bit PWM for Pan & Tilt Servos |
| **SSD1306 OLED Display** | `GPIO 21 (SDA)`<br>`GPIO 22 (SCL)` | I²C (0x3C address) | 3.3V Logic & VCC | Local Tactical Info (Status, Target count) |
| **RGB Alert LEDs (WS2812B)** | `GPIO 18` | Single-wire RMT | 5V VCC, 3.3V Data | Visual Status Ring (Green/Amber/Red strobe) |
| **Active Threat Buzzer** | `GPIO 19` | Digital Output / PWM | 5V Active Piezo | Audible Alarm on High Threat ($S_{threat} \ge 75$) |
| **Ultrasonic Sensor (HC-SR04)**| `GPIO 4 (Trig)`<br>`GPIO 5 (Echo)` | GPIO Pulse / Interrupt | 5V VCC, 3.3V divider | Low-altitude / Proximity backup sensing |
| **AI Engine / Laptop Link** | `USB-C / UART0` | USB CDC Serial / Wi-Fi | 115200 or 921600 bps | Telemetry stream & Gimbal control commands |

---

## 2. LD2450 mmWave Radar Serial Frame Protocol

The LD2450 transmits structured target packets every $100\text{ms}$ at `256000 bps` (`8-N-1`):

```
+---------------+---------------+--------------------+---------------+---------------+
| Header (4B)   | Target 1 (8B) | Target 2 (8B)      | Target 3 (8B) | Tail (2B)     |
| 0xAA FF 03 00 | X, Y, Speed, R| X, Y, Speed, R     | X, Y, Speed, R| 0x55 CC       |
+---------------+---------------+--------------------+---------------+---------------+
```

### Target Data Sub-Frame (8 Bytes per target):
1. **X Coordinate (2 Bytes, signed int16)**: Lateral position in millimeters ($\pm 6000\text{mm}$).
2. **Y Coordinate (2 Bytes, signed int16)**: Forward distance in millimeters ($0 - 6000\text{mm}$).
3. **Radial Speed (2 Bytes, signed int16)**: Velocity in $\text{cm/s}$ (negative = approaching, positive = receding).
4. **Distance Resolution / Confidence (2 Bytes, uint16)**: Target gate & SNR metric.

---

## 3. ESP32 $\longleftrightarrow$ AI Engine Serial & WebSocket Protocol

### 3.1 Telemetry Packet (ESP32 $\to$ Main Engine / JSON format)
```json
{
  "timestamp": 1723612800123,
  "system_status": "ARMED",
  "battery_voltage": 12.4,
  "rf_security": {
    "status": "SECURE",
    "noise_floor_dbm": -88.5,
    "jamming_detected": false,
    "active_channel": 6
  },
  "radar_targets": [
    {
      "id": 1,
      "x_mm": -850,
      "y_mm": 3420,
      "speed_cms": -240,
      "distance_mm": 3524,
      "azimuth_deg": -13.9
    }
  ],
  "gimbal_state": {
    "pan_deg": 90.0,
    "tilt_deg": 45.0
  }
}
```

### 3.2 Actuation Command Packet (Main Engine $\to$ ESP32)
```json
{
  "cmd": "GIMBAL_TRACK",
  "target_id": 3,
  "pan_angle": 105.4,
  "tilt_angle": 52.8,
  "threat_level": "HIGH",
  "buzzer_active": true,
  "led_color": "#FF0033"
}
```

---

## 4. Power Budget & Distribution Scheme

```
[ 12V Li-ion 4S Battery Pack / Power Supply (14.8V Nominal, 5000mAh) ]
                         |
                         +---> [ DC-DC Buck Converter 1 (12V -> 5V @ 5A) ] ---> Servos (PCA9685 V+ Rail) & Buzzer
                         |
                         +---> [ DC-DC Buck Converter 2 (12V -> 5V @ 3A) ] ---> ESP32, Camera, LD2450 Radar, OLED
                         |
                         +---> [ DC-DC / Pass-through to 5G Router / Laptop USB-PD ]
```
