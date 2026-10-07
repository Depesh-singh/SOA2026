# VayuNetra — Servo Tracker Setup Guide

## Files Created

```
servo_tracker/
├── __init__.py                          # Python package marker
├── servo_controller.py                  # Main closed-loop servo controller
├── manual_test.py                       # Manual angle test script
├── auto_tracking_test.py                # Automatic closed-loop tracking test
└── esp32_tilt_receiver/
    └── esp32_tilt_receiver.ino          # ESP32 firmware (upload via Arduino IDE)
```

> [!IMPORTANT]
> **No existing VayuNetra code was modified.** This is a completely standalone module.

---

## Step 1: Upload ESP32 Firmware

### What you need:
- Arduino IDE installed
- ESP32 board support installed in Arduino IDE
- ESP32 connected via USB (COM5)

### Steps:
1. Open Arduino IDE
2. Go to **File → Open** and navigate to:
   ```
   C:\Users\Depesh\Downloads\SIH(ayush)\SIH\servo_tracker\esp32_tilt_receiver\esp32_tilt_receiver.ino
   ```
3. Select board: **Tools → Board → ESP32 Dev Module**
4. Select port: **Tools → Port → COM5**
5. **IMPORTANT**: Before uploading, hold the **BOOT** button on the ESP32
6. Click **Upload** (→ arrow button)
7. Release BOOT button when you see "Connecting..." in the console
8. Wait for "Done uploading"

### After upload:
- The ESP32 LED will blink (heartbeat)
- Open **Tools → Serial Monitor** at **115200 baud**
- You should see: `READY:90.0`
- Type `TILT:70` and press Enter → servo moves LEFT
- Type `TILT:120` and press Enter → servo moves RIGHT
- **Close Serial Monitor before running Python scripts** (only one program can use COM5)

---

## Step 2: Manual Test (verify servo directions)

**Close Arduino Serial Monitor first!**

```powershell
cd C:\Users\Depesh\Downloads\SIH(ayush)\SIH
python servo_tracker/manual_test.py
```

You will see a `TILT>` prompt. Type angles and verify:

| You type | Expected servo position |
|----------|------------------------|
| `70`     | Full LEFT              |
| `80`     | LEFT                   |
| `90`     | CENTER                 |
| `100`    | RIGHT                  |
| `120`    | Full RIGHT             |
| `sweep`  | Smooth sweep test      |
| `q`      | Quit (returns to 90°)  |

---

## Step 3: Automatic Tracking Test (closed-loop simulation)

```powershell
cd C:\Users\Depesh\Downloads\SIH(ayush)\SIH
python servo_tracker/auto_tracking_test.py
```

This simulates a drone moving across a 640px frame:
- Drone at center (x=320) → servo holds at 90°
- Drone moves left (x=100) → servo goes below 90°
- Drone moves right (x=550) → servo goes above 90°
- Drone returns to center → servo returns to ~90°
- Target lost → servo holds last position
- Smooth sweep → drone moves left-to-right continuously

You will see real-time debug output:
```
  TARGET: YES | X:  100 | CENTER: 320 | ERROR: -220 | DIR: LEFT            | SERVO: 82.5°
  TARGET: YES | X:  550 | CENTER: 320 | ERROR:  230 | DIR: RIGHT           | SERVO: 99.2°
  TARGET: YES | X:  315 | CENTER: 320 | ERROR:   -5 | DIR: CENTER (HOLD)   | SERVO: 90.0°
  TARGET: NO  | X:  --- | CENTER: 320 | ERROR:  --- | DIR: NO TARGET       | SERVO: 90.0°
```

---

## Step 4: Integration with Existing VayuNetra AI (Later)

When you are ready to connect this to your existing AI system, you only need to call:

```python
from servo_tracker.servo_controller import ServoTracker

tracker = ServoTracker(port="COM5")
tracker.start()

# Inside your detection loop (wherever target position is available):
tracker.update_target(target_center_x=cx, frame_width=640)

# When target is lost:
tracker.clear_target()

# On shutdown:
tracker.stop()
```

Your existing AI code remains **completely untouched**.

---

## Configurable Parameters

| Parameter          | Default | Description                                    |
|--------------------|---------|------------------------------------------------|
| `port`             | COM5    | Serial port for ESP32                          |
| `baudrate`         | 115200  | Serial baud rate                               |
| `center_angle`     | 90.0    | Servo center position (degrees)                |
| `min_angle`        | 70.0    | Minimum servo angle (LEFT limit)               |
| `max_angle`        | 120.0   | Maximum servo angle (RIGHT limit)              |
| `deadband_px`      | 30      | Pixels from center to ignore (hold steady)     |
| `max_step_deg`     | 3.0     | Max degrees the servo can move per update       |
| `gain`             | 0.04    | Degrees per pixel of error                     |
| `update_interval_ms` | 150   | Minimum time between servo commands (ms)       |
| `hold_on_lost`     | True    | Hold position when target lost (vs return to center) |

---

## Serial Protocol

```
Laptop → ESP32:    TILT:90.0\n
ESP32 → Laptop:    OK:90.0\n
```

Simple ASCII. No JSON. No binary framing.

---

## Architecture

```
┌──────────────────────┐
│  Existing VayuNetra  │
│  AI Detection Engine │
│  (UNTOUCHED)         │
│                      │
│  Output: target_x    │
└──────────┬───────────┘
           │
           │  tracker.update_target(cx, 640)
           ▼
┌──────────────────────┐
│  ServoTracker        │
│  (NEW — standalone)  │
│                      │
│  • Computes error    │
│  • Applies deadband  │
│  • Incremental step  │
│  • Rate-limited      │
└──────────┬───────────┘
           │
           │  TILT:85.0\n
           ▼
┌──────────────────────┐
│  USB Serial (COM5)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ESP32 Dev Module    │
│  esp32_tilt_receiver │
│                      │
│  GPIO 18 → PWM      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  MG996R Tilt Servo   │
└──────────────────────┘
```
