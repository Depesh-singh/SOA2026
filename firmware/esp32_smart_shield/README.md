# SMART-SHIELD v3.0: ESP32 Edge Firmware

This directory contains the production-ready microcontroller firmware for the **ESP32 Edge Sensor & Actuation Controller**.

---

## 1. Hardware Pinout & Wiring

| Peripheral / Sensor | ESP32 Pin | Interface Type | Electrical Notes |
|:---|:---|:---|:---|
| **LD2450 mmWave Radar** | `GPIO 16 (RX2)`<br>`GPIO 17 (TX2)` | UART (Serial2 @ 256000 bps) | 3.3V Logic, 5V VCC |
| **PCA9685 16-Ch PWM Driver** | `GPIO 21 (SDA)`<br>`GPIO 22 (SCL)` | I²C (0x40 address) | 3.3V Logic, 5V Servo V+ Rail |
| **SSD1306 OLED Display (128x64)**| `GPIO 21 (SDA)`<br>`GPIO 22 (SCL)` | I²C (0x3C address) | 3.3V Logic & VCC |
| **WS2812B RGB Status LEDs** | `GPIO 18` | Single-wire RMT / NeoPixel | 5V VCC, 3.3V Data |
| **Active Piezo Alarm Buzzer** | `GPIO 19` | Digital Output | 5V Active Piezo |
| **HC-SR04 Ultrasonic Sensor** | `GPIO 4 (Trig)`<br>`GPIO 5 (Echo)` | GPIO Pulse / Interrupt | 5V VCC (Use resistor divider on Echo to 3.3V) |
| **Battery Voltage Divider** | `GPIO 34 (ADC1_CH6)` | Analog In (0-3.3V) | 100kΩ / 22kΩ voltage divider from 12V rail |
| **Laptop AI Engine Link** | `USB-C / UART0` | USB CDC Serial @ 115200 bps | Bidirectional JSON telemetry & commands |

---

## 2. Required Arduino IDE Libraries

Install the following libraries via the Arduino Library Manager (`Ctrl + Shift + I`):
1. **ArduinoJson** by *Benoît Blanchon* (v6.x or v7.x)
2. **Adafruit PWM Servo Driver Library** by *Adafruit*
3. **Adafruit SSD1306** & **Adafruit GFX Library** by *Adafruit*
4. **Adafruit NeoPixel** by *Adafruit*

---

## 3. Flashing Instructions

1. Open `esp32_smart_shield.ino` in Arduino IDE or VS Code with Arduino extension.
2. Select Board: **ESP32 Dev Module** (or **ESP32-S3 Dev Module**).
3. Set Upload Speed: **921600** (or 115200).
4. Set Flash Frequency: **80MHz**.
5. Connect your ESP32 via USB-C and select the active COM port.
6. Click **Upload**.
7. Open Serial Monitor at **115200 baud** to verify initial telemetry broadcast.
