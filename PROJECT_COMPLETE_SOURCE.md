# PROJECT COMPLETE SOURCE: SMART-SHIELD v3.0

## 1. PROJECT OVERVIEW

**SMART-SHIELD v3.0** is an integrated, low-cost, AI-powered multi-target aerial surveillance, tracking, and cyber-defence platform. It combines edge-based RF awareness, mmWave radar sensing (LD2450), high-resolution optical vision (YOLOv8 + ByteTrack), multi-sensor fusion (EKF), automated dual-axis optical pan/tilt tracking (PCA9685 PID), and edge alert mechanisms into a unified tactical defense solution.

- **Frontend Technology**: HTML5, Vanilla CSS, Vanilla JavaScript ES6+, HTML5 Canvas WebGL Radar & FLIR renderers, Web Audio API sound engine, WebSocket client.
- **Backend Technology**: Python 3.10+, FastAPI (AsyncIO Orchestration Hub), WebSockets (`/ws/telemetry`), OpenCV (`opencv-python`), PyTorch / Ultralytics (`ultralytics YOLOv8`), ByteTrack MOT.
- **Database & Storage**: Dual-tier storage supporting local SQLite persistent store (`database/smart_shield.db`), TimescaleDB / PostgreSQL time-series cluster, and high-speed in-memory circular ring buffer.
- **Microcontroller Firmware**: ESP32 Edge Firmware (`esp32_smart_shield.ino`), UART2 for LD2450 24GHz radar at 256000 bps, I2C for PCA9685 servo driver & SSD1306 OLED, RMT for WS2812B RGB LEDs, Active Piezo alarm buzzer.
- **APIs**: REST endpoints (`/api/status`, `/api/video_feed`, `/api/simulation/add_intruder`, `/api/cyber/toggle_jamming`, `/api/cyber/frequency_hop`, `/api/logs/export/csv`), WebSocket broadcast (`/ws/telemetry`).

---

## 2. PROJECT STRUCTURE

```text
SIH/
├── PRD_Product_Requirements_Document.md
├── TRD_Technical_Requirements_Document.md
├── ICD_Interface_Control_Document.md
├── SYSTEM_ARCHITECTURE_AND_EXECUTION_PLAN.md
├── yolov8n.pt (Binary Model Weight - Excluded)
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── js/
│       ├── gimbal_controls.js
│       ├── optical_hud.js
│       ├── radar_scope.js
│       └── rf_spectrum.js
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   ├── simulator.py
│   ├── cyber_defense/
│   │   ├── __init__.py
│   │   └── rf_monitor.py
│   ├── fusion/
│   │   ├── __init__.py
│   │   ├── ekf.py
│   │   ├── sensor_fusion.py
│   │   ├── state_estimator.py
│   │   ├── threat_matrix.py
│   │   └── trajectory_predictor.py
│   ├── gimbal/
│   │   ├── __init__.py
│   │   ├── pid.py
│   │   └── servo_control.py
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── esp32_serial.py
│   │   └── radar_interface.py
│   └── vision/
│       ├── __init__.py
│       ├── calibration.py
│       ├── detector.py
│       ├── tracker.py
│       └── velocity_estimator.py
├── database/
│   ├── __init__.py
│   ├── db_manager.py
│   └── schema.sql
├── firmware/
│   └── esp32_smart_shield/
│       ├── README.md
│       └── esp32_smart_shield.ino
└── tests/
    ├── __init__.py
    └── test_system.py
```

---

## 3. MASTER SOURCE CODE REPOSITORY

========================================================
FILE: PRD_Product_Requirements_Document.md
========================================================

```markdown
# SMART-SHIELD v3.0: Product Requirements Document (PRD)

---

## 1. Executive Summary & Vision
**SMART-SHIELD v3.0** is an integrated, low-cost, AI-powered multi-target aerial surveillance, tracking, and cyber-defence platform. It combines edge-based RF awareness, mmWave radar sensing (LD2450), high-resolution optical vision (YOLOv8 + ByteTrack), multi-sensor fusion, automated dual-axis optical pan/tilt tracking, and edge alert mechanisms into a unified tactical defense solution.

### Core Mission Statement:
> *"Detect earlier. Understand faster. Track continuously. Respond intelligently."*

---

## 2. Product Objectives & Target Personas

### 2.1 Objectives
* **Real-Time Multi-Target Aerial Detection**: Identify up to 10+ airborne targets simultaneously in the monitored zone with persistent IDs.
* **Sensor Fusion Accuracy**: Eliminate optical false alarms (e.g., birds, clouds) by correlating visual detections with 24GHz mmWave radar distance/velocity signatures.
* **Automated Threat Assessment**: Dynamically calculate multi-variable threat scores and autonomously cue mechanical Pan/Tilt optical cameras to track the highest-priority threat.
* **Cyber / RF Spectrum Defense**: Continuous detection of hostile electromagnetic anomalies (jamming, control link spoofing, unauthorized RF intrusions) to secure mission continuity.
* **Field Portability & Low-Cost Deployment**: Deliver military-grade situational awareness on cost-effective COTS (Commercial Off-The-Shelf) hardware and 5G connected infrastructure.

### 2.2 User Personas
1. **Field Tactical Operator**: Needs instantaneous visual/radar alerts, HUD tracking overlays, and manual/autonomous pan-tilt override.
2. **Base Security Commander**: Needs macro-level multi-drone tactical overview, incident audit logs, threat heatmaps, and RF integrity status.
3. **Cyber/Electronic Warfare Officer**: Requires real-time RF spectrum telemetry, signal anomaly warnings, and countermeasure control (frequency hopping, link strengthening).

---

## 3. Key Product Features & Scope

### 3.1 Multi-Modal Detection & Fusion
* **Visual Recognition**: YOLO-based aerial target detection (Drone, Quadcopter, Fixed-wing, Unknown/Bird) with confidence scoring.
* **mmWave Radar Tracking**: LD2450 24GHz sensor tracking radial distance ($r$), azimuth angle ($\theta$), and relative speed ($v$).
* **Sensor Fusion Engine**: Spatial-temporal alignment of radar coordinate vectors with camera bounding boxes using Extended Kalman Filtering (EKF).

### 3.2 Dynamic Threat Scoring & Target Prioritization
* Dynamic scoring formula evaluating:
  * Proximity ($D$)
  * Approach Velocity ($\vec{v}$)
  * Trajectory Vector relative to Protected Assets
  * Visual Classification Confidence ($C_{class}$)
  * Behavioral Anomaly / Erratic Maneuvering score ($B_{err}$)
* **Autonomous Actuation**: Directing PCA9685-driven pan/tilt servos to lock onto Target #01 (Highest Threat).

### 3.3 Cyber-Defence & Spectrum Awareness
* Real-time 2.4GHz / 5.8GHz / Sub-GHz RF spectrum scanner.
* Instant detection of RF Jamming (high noise floor), GPS/Signal Spoofing, and unauthorized C2 (Command & Control) RF links.
* Automated defensive countermeasures: frequency hopping / fallback channels, link hardening, and system-wide operator alarms.

### 3.4 Command & Control (C2) Operator Dashboard
* **Tactical Radar PPI Scope**: 360°/Sector radar sweep visualizer with target blips, velocity vectors, and threat color coding (Green: Low, Amber: Medium, Red: High).
* **Live Optical HUD Stream**: WebRTC/MJPEG video feed with persistent bounding boxes, targeting reticles, distance/speed overlays.
* **Cyber EW Spectrum Monitor**: Real-time FFT spectrum visualizer and threat status indicators.
* **Actuation Controls**: Auto-track toggle, manual Pan/Tilt virtual joystick, alert buzzer muting, and target lock selection.

---

## 4. Functional Requirements (FR)

| ID | Requirement | Priority | Acceptance Criteria |
|:---|:---|:---|:---|
| **FR-01** | Multi-Target Detection | P0 | System must track $\ge 3$ simultaneous targets without ID switching across frames. |
| **FR-02** | Sensor Fusion Latency | P0 | Camera + Radar fusion loop must execute at $\ge 25$ FPS with $<50\text{ms}$ pipeline latency. |
| **FR-03** | Priority Targeting Auto-Aim | P0 | Pan/tilt gimbal must reposition within $200\text{ms}$ of priority target re-ranking. |
| **FR-04** | RF Anomaly Trigger | P1 | RF jamming or rogue carrier spikes $>15\text{dB}$ above baseline must trigger alert within $500\text{ms}$. |
| **FR-05** | Remote 5G/Web Dashboard | P0 | Browser dashboard receives telemetry via WebSocket with $<100\text{ms}$ end-to-end latency. |
| **FR-06** | Hardware Status & Telemetry | P1 | ESP32 updates local OLED, RGB LED status indicator, and audible buzzer on threat state change. |
| **FR-07** | Incident Logging & Replay | P2 | Telemetry, optical snapshots, and RF events stored in timeseries database with playback capability. |

---

## 5. Non-Functional Requirements (NFR)

* **Performance & Frame Rate**: AI inference $\ge 30\text{ FPS}$ on GPU/Edge NPU; $\ge 15\text{ FPS}$ on standard CPU.
* **Reliability & Availability**: $99.9\%$ operational uptime under continuous field operation; automatic watchdog resets on ESP32.
* **Security**: AES-256 encrypted WebSocket/WebRTC communications; token-based API authentication for remote command links.
* **Power Efficiency**: Full-system operation on 12V Li-ion battery pack with $>4$ hours sustained field operation.
* **Environmental**: Operating temperature $-10^\circ\text{C}$ to $55^\circ\text{C}$ with internal fan cooling and IP64 splash-proof 3D enclosure.
```

========================================================
FILE: TRD_Technical_Requirements_Document.md
========================================================

```markdown
# SMART-SHIELD v3.0: Technical Requirements Document (TRD)

---

## 1. System Architecture & Component Diagram

```
+---------------------------------------------------------------------------------------+
|                                    SENSORY LAYER                                      |
|  +------------------------+  +------------------------+  +-------------------------+  |
|  | LD2450 mmWave Radar   |  | HD Optical Camera      |  | RF Spectrum / ESP32 RF  |  |
|  | (UART: 256000 bps)     |  | (UVC / RTSP / USB)     |  | (2.4/5.8 GHz Receiver)  |  |
|  +-----------+------------+  +-----------+------------+  +------------+------------+  |
+--------------|---------------------------|----------------------------|---------------+
               | UART                      | Frame Feed                 | SPI / ADC / I2C
+--------------v---------------------------v----------------------------v---------------+
|                              EDGE CONTROLLER & ACTUATION (ESP32)                      |
|  - Microcontroller: ESP32-WROOM-32 / ESP32-S3 (Dual-Core @ 240MHz)                    |
|  - Sensor Aggregation & Packet Serialization (JSON / Protobuf / Binary Frame)          |
|  - Actuation Driver: PCA9685 I2C 16-Channel 12-bit PWM -> Pan/Tilt Micro-Servos (MG996R)|
|  - Local HMI: 0.96" I2C SSD1306 OLED, WS2812B RGB Status LEDs, Active Piezo Buzzer   |
+------------------------------------------+--------------------------------------------+
                                           | USB Serial (CDC) / Wi-Fi / 5G Link (TCP/WS)
+------------------------------------------v--------------------------------------------+
|                          AI ENGINE & FUSION SERVER (LAPTOP / SBC)                     |
|  1. Vision Processing: YOLOv8 / YOLOv11 (TensorRT / ONNX Runtime)                     |
|  2. Multi-Object Tracking: ByteTrack / DeepSORT with Hungarian Association & Kalman   |
|  3. Radar-Camera Fusion: 3D-to-2D Coordinate Transformation & Extended Kalman Filter  |
|  4. Threat Scoring & Prioritization Engine (Vector Kinematics + Anomaly Scoring)     |
|  5. Cyber-Defence Analyzer: FFT Energy Profiling, Jamming/Spoofing Detector           |
|  6. Pan/Tilt PID Control Loop -> Serial/WS feedback to ESP32                          |
|  7. Real-Time Telemetry & Video Broadcaster (FastAPI + WebSockets + WebRTC)           |
+------------------------------------------+--------------------------------------------+
                                           | 5G / Local Gigabit Network (Secure WebSocket)
+------------------------------------------v--------------------------------------------+
|                        OPERATOR COMMAND & CONTROL DASHBOARD (FRONTEND)                |
|  - Interactive 360° Radar PPI Scope (HTML5 Canvas / WebGL)                            |
|  - Tactical HUD Optical Feed with Target Bounding Boxes, Threat Rings & Crosshairs    |
|  - RF Spectrum Waterfall & Cyber Anomaly Alert Panel                                  |
|  - Mission Telemetry, Target Prioritization Table & Manual/Auto Gimbal Controls       |
+---------------------------------------------------------------------------------------+
```

---

## 2. Deep Learning & Sensor Fusion Pipeline

### 2.1 Object Detection & Tracking
* **Detection Model**: YOLOv8n/s trained on aerial drone datasets (quadcopters, hexacopters, fixed-wing, drones, birds/false-positives).
  * Input Resolution: $640 \times 640$ pixels.
  * Target Latency: $\le 15\text{ms}$ on NVIDIA CUDA / $\le 35\text{ms}$ on CPU (ONNX Runtime).
* **Multi-Object Tracking (MOT)**: **ByteTrack**
  * Employs low-confidence association to maintain persistent IDs during partial occlusions or high-speed maneuvers.
  * State Vector: $x = [u, v, s, r, \dot{u}, \dot{v}, \dot{s}]^T$ where $(u,v)$ is bounding box center, $s$ is scale, $r$ is aspect ratio.

### 2.2 Radar-Camera Sensor Fusion
* **Coordinate Transformation**:
  $$\begin{bmatrix} X_c \\ Y_c \\ Z_c \end{bmatrix} = \mathbf{R}_{radar}^{cam} \begin{bmatrix} X_r \\ Y_r \\ Z_r \end{bmatrix} + \mathbf{T}_{radar}^{cam}$$
  Projected to image plane $(u, v)$:
  $$\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} \sim \mathbf{K} \begin{bmatrix} X_c \\ Y_c \\ Z_c \end{bmatrix}$$
* **Fusion Algorithm**:
  * **Extended Kalman Filter (EKF)** fusing visual centroid $(u, v)$ with Radar Range $(r)$, Azimuth $(\theta)$, and Radial Velocity $(v_r)$.
  * Fusion matching via Mahalanobis distance & Gating metric.

---

## 3. Mathematical Threat Scoring Model

The threat score $S_{threat} \in [0, 100]$ for each detected target $i$ is calculated continuously at 30Hz:

$$S_{threat}(i) = w_1 \cdot f_D(d_i) + w_2 \cdot f_V(v_i) + w_3 \cdot f_\theta(\alpha_i) + w_4 \cdot C_{class}(i) + w_5 \cdot B_{err}(i)$$

Where:
* **Distance Weight ($f_D$)**: $f_D(d_i) = \max\left(0, 1 - \frac{d_i}{D_{max}}\right) \times 100$ (closer targets yield higher threat).
* **Velocity Weight ($f_V$)**: $f_V(v_i) = \min\left(100, \frac{|v_i|}{V_{max}} \times 100\right)$ where incoming speed $>0$.
* **Trajectory Vector ($f_\theta$)**: $\alpha_i$ is angle between target velocity vector and defense perimeter centroid ($\cos \alpha_i \to 1$ for direct inbound).
* **Classification Confidence ($C_{class}$)**: Model probability $P(target == \text{'Drone'})$.
* **Erratic Behavior Factor ($B_{err}$)**: Rapid acceleration changes / non-ballistic high jerk indicator.
* **Weights**: $w_1 = 0.30, w_2 = 0.25, w_3 = 0.20, w_4 = 0.15, w_5 = 0.10$ ($\sum w_i = 1.0$).

### Threat Level Classification:
* **$S_{threat} \ge 75$**: **HIGH THREAT (RED)** $\to$ Trigger Auto-Lock Gimbal + Audio Alarm + Red Strobe.
* **$40 \le S_{threat} < 75$**: **MEDIUM THREAT (AMBER)** $\to$ Secondary tracking queue + Yellow Indicator.
* **$S_{threat} < 40$**: **LOW THREAT (GREEN)** $\to$ Monitor passively.

---

## 4. Cyber-Defence & RF Spectrum Monitoring Specifications

### 4.1 RF Detection Signatures
* **RF Jamming Detection**:
  * Measure Received Signal Strength Indicator (RSSI) / Noise Floor across 2.400–2.483 GHz and 5.725–5.850 GHz.
  * Jamming condition triggered if:
    $$\overline{\text{RSSI}}_{window} - \text{NoiseFloor}_{baseline} > 18\text{ dBm} \quad \text{across} \ge 3 \text{ contiguous channels}$$
* **Protocol & Control Link Anomaly**:
  * Detect non-standard modulation spikes, continuous unmodulated carrier waves, or frequency sweeping patterns.
  * Detect de-authentication / spoofing frames on 802.11 / proprietary drone telemetry protocols.

### 4.2 Automated Countermeasure Protocols
1. **Dynamic Frequency Hopping**: Shift C2 communication link to predefined backup channels upon jamming detection.
2. **RF Hardening & Gain Adjust**: Dynamically adjust LNA (Low Noise Amplifier) gain and switch to directional antenna array.
3. **Telemetry Redundancy**: Seamless failover to 5G cellular / encrypted Ethernet fallback link.

---

## 5. Actuation & Gimbal Control Loop

* **Actuator Hardware**: Dual-axis Pan (Azimuth: $0^\circ - 180^\circ$) & Tilt (Elevation: $15^\circ - 90^\circ$) servo assembly.
* **Driver Interface**: PCA9685 16-channel 12-bit I2C PWM driver at $50\text{Hz}$ update rate.
* **Tracking Controller**:
  * Proportional-Integral-Derivative (PID) closed-loop controller targeting optical frame center $(u_{target} - u_{center}, v_{target} - v_{center})$.
  * Radar coarse slewing $\to$ Camera fine PID visual servoing lock.
```

========================================================
FILE: ICD_Interface_Control_Document.md
========================================================

```markdown
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
```

========================================================
FILE: SYSTEM_ARCHITECTURE_AND_EXECUTION_PLAN.md
========================================================

```markdown
# SMART-SHIELD v3.0: Frontend, Backend & Database Architecture Plan

---

## 1. Full-Stack System Blueprint

```
+---------------------------------------------------------------------------------------------------+
|                                      OPERATOR FRONTEND (UI/UX)                                    |
|  +---------------------------+  +---------------------------+  +-------------------------------+  |
|  | Tactical 360° Radar Scope |  | Optical YOLO HUD Stream   |  | RF Spectrum & Cyber Monitor   |  |
|  | - Canvas/WebGL Radar PPI  |  | - WebRTC/MJPEG Video feed |  | - FFT Waterfall Graph         |  |
|  | - Sweeping Phosphor Line  |  | - Dynamic Bounding Boxes  |  | - Jamming/Spoofing Alerts     |  |
|  | - Multi-Target Blips & IDs|  | - Priority Lock Reticle   |  | - Frequency Hopping Status    |  |
|  +---------------------------+  +---------------------------+  +-------------------------------+  |
|  +---------------------------------------------------------------------------------------------+  |
|  | Target Prioritization Table | Manual Gimbal Joystick | System Health & 5G Telemetry Widget |  |
|  +---------------------------------------------------------------------------------------------+  |
+--------------------------------------------------^------------------------------------------------+
                                                   | Bi-directional WebSocket & REST APIs
+--------------------------------------------------v------------------------------------------------+
|                                    BACKEND APPLICATION SERVICES                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | FastAPI / AsyncIO Orchestration Hub                                                          |  |
|  |   * WebSocket Server (`/ws/telemetry`, `/ws/rf_stream`, `/ws/gimbal_control`)                |  |
|  |   * REST Endpoints (`/api/targets`, `/api/rf/mitigate`, `/api/logs`, `/api/config`)          |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                  |                                                |
|       +------------------------------------------+-----------------------------------------+      |
|       |                                          |                                         |      |
|  +----v--------------------+       +-------------v--------------+       +------------------v----+  |
|  | Computer Vision Engine  |       | Sensor Fusion & Threat Eval|       | Hardware I/O & Comm   |  |
|  | - YOLOv8 Inference      |       | - Radar-Camera EKF Fusion  |       | - ESP32 Serial Parser |  |
|  | - ByteTrack Tracker     |       | - Kinematic Vector Calc    |       | - LD2450 Radar Ingest |  |
|  | - Optical Feature Extr. |       | - Threat Scoring (0-100)   |       | - PCA9685 PID Gimbal  |  |
|  | - Target Classification |       | - Target Priority Arbiter  |       | - RF Spectrum Receiver|  |
|  +-------------------------+       +----------------------------+       +-----------------------+  |
+--------------------------------------------------^------------------------------------------------+
                                                   |
+--------------------------------------------------v------------------------------------------------+
|                                    DATABASE & STORAGE ARCHITECTURE                                |
|  +--------------------------------+  +--------------------------------+  +---------------------+  |
|  | Timeseries Telemetry Store     |  | Relational Audit & Events      |  | In-Memory Cache     |  |
|  | (PostgreSQL / TimescaleDB)     |  | (PostgreSQL / SQLite)          |  | (Redis / RAM Cache) |  |
|  | - 30Hz Target Trajectories     |  | - Target Classification Log    |  | - Active Target Ring|  |
|  | - Radar Points & Velocity      |  | - Cyber / RF Incident Log      |  | - Real-time Gimbal  |  |
|  | - RF Spectrum RSSI / FFT Scans |  | - Operator Action Audit Trail  |  | - Low-latency PubSub|  |
|  +--------------------------------+  +--------------------------------+  +---------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Frontend Architecture Plan

### 2.1 UI/UX Layout & Components
The Frontend is engineered as a high-density, mission-critical military C2 (Command & Control) dark-mode interface:

1. **Header Bar**:
   * System Armed/Standby Status, Defense Sector Selector, Master Alarm Badge, 5G Latency Counter ($<25\text{ms}$), Active Target Summary ($N=3$).
2. **Left Panel: Tactical Radar PPI Scope**:
   * Real-time $360^\circ$ circular scope with continuous rotating beam sweep.
   * Distance rings: $25\text{m}$, $50\text{m}$, $100\text{m}$, $150\text{m}$, $200\text{m}$.
   * Target blips color-coded by threat level (Green: Low, Orange: Medium, Red: High) with velocity tail vectors and persistent IDs (`ID:01`, `ID:02`, `ID:03`).
3. **Center Panel: Live Optical Video Feed (HUD)**:
   * Real-time RTSP/WebRTC video stream.
   * Overlay Canvas: Bounding boxes, classification badges, distance/speed indicators, and auto-aim target lock reticle on the highest threat.
4. **Right Top Panel: Cyber-Defence & RF Spectrum Analyzer**:
   * Live RF Spectrum frequency graph ($2.4\text{GHz} - 5.8\text{GHz}$) with peak power thresholds.
   * Jamming / Spoofing Anomaly status card with one-click **"Engage Frequency Hopping"** countermeasure trigger.
5. **Bottom Panel: Multi-Target Threat Prioritization Matrix**:
   * Tabular list ranking targets #01, #02, #03 by dynamic threat score ($S_{threat}$).
   * Manual "LOCK" button to override auto-tracking gimbal and select a specific target.
6. **Bottom Right Panel: Gimbal & Peripheral Hardware Controller**:
   * Pan/Tilt angle dials ($0-180^\circ$ Pan, $15-90^\circ$ Tilt).
   * Virtual Pan/Tilt joystick for manual override.
   * Buzzer mute toggle, RGB LED strobe mode selector.

---

## 3. Backend Architecture Plan

### 3.1 Core Processing Services (Python FastAPI + AsyncIO)

1. **`VisionPipelineWorker`**:
   * Reads video frames from hardware camera / RTSP stream.
   * Runs YOLOv8 tensor inference for aerial object detection (`drone`, `quadcopter`, `fixed-wing`, `bird`).
   * Passes bounding boxes to **ByteTrack** for persistent ID tracking across consecutive frames.
2. **`RadarIngestWorker`**:
   * Connects via asynchronous serial (`pyserial-asyncio`) to ESP32 / LD2450 mmWave radar at `256000 bps`.
   * Unpacks binary frame packets: target coordinates $(X, Y)$, radial velocities $(v_r)$, and SNR resolutions.
3. **`FusionAndThreatEngine`**:
   * Correlates visual detections with radar coordinates using an Extended Kalman Filter (EKF).
   * Evaluates the continuous threat score equation:
     $$S_{threat} = 0.30 f_D + 0.25 f_V + 0.20 f_\theta + 0.15 C_{class} + 0.10 B_{err}$$
   * Elects the **Primary Priority Target** ($ID_{pri}$).
4. **`GimbalPIDController`**:
   * Calculates required Pan ($\Delta \theta_x$) and Tilt ($\Delta \theta_y$) angular offsets to center $ID_{pri}$ in the optical frame.
   * Emits PWM servo correction commands to ESP32 / PCA9685 via serial/I2C.
5. **`CyberDefenceWorker`**:
   * Ingests RF spectrum power levels and RSSI metrics.
   * Triggers anomaly classification rules:
     * High broad-band noise $\to$ **RF Jamming Alert**.
     * Irregular packet injection / beacon flooding $\to$ **C2 Spoofing Alert**.
   * Dispatches automated countermeasure instructions (Channel Hop / Link Hardening).

---

## 4. Database Architecture & Data Schemas

### 4.1 Storage Strategy
* **In-Memory Cache (Redis)**: Live state of all currently active targets, current gimbal coordinates, and real-time alerts for $<5\text{ms}$ retrieval.
* **Timeseries Database (PostgreSQL / TimescaleDB)**: High-rate trajectory telemetry, RF spectrum scans, and sensor logs.
* **Relational Tables**: Target session records, cyber-attack incident logs, and operator audit trail.

### 4.2 Database Schema (SQL Definition)

```sql
-- 1. Target Sessions Table
CREATE TABLE targets (
    target_id VARCHAR(32) PRIMARY KEY,
    first_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    classification VARCHAR(32) NOT NULL, -- 'Quadcopter', 'Fixed-Wing', 'Drone', 'Unknown'
    initial_distance_m FLOAT,
    max_threat_score FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'ACTIVE' -- 'ACTIVE', 'NEUTRALIZED', 'LOST'
);

-- 2. Timeseries Target Telemetry
CREATE TABLE target_telemetry (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_id VARCHAR(32) REFERENCES targets(target_id) ON DELETE CASCADE,
    x_pos_m FLOAT NOT NULL,
    y_pos_m FLOAT NOT NULL,
    z_pos_m FLOAT,
    distance_m FLOAT NOT NULL,
    azimuth_deg FLOAT NOT NULL,
    elevation_deg FLOAT,
    speed_ms FLOAT NOT NULL,
    heading_deg FLOAT,
    optical_confidence FLOAT,
    radar_snr FLOAT,
    threat_score FLOAT NOT NULL,
    threat_level VARCHAR(10) NOT NULL -- 'LOW', 'MEDIUM', 'HIGH'
);
CREATE INDEX idx_telemetry_time_target ON target_telemetry (timestamp DESC, target_id);

-- 3. Cyber-Defence & RF Spectrum Anomaly Logs
CREATE TABLE cyber_rf_events (
    event_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(32) NOT NULL, -- 'JAMMING_ATTEMPT', 'SIGNAL_SPOOFING', 'UNAUTHORIZED_C2'
    frequency_mhz FLOAT NOT NULL,
    rssi_dbm FLOAT NOT NULL,
    noise_floor_delta_db FLOAT,
    severity VARCHAR(10) NOT NULL, -- 'WARNING', 'CRITICAL'
    countermeasure_taken VARCHAR(64), -- 'CHANNEL_HOP_CH11', 'ANTENNA_HARDENING', 'ALERT_OPERATOR'
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- 4. System & Hardware Audit Logs
CREATE TABLE system_audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    subsystem VARCHAR(32) NOT NULL, -- 'GIMBAL', 'ESP32', 'AI_ENGINE', 'POWER', 'OPERATOR'
    event_message TEXT NOT NULL,
    battery_voltage FLOAT,
    core_temp_c FLOAT,
    gimbal_pan_deg FLOAT,
    gimbal_tilt_deg FLOAT
);
```

---

## 5. Implementation Roadmap & Execution Phases

```
+------------------------------------------------------------------------------------+
| PHASE 1: Embedded & Hardware Control                                               |
| - ESP32 firmware for LD2450 mmWave parsing, PCA9685 servo control, OLED & buzzer  |
+------------------------------------------------------------------------------------+
                                          |
+-----------------------------------------v------------------------------------------+
| PHASE 2: AI Vision, Sensor Fusion & Threat Engine Backend                          |
| - YOLOv8 + ByteTrack detection & tracking pipeline                                 |
| - Camera-Radar coordinate fusion & Extended Kalman Filter                          |
| - Multi-target Threat Scoring & Pan/Tilt PID visual servoing loop                  |
| - Cyber-Defence RF anomaly detector & FastAPI WebSocket broadcaster               |
+------------------------------------------------------------------------------------+
                                          |
+-----------------------------------------v------------------------------------------+
| PHASE 3: Interactive Tactical Operator Dashboard (Frontend)                        |
| - 360° Radar PPI Scope with sweeping beam & multi-target blips                      |
| - Optical HUD Video Stream with YOLO target reticles & lock-on indicator           |
| - Cyber RF Spectrum waterfall monitor & countermeasure panel                       |
| - Target prioritization table & manual/auto gimbal controls                        |
+------------------------------------------------------------------------------------+
                                          |
+-----------------------------------------v------------------------------------------+
| PHASE 4: Database Integration & End-to-End Field Validation                        |
| - TimescaleDB/PostgreSQL telemetry logging & historical replay                      |
| - End-to-end hardware-in-the-loop validation & simulated multi-drone flight scenarios|
+------------------------------------------------------------------------------------+
```
```

========================================================
FILE: frontend/index.html
========================================================

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IAF STRATEGIC AIR COMMAND | Main Battle Operations Center</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&family=Orbitron:wght@600;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="cinematic-command-center">

  <!-- =========================================================================
       STRATEGIC AIR COMMAND & WAR ROOM HEADER (TOP GUN / NORAD BIG-BOARD)
       ========================================================================= -->
  <header class="warroom-header">
    <div class="header-left">
      <div class="iaf-emblem-wrap">
        <div class="iaf-roundel">
          <span class="ring-saffron"></span>
          <span class="ring-white"></span>
          <span class="ring-green"></span>
        </div>
        <div class="title-group">
          <div class="command-motto">भारतीय वायु सेना • STRATEGIC AIR COMMAND</div>
          <h1 class="main-screen-title">MAIN AIR DEFENCE BATTLE OPERATIONS CENTER <span class="badge-sector">WAC-ADS-04</span></h1>
          <div class="recon-sat-telemetry">
            <span id="backend-uplink-status">⚡ BACKEND C2: <strong class="text-amber">STANDALONE SIM</strong></span>
            <span class="sep">|</span>
            <span>🛰️ GSAT-7A RUKMANI: <strong class="text-cyan">UPLINK 100%</strong></span>
            <span class="sep">|</span>
            <span>🛰️ RISAT-2BR1 SAR: <strong class="text-green">PASS #4128 ACTIVE</strong></span>
            <span class="sep">|</span>
            <span>AFNET SECURE FIBRE: <strong class="text-cyan">11ms LATENCY</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- CENTER: GLOWING DEFCON & AIR DEFENCE ALERT DIAL -->
    <div class="header-center">
      <div class="defcon-module defcon-2-alert">
        <div class="defcon-label-bar">READINESS CONDITION</div>
        <div class="defcon-display">
          <div class="defcon-level">DEFCON 2</div>
          <div class="defcon-status-text">AIR DEFENCE ALERT (STATE RED)</div>
        </div>
        <div class="defcon-lights">
          <span class="d-light d-5">5</span>
          <span class="d-light d-4">4</span>
          <span class="d-light d-3">3</span>
          <span class="d-light d-2 active">2</span>
          <span class="d-light d-1">1</span>
        </div>
      </div>
    </div>

    <!-- RIGHT: MISSION CLOCKS & COMMS CONTROLS -->
    <div class="header-right">
      <div class="quad-clock-array">
        <div class="clock-cell">
          <span class="ck-label">ZULU (UTC)</span>
          <span id="clock-zulu" class="ck-val">07:15:32 Z</span>
        </div>
        <div class="clock-cell">
          <span class="ck-label">IST TIME</span>
          <span id="clock-ist" class="ck-val text-cyan">12:45:32 IST</span>
        </div>
        <div class="clock-cell">
          <span class="ck-label">MISSION ELAPSED</span>
          <span id="clock-met" class="ck-val text-green">+01:42:19</span>
        </div>
        <div class="clock-cell highlight-red">
          <span class="ck-label">INTERCEPT TTI</span>
          <span id="clock-tti" class="ck-val text-red">T-MINUS 00:01:45</span>
        </div>
      </div>

      <div class="header-audio-controls">
        <button class="btn-warroom btn-klaxon" id="btn-master-klaxon" onclick="toggleKlaxonAlert()">
          🚨 KLAXON: <span id="klaxon-status-text">ARMED</span>
        </button>
        <button class="btn-warroom btn-comms" id="btn-radio-comms" onclick="playRadioCommsBeep()">
          📻 COMMS BEEP
        </button>
      </div>
    </div>
  </header>

  <!-- =========================================================================
       MAIN MULTI-DISPLAY TACTICAL GRID (5 DEDICATED CINEMATIC ARRAYS)
       ========================================================================= -->
  <main class="warroom-grid">

    <!-- DISPLAY ARRAY 1: 3D GEOSPATIAL AIRSPACE VECTOR GRID ("THE BIG BOARD") -->
    <section class="c2-display-panel panel-big-board">
      <div class="display-panel-header">
        <div class="panel-tag-group">
          <span class="panel-icon">🌐</span>
          <h2>RECOGNIZED AIR SITUATION PICTURE (RASP) — 3D TACTICAL AIRSPACE</h2>
        </div>
        <div class="panel-pills">
          <span class="pill-mil">SENSOR: 3D CAR / LLLR MM-WAVE</span>
          <span class="pill-mil pill-pulse">● 30 RPM SWEEP</span>
          <span class="pill-mil">SAM ENVELOPE: ACTIVE</span>
        </div>
      </div>

      <div class="radar-scope-container">
        <canvas id="radarCanvas" width="480" height="480"></canvas>
        <div class="radar-hud-markings">
          <div class="bearing-mark mark-n">000° (NORTH)</div>
          <div class="bearing-mark mark-e">090° (EAST)</div>
          <div class="bearing-mark mark-s">180° (SOUTH)</div>
          <div class="bearing-mark mark-w">270° (WEST)</div>
          <div class="sam-legend-badge">
            <span class="dot-sam-akash"></span> AKASH SAM ZONE (120m) &nbsp;|&nbsp;
            <span class="dot-sam-dew"></span> DEW LASER KILL-ZONE (50m)
          </div>
        </div>
      </div>

      <!-- Real-time Track Vector Telemetry -->
      <div class="bigboard-telemetry-strip">
        <div class="strip-cell">
          <span class="sc-label">ACTIVE CONTACTS</span>
          <span class="sc-val text-cyan" id="track-count-val">03</span>
        </div>
        <div class="strip-cell">
          <span class="sc-label">PRIMARY HOSTILE</span>
          <span class="sc-val text-red" id="closest-range-val">65 m</span>
        </div>
        <div class="strip-cell">
          <span class="sc-label">CLOSURE VELOCITY</span>
          <span class="sc-val text-amber" id="max-closure-val">-21.5 m/s</span>
        </div>
        <div class="strip-cell">
          <span class="sc-label">TIME TO IMPACT (CPA)</span>
          <span class="sc-val text-red" id="tti-val">3.0 SEC</span>
        </div>
        <div class="strip-cell">
          <span class="sc-label">AIR DEFENCE THREAT</span>
          <span class="sc-val text-red" id="air-threat-level">CRITICAL (HIGH)</span>
        </div>
      </div>
    </section>

    <!-- DISPLAY ARRAY 2: MULTI-MODE EO/IR FLIR RECONNAISSANCE POD -->
    <section class="c2-display-panel panel-eoir-pod">
      <div class="display-panel-header">
        <div class="panel-tag-group">
          <span class="panel-icon">⌖</span>
          <h2>EO/IR FLIR TARGET RECONNAISSANCE POD</h2>
        </div>
        <!-- Multi-Spectral Vision Mode Switcher -->
        <div class="vision-mode-bar">
          <button class="btn-vision-mode active" id="mode-flir-white" onclick="setVisionMode('WHITE_HOT')">FLIR WHITE-HOT</button>
          <button class="btn-vision-mode" id="mode-flir-black" onclick="setVisionMode('BLACK_HOT')">FLIR BLACK-HOT</button>
          <button class="btn-vision-mode" id="mode-nvg" onclick="setVisionMode('NVG_GREEN')">NVG GREEN</button>
          <button class="btn-vision-mode" id="mode-optical" onclick="setVisionMode('DAY_OPTICAL')">DAY OPTICAL</button>
        </div>
      </div>

      <div class="optical-feed-container">
        <canvas id="opticalCanvas" width="660" height="420"></canvas>
        
        <!-- Tactical Cinema HUD Elements -->
        <div class="flir-cinematic-overlay">
          <!-- Top Telemetry Row -->
          <div class="flir-top-bar">
            <span>FCR AZ: <strong id="fcr-az-val">345.7°</strong></span>
            <span>FCR EL: <strong id="fcr-el-val">+10.5°</strong></span>
            <span>LRF: <strong class="text-green" id="lrf-status">65.2m [10Hz CONTINUOUS]</strong></span>
            <span>FOV: <strong id="zoom-text">4.0X OPTICAL</strong></span>
            <span>STABILIZATION: <strong class="text-cyan">3-AXIS GYRO LOCKED</strong></span>
          </div>

          <!-- Digital Zoom Controls -->
          <div class="flir-zoom-controls">
            <span class="zoom-label">MAG:</span>
            <button class="btn-zoom" onclick="setZoomLevel(1)">1X</button>
            <button class="btn-zoom active" onclick="setZoomLevel(4)">4X</button>
            <button class="btn-zoom" onclick="setZoomLevel(8)">8X</button>
            <button class="btn-zoom" onclick="setZoomLevel(16)">16X</button>
          </div>

          <!-- Laser Designator Arming Status -->
          <div class="laser-designator-box">
            <div class="designator-title">⚡ FIRE-CONTROL TARGET LOCK: TRK-103</div>
            <div class="designator-desc" id="designation-text">
              HOSTILE (BANDIT) • BRG 346° • RNG 65m • MACH 0.08 • LEAD SOLUTION COMPUTED
            </div>
            <div class="designator-status">LASER DESIGNATOR: ARMED • READY FOR ENGAGEMENT</div>
          </div>
        </div>
      </div>

      <!-- KILL CHAIN WEAPON ASSIGNMENT CONTROLS -->
      <div class="kill-chain-action-bar">
        <div class="directive-strip">
          <span>COMBAT ENGAGEMENT DIRECTIVE:</span>
          <strong class="text-red" id="directive-text">STANDBY — WEAPONS AUTHORIZED ON PRIMARY HOSTILE</strong>
        </div>
        <div class="weapon-action-grid">
          <button class="btn-combat btn-softkill" onclick="executeSoftKill()">
            ⚡ ENGAGE SOFT-KILL (RF DENIAL BEAM)
          </button>
          <button class="btn-combat btn-hardkill" onclick="executeHardKill()">
            💥 ENGAGE HARD-KILL (DEW LASER / MICRO-SAM)
          </button>
          <button class="btn-combat btn-scramble" onclick="scrambleInterceptor()">
            🚁 SCRAMBLE INTERCEPTOR (TRK-901)
          </button>
          <button class="btn-combat btn-bogie" onclick="simulateNewIntruder()">
            + INJECT BOGIE
          </button>
          <button class="btn-combat btn-warroom-cyan" style="background: rgba(0,240,255,0.15); border: 1px solid #00f0ff; color: #00f0ff; grid-column: span 2;" onclick="exportMissionReportCsv()">
            📊 EXPORT MISSION AUDIT CSV
          </button>
        </div>
      </div>
    </section>

    <!-- DISPLAY ARRAY 3: SQUADRON SCRAMBLE BOARD & SAM BATTERIES -->
    <section class="c2-display-panel panel-squadrons">
      <div class="display-panel-header">
        <div class="panel-tag-group">
          <span class="panel-icon">✈️</span>
          <h2>AIR DEFENCE SQUADRON &amp; BATTERY STATUS</h2>
        </div>
        <span class="pill-mil">SECTOR WAC READY</span>
      </div>

      <div class="squadron-board-list">
        <!-- Squadron 1: Rafale -->
        <div class="squad-card squad-active">
          <div class="squad-header">
            <div class="squad-name">NO. 17 SQN "GOLDEN ARROWS"</div>
            <span class="squad-badge badge-airborne">AIRBORNE (CAP)</span>
          </div>
          <div class="squad-meta">
            <span>AIRCRAFT: <strong>RAFALE DH (x2)</strong></span>
            <span>PAYLOAD: <strong>METEOR BVRAAM / MICA</strong></span>
          </div>
          <div class="squad-footer">
            <span>LOCATION: <strong>SECTOR NORTH PATROL</strong></span>
            <button class="btn-squad-order" onclick="vectorSquadron('GOLDEN ARROWS')">🎯 VECTOR TO INTERCEPT</button>
          </div>
        </div>

        <!-- Squadron 2: Su-30MKI -->
        <div class="squad-card">
          <div class="squad-header">
            <div class="squad-name">NO. 220 SQN "DESERT TIGERS"</div>
            <span class="squad-badge badge-alert">SCRAMBLE 2-MIN</span>
          </div>
          <div class="squad-meta">
            <span>AIRCRAFT: <strong>SU-30MKI (x2)</strong></span>
            <span>PAYLOAD: <strong>ASTRA MK-1 / R-77</strong></span>
          </div>
          <div class="squad-footer">
            <span>BASE: <strong>HALWARA AIR FORCE STATION</strong></span>
            <button class="btn-squad-order btn-order-scramble" onclick="vectorSquadron('DESERT TIGERS')">🚀 LAUNCH SCRAMBLE</button>
          </div>
        </div>

        <!-- SAM Battery 1: Akash-Prime -->
        <div class="squad-card">
          <div class="squad-header">
            <div class="squad-name">AIR DEFENCE BATTERY "AKASH-PRIME"</div>
            <span class="squad-badge badge-armed">WEAPONS FREE</span>
          </div>
          <div class="squad-meta">
            <span>SYSTEM: <strong>AKASH-NG / 3D CAR RADAR</strong></span>
            <span>MISSILE READY: <strong>3x ARMED IN CANISTER</strong></span>
          </div>
          <div class="squad-footer">
            <span>ENVELOPE: <strong>120m CLOSE-IN DEFENCE</strong></span>
            <button class="btn-squad-order" onclick="vectorSquadron('AKASH-PRIME')">🔒 AUTO-SLAVE FCR</button>
          </div>
        </div>

        <!-- Counter-Drone DEW Unit -->
        <div class="squad-card">
          <div class="squad-header">
            <div class="squad-name">TACTICAL COUNTER-UAS DEW UNIT</div>
            <span class="squad-badge badge-active">TRACK LOCK</span>
          </div>
          <div class="squad-meta">
            <span>SYSTEM: <strong>10kW DIRECTED ENERGY LASER</strong></span>
            <span>POWER LEVEL: <strong>98% CHARGED (CAPACITOR BANK)</strong></span>
          </div>
          <div class="squad-footer">
            <span>KILL-ZONE: <strong>50m VITAL POINT (VA/VP)</strong></span>
            <button class="btn-squad-order btn-order-fire" onclick="executeHardKill()">⚡ FIRE LASER PULSE</button>
          </div>
        </div>
      </div>
    </section>

    <!-- DISPLAY ARRAY 4: ESM ELECTRONIC WARFARE WATERFALL & ECCM -->
    <section class="c2-display-panel panel-esm-ew">
      <div class="display-panel-header">
        <div class="panel-tag-group">
          <span class="panel-icon">⚡</span>
          <h2>ESM WIDEBAND SPECTRUM WATERFALL &amp; ECCM</h2>
        </div>
        <span class="mil-status-tag tag-secure" id="esm-status-tag">SPECTRUM SECURE</span>
      </div>

      <div class="esm-waterfall-box">
        <div class="freq-band-ticks">
          <span>0.5 GHz (HF/VHF)</span>
          <span>1.2 GHz (GPS L2)</span>
          <span>1.5 GHz (GPS L1)</span>
          <span>2.4 GHz (C2)</span>
          <span>5.8 GHz (FLIR)</span>
          <span>6.0 GHz</span>
        </div>
        <canvas id="spectrumCanvas" width="400" height="150"></canvas>
      </div>

      <div class="esm-threat-alert-box" id="esm-alert-box">
        <div class="alert-icon">🛡️</div>
        <div class="alert-text">
          <h4 id="esm-alert-title">TACTICAL RF SPECTRUM NOMINAL</h4>
          <p id="esm-alert-desc">Noise floor baseline -88.5 dBm. No hostile jamming strobe or GPS spoofing detected.</p>
        </div>
      </div>

      <div class="eccm-action-buttons">
        <button class="btn-warroom btn-warroom-outline" id="btn-jam-sim" onclick="toggleHostileJamming()">
          ⚠️ SIMULATE HOSTILE JAMMING
        </button>
        <button class="btn-warroom btn-warroom-cyan" id="btn-eccm-hop" onclick="executeEccmFrequencyHop()">
          🔄 ENGAGE ECCM FREQUENCY HOPPING
        </button>
      </div>
    </section>

    <!-- DISPLAY ARRAY 5: TEWA MASTER AIR TRACK MATRIX -->
    <section class="c2-display-panel panel-bottom-tewa">
      <div class="display-panel-header">
        <div class="panel-tag-group">
          <span class="panel-icon">📋</span>
          <h2>TEWA (THREAT EVALUATION &amp; WEAPON ASSIGNMENT) MASTER AIR PICTURE MATRIX</h2>
        </div>
        <span class="pill-mil">CLASSIFICATION STANDARD: STANAG 1059 / MIL-STD-2525D</span>
      </div>

      <div class="tewa-table-wrap">
        <table class="tewa-table">
          <thead>
            <tr>
              <th>TRACK ID</th>
              <th>TACTICAL CALLSIGN</th>
              <th>CLASSIFICATION</th>
              <th>RANGE (RNG)</th>
              <th>BEARING (BRG)</th>
              <th>ALTITUDE (AGL)</th>
              <th>GROUND SPEED</th>
              <th>CLOSURE RATE</th>
              <th>TIME TO IMPACT (TTI)</th>
              <th>IFF INTERROGATION</th>
              <th>THREAT INDEX</th>
              <th>ASSIGNED FIRE-CONTROL</th>
              <th>COMBAT ACTION</th>
            </tr>
          </thead>
          <tbody id="tewa-table-body">
            <!-- Dynamically populated rows -->
          </tbody>
        </table>
      </div>
    </section>

  </main>

  <!-- JAVASCRIPT MODULES -->
  <script src="js/radar_scope.js"></script>
  <script src="js/optical_hud.js"></script>
  <script src="js/rf_spectrum.js"></script>
  <script src="js/gimbal_controls.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

========================================================
FILE: frontend/styles.css
========================================================

```css
/* ==========================================================================
   CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
   Aesthetics inspired by Top Gun: Maverick, Fighter (2024), NORAD, and S.H.I.E.L.D. C2
   ========================================================================== */

:root {
  --bg-deep-space: #03060a;
  --bg-panel: rgba(8, 14, 22, 0.94);
  --bg-panel-dark: rgba(4, 8, 14, 0.98);
  --bg-header: rgba(10, 18, 30, 0.98);

  --neon-cyan: #00f0ff;
  --neon-cyan-glow: rgba(0, 240, 255, 0.25);
  --neon-red: #ff1e38;
  --neon-red-glow: rgba(255, 30, 56, 0.4);
  --neon-amber: #ffaa00;
  --neon-green: #00ff66;
  --neon-green-glow: rgba(0, 255, 102, 0.2);

  --iaf-saffron: #ff9933;
  --iaf-white: #ffffff;
  --iaf-green: #138808;

  --border-mil: #142844;
  --border-active: #00f0ff;
  --border-red: #ff1e38;

  --text-main: #e2e8f0;
  --text-dim: #7e94b0;
  --text-muted: #3d506a;

  --font-mono: 'Share Tech Mono', monospace;
  --font-title: 'Rajdhani', sans-serif;
  --font-stencil: 'Orbitron', sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body.cinematic-command-center {
  background-color: var(--bg-deep-space);
  background-image: 
    radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.06) 0%, transparent 60%),
    radial-gradient(circle at 10% 40%, rgba(255, 30, 56, 0.04) 0%, transparent 50%),
    linear-gradient(rgba(3, 6, 10, 0.97), rgba(3, 6, 10, 0.97)),
    repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 240, 255, 0.015) 2px, rgba(0, 240, 255, 0.015) 4px);
  color: var(--text-main);
  font-family: var(--font-title);
  font-size: 13px;
  line-height: 1.35;
  min-height: 100vh;
  overflow-x: hidden;
  user-select: none;
}

/* ==========================================================================
   WAR ROOM STRATEGIC HEADER
   ========================================================================== */

.warroom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 18px;
  background: var(--bg-header);
  border-bottom: 2px solid var(--border-mil);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.9), inset 0 -1px 0 rgba(0, 240, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
}

.iaf-emblem-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.iaf-roundel {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--iaf-saffron);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  box-shadow: 0 0 16px rgba(255, 153, 51, 0.5);
}
.iaf-roundel .ring-white {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--iaf-white);
  position: absolute;
}
.iaf-roundel .ring-green {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--iaf-green);
  position: absolute;
}

.command-motto {
  font-family: var(--font-stencil);
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--iaf-saffron);
  font-weight: 700;
}

.main-screen-title {
  font-family: var(--font-stencil);
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 1.5px;
  color: #ffffff;
  line-height: 1.2;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
}

.badge-sector {
  background: rgba(0, 240, 255, 0.15);
  color: var(--neon-cyan);
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 2px;
  border: 1px solid var(--neon-cyan);
  vertical-align: middle;
  font-family: var(--font-mono);
}

.recon-sat-telemetry {
  display: flex;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 2px;
}
.recon-sat-telemetry .sep { color: var(--text-muted); }

/* DEFCON MODULE */
.defcon-module {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(14, 6, 10, 0.85);
  border: 1px solid var(--border-red);
  padding: 4px 16px;
  border-radius: 4px;
  box-shadow: 0 0 18px var(--neon-red-glow);
  position: relative;
}

.defcon-label-bar {
  font-family: var(--font-stencil);
  font-size: 8px;
  color: var(--text-dim);
  letter-spacing: 1.5px;
}

.defcon-display {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.defcon-level {
  font-family: var(--font-stencil);
  font-size: 18px;
  font-weight: 900;
  color: var(--neon-red);
  letter-spacing: 1px;
  text-shadow: 0 0 12px var(--neon-red);
}

.defcon-status-text {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.defcon-lights {
  display: flex;
  gap: 6px;
  margin-top: 2px;
}

.d-light {
  width: 14px;
  height: 6px;
  border-radius: 1px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 0px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.d-light.d-2.active {
  background: var(--neon-red);
  box-shadow: 0 0 10px var(--neon-red);
  border-color: #fff;
  animation: defconBlink 1s infinite;
}

@keyframes defconBlink {
  50% { opacity: 0.4; }
}

/* QUAD CLOCK ARRAY */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quad-clock-array {
  display: flex;
  gap: 8px;
  background: rgba(4, 8, 14, 0.8);
  border: 1px solid var(--border-mil);
  padding: 4px 10px;
  border-radius: 4px;
}

.clock-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 6px;
  border-right: 1px solid rgba(20, 40, 68, 0.6);
}
.clock-cell:last-child { border-right: none; }

.ck-label {
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}

.ck-val {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
}

.highlight-red {
  background: rgba(255, 30, 56, 0.15);
  border-radius: 2px;
}

.header-audio-controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-warroom {
  font-family: var(--font-title);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  border: 1px solid var(--border-mil);
  background: rgba(14, 24, 40, 0.9);
  color: var(--text-main);
  transition: all 0.15s ease;
}

.btn-warroom:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px var(--neon-cyan-glow);
}

.btn-klaxon {
  background: rgba(255, 30, 56, 0.25);
  border-color: var(--neon-red);
  color: #fff;
}
.btn-klaxon:hover {
  background: rgba(255, 30, 56, 0.45);
  box-shadow: 0 0 14px var(--neon-red-glow);
}

/* ==========================================================================
   MAIN MULTI-DISPLAY GRID LAYOUT
   ========================================================================= */

.warroom-grid {
  display: grid;
  grid-template-columns: 500px 1fr 400px;
  gap: 12px;
  padding: 12px;
}

.panel-bottom-tewa {
  grid-column: 1 / -1;
}

.c2-display-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-mil);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(14px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  position: relative;
}

.c2-display-panel::before {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 12px; height: 12px;
  border-top: 2px solid var(--neon-cyan);
  border-left: 2px solid var(--neon-cyan);
  pointer-events: none;
}
.c2-display-panel::after {
  content: '';
  position: absolute;
  bottom: 0; right: 0; width: 12px; height: 12px;
  border-bottom: 2px solid var(--neon-cyan);
  border-right: 2px solid var(--neon-cyan);
  pointer-events: none;
}

.display-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(12, 20, 32, 0.95);
  border-bottom: 1px solid var(--border-mil);
}

.panel-tag-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-tag-group h2 {
  font-family: var(--font-stencil);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #fff;
  text-transform: uppercase;
}

.panel-icon {
  color: var(--neon-cyan);
  font-size: 14px;
}

.panel-pills {
  display: flex;
  gap: 6px;
}

.pill-mil {
  font-family: var(--font-mono);
  font-size: 9px;
  background: rgba(20, 40, 68, 0.5);
  border: 1px solid var(--border-mil);
  padding: 2px 6px;
  border-radius: 2px;
  color: var(--text-dim);
}

.pill-pulse {
  background: rgba(0, 255, 102, 0.15);
  border-color: var(--neon-green);
  color: var(--neon-green);
  animation: radarPillPulse 1.2s infinite;
}

@keyframes radarPillPulse {
  50% { opacity: 0.4; }
}

/* ==========================================================================
   DISPLAY 1: 3D RASP RADAR SCOPE ("THE BIG BOARD")
   ========================================================================== */

.radar-scope-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px;
  background: radial-gradient(circle, #04120a 0%, #03070d 100%);
}

#radarCanvas {
  border-radius: 50%;
  border: 2px solid rgba(0, 255, 102, 0.4);
  box-shadow: 0 0 35px rgba(0, 255, 102, 0.15), inset 0 0 30px rgba(0, 255, 102, 0.08);
}

.radar-hud-markings {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
}

.bearing-mark {
  position: absolute;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--neon-green);
  font-weight: 700;
}
.mark-n { top: 12px; left: 50%; transform: translateX(-50%); }
.mark-s { bottom: 12px; left: 50%; transform: translateX(-50%); }
.mark-e { right: 14px; top: 50%; transform: translateY(-50%); }
.mark-w { left: 14px; top: 50%; transform: translateY(-50%); }

.sam-legend-badge {
  position: absolute;
  bottom: 10px;
  right: 12px;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid var(--border-mil);
  padding: 2px 8px;
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-dim);
}

.dot-sam-akash {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--neon-amber);
}
.dot-sam-dew {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--neon-red);
}

.bigboard-telemetry-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  padding: 8px 10px;
  background: rgba(6, 12, 20, 0.95);
  border-top: 1px solid var(--border-mil);
  text-align: center;
}

.strip-cell .sc-label {
  display: block;
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--text-dim);
}

.strip-cell .sc-val {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
}

.text-cyan { color: var(--neon-cyan); }
.text-red { color: var(--neon-red); }
.text-green { color: var(--neon-green); }
.text-amber { color: var(--neon-amber); }

/* ==========================================================================
   DISPLAY 2: MULTI-MODE EO/IR FLIR TARGET RECON POD
   ========================================================================== */

.vision-mode-bar {
  display: flex;
  gap: 4px;
}

.btn-vision-mode {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 2px;
  border: 1px solid var(--border-mil);
  background: rgba(14, 24, 40, 0.8);
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-vision-mode.active {
  background: var(--neon-cyan);
  color: #000;
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px var(--neon-cyan-glow);
}

.optical-feed-container {
  position: relative;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 420px;
}

#opticalCanvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.flir-cinematic-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
}

.flir-top-bar {
  position: absolute;
  top: 8px;
  left: 10px;
  display: flex;
  gap: 14px;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(0, 240, 255, 0.3);
  padding: 4px 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--neon-cyan);
}

.flir-zoom-controls {
  position: absolute;
  top: 8px;
  right: 10px;
  display: flex;
  gap: 4px;
  align-items: center;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid var(--border-mil);
  padding: 2px 6px;
  pointer-events: auto;
}

.zoom-label {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-dim);
}

.btn-zoom {
  font-family: var(--font-mono);
  font-size: 9px;
  padding: 2px 6px;
  background: rgba(14, 24, 40, 0.9);
  border: 1px solid var(--border-mil);
  color: var(--text-main);
  border-radius: 2px;
  cursor: pointer;
}

.btn-zoom.active {
  background: var(--neon-amber);
  color: #000;
  border-color: var(--neon-amber);
}

.laser-designator-box {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(255, 30, 56, 0.28);
  border: 1px solid var(--neon-red);
  padding: 6px 12px;
  border-radius: 3px;
  font-family: var(--font-mono);
}

.designator-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--neon-red);
  letter-spacing: 1px;
}

.designator-desc {
  font-size: 11px;
  color: #fff;
  margin: 2px 0;
}

.designator-status {
  font-size: 9px;
  color: var(--neon-amber);
}

/* KILL CHAIN ACTION BAR */
.kill-chain-action-bar {
  padding: 8px 12px;
  background: rgba(6, 12, 20, 0.95);
  border-top: 1px solid var(--border-mil);
}

.directive-strip {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 10px;
  margin-bottom: 6px;
}

.weapon-action-grid {
  display: grid;
  grid-template-columns: 1.4fr 1.4fr 1.2fr 0.8fr;
  gap: 8px;
}

.btn-combat {
  font-family: var(--font-title);
  font-size: 11px;
  font-weight: 700;
  padding: 6px 8px;
  border-radius: 3px;
  cursor: pointer;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  transition: all 0.15s ease;
}

.btn-softkill {
  background: rgba(0, 240, 255, 0.18);
  border: 1px solid var(--neon-cyan);
  color: var(--neon-cyan);
}
.btn-softkill:hover {
  background: var(--neon-cyan);
  color: #000;
  box-shadow: 0 0 12px var(--neon-cyan);
}

.btn-hardkill {
  background: rgba(255, 30, 56, 0.28);
  border: 1px solid var(--neon-red);
  color: #fff;
}
.btn-hardkill:hover {
  background: var(--neon-red);
  color: #fff;
  box-shadow: 0 0 15px var(--neon-red-glow);
}

.btn-scramble {
  background: rgba(255, 170, 0, 0.2);
  border: 1px solid var(--neon-amber);
  color: var(--neon-amber);
}
.btn-scramble:hover {
  background: var(--neon-amber);
  color: #000;
}

.btn-bogie {
  background: rgba(20, 40, 68, 0.6);
  border: 1px solid var(--border-mil);
  color: var(--text-main);
}
.btn-bogie:hover {
  background: rgba(0, 240, 255, 0.4);
}

/* ==========================================================================
   DISPLAY 3: SQUADRON SCRAMBLE BOARD & SAM BATTERIES
   ========================================================================== */

.squadron-board-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
}

.squad-card {
  background: rgba(6, 12, 20, 0.9);
  border: 1px solid var(--border-mil);
  padding: 8px 10px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.squad-card:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px var(--neon-cyan-glow);
}

.squad-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.squad-name {
  font-family: var(--font-stencil);
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.squad-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 700;
}

.badge-airborne { background: rgba(0, 255, 102, 0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
.badge-alert { background: rgba(255, 170, 0, 0.2); color: var(--neon-amber); border: 1px solid var(--neon-amber); }
.badge-armed { background: rgba(255, 30, 56, 0.25); color: var(--neon-red); border: 1px solid var(--neon-red); }
.badge-active { background: rgba(0, 240, 255, 0.2); color: var(--neon-cyan); border: 1px solid var(--neon-cyan); }

.squad-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-dim);
}

.squad-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  padding-top: 4px;
  border-top: 1px solid rgba(20, 40, 68, 0.5);
  font-family: var(--font-mono);
  font-size: 9px;
}

.btn-squad-order {
  font-family: var(--font-title);
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  background: rgba(0, 240, 255, 0.15);
  border: 1px solid var(--neon-cyan);
  color: var(--neon-cyan);
  border-radius: 2px;
  cursor: pointer;
}
.btn-squad-order:hover {
  background: var(--neon-cyan);
  color: #000;
}

.btn-order-scramble {
  background: rgba(255, 170, 0, 0.2);
  border-color: var(--neon-amber);
  color: var(--neon-amber);
}
.btn-order-scramble:hover {
  background: var(--neon-amber);
  color: #000;
}

.btn-order-fire {
  background: rgba(255, 30, 56, 0.3);
  border-color: var(--neon-red);
  color: #fff;
}
.btn-order-fire:hover {
  background: var(--neon-red);
  color: #fff;
}

/* ==========================================================================
   DISPLAY 4: ESM ELECTRONIC WARFARE & ECCM
   ========================================================================== */

.esm-waterfall-box {
  padding: 6px 10px;
  background: #020509;
}

.freq-band-ticks {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

#spectrumCanvas {
  width: 100%;
  background: #020509;
  border: 1px solid rgba(0, 240, 255, 0.25);
  border-radius: 3px;
}

.esm-threat-alert-box {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 6px 10px;
  padding: 6px 10px;
  background: rgba(0, 255, 102, 0.08);
  border: 1px solid var(--neon-green);
  border-radius: 3px;
  transition: all 0.25s ease;
}

.esm-threat-alert-box.threat-active {
  background: rgba(255, 30, 56, 0.22);
  border-color: var(--neon-red);
}

.alert-icon { font-size: 18px; }

.esm-threat-alert-box h4 {
  font-family: var(--font-title);
  font-size: 12px;
  color: var(--neon-green);
  font-weight: 700;
}

.esm-threat-alert-box.threat-active h4 { color: var(--neon-red); }

.esm-threat-alert-box p {
  font-size: 10px;
  color: var(--text-dim);
}

.eccm-action-buttons {
  display: flex;
  gap: 8px;
  padding: 0 10px 8px 10px;
}
.eccm-action-buttons .btn-warroom { flex: 1; font-size: 10px; }

.btn-warroom-outline {
  background: rgba(14, 24, 40, 0.8);
  border: 1px solid var(--border-mil);
}

.btn-warroom-cyan {
  background: rgba(0, 240, 255, 0.2);
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

/* ==========================================================================
   DISPLAY 5: TEWA MASTER AIR TRACK MATRIX
   ========================================================================== */

.tewa-table-wrap {
  padding: 8px 10px;
  overflow-x: auto;
}

.tewa-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 11px;
}

.tewa-table th {
  background: rgba(12, 20, 32, 0.95);
  color: var(--neon-cyan);
  text-align: left;
  padding: 6px 8px;
  border-bottom: 2px solid var(--border-mil);
  font-weight: 600;
  font-size: 10px;
  letter-spacing: 0.5px;
}

.tewa-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(20, 40, 68, 0.4);
  color: var(--text-main);
  white-space: nowrap;
}

.tewa-table tr:hover {
  background: rgba(0, 240, 255, 0.06);
}

.row-hostile-priority {
  background: rgba(255, 30, 56, 0.16);
  border-left: 3px solid var(--neon-red);
}

.tewa-badge {
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 700;
  font-size: 10px;
  display: inline-block;
}

.tewa-critical { background: rgba(255, 30, 56, 0.3); color: var(--neon-red); border: 1px solid var(--neon-red); }
.tewa-elevated { background: rgba(255, 170, 0, 0.3); color: var(--neon-amber); border: 1px solid var(--neon-amber); }
.tewa-nominal { background: rgba(0, 255, 102, 0.3); color: var(--neon-green); border: 1px solid var(--neon-green); }

.iff-hostile { color: var(--neon-red); font-weight: 700; }
.iff-suspect { color: var(--neon-amber); }
.iff-friendly { color: var(--neon-green); }
```

========================================================
FILE: frontend/app.js
========================================================

```javascript
/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Master State Coordinator & Air Defence Battle Manager
 */

class CinematicWarroomC2 {
  constructor() {
    this.tracks = [
      {
        trackId: 'TRK-101',
        callsign: 'SUSPECT (BOGIE-01)',
        classification: 'SUSPECT',
        x: -55.0,
        y: 95.0,
        z: 22.0,
        vx: 3.8,
        vy: -5.5,
        range: 109.7,
        bearing: 330.0,
        altitude: 22.0,
        speed: 6.7,
        closureRate: -5.5,
        threatScore: 56.4,
        threatCategory: 'ELEVATED',
        iffMode: 'MODE 4: UNRESPONSIVE',
        weaponAssigned: 'EO/IR FCR TRACKING'
      },
      {
        trackId: 'TRK-102',
        callsign: 'UNKNOWN CONTACT-02',
        classification: 'SUSPECT',
        x: 105.0,
        y: 125.0,
        z: 28.0,
        vx: -6.2,
        vy: -4.0,
        range: 163.2,
        bearing: 40.0,
        altitude: 28.0,
        speed: 7.4,
        closureRate: -5.1,
        threatScore: 44.0,
        threatCategory: 'ELEVATED',
        iffMode: 'MODE 4: NO SQUAWK',
        weaponAssigned: 'AKASH SAM MONITORING'
      },
      {
        trackId: 'TRK-103',
        callsign: 'HOSTILE (BANDIT-03)',
        classification: 'HOSTILE',
        x: -18.0,
        y: 62.0,
        z: 14.0,
        vx: 4.0,
        vy: -21.0,
        range: 64.5,
        bearing: 343.8,
        altitude: 14.0,
        speed: 21.4,
        closureRate: -21.0,
        threatScore: 92.5,
        threatCategory: 'CRITICAL',
        iffMode: 'MODE 4: HOSTILE EMISSION',
        weaponAssigned: 'DEW LASER / DIRECTED JAMMER ARMED'
      }
    ];

    this.primaryTrackId = 'TRK-103';
    this.gimbalPan = 343.8;
    this.gimbalTilt = 12.5;
    this.isJammingActive = false;
    this.activeChannel = 6;
    this.metSeconds = 6140; // 01:42:20
    this.ttiSeconds = 105;  // 00:01:45
    this.isBackendConnected = false;
    this.ws = null;

    this.initClocks();
    this.initWebSocket();
    this.startSimulationLoop();
  }

  initWebSocket() {
    const wsHost = (window.location.protocol === 'file:' || !window.location.host) ? 'localhost:8000' : (window.location.host.includes(':') ? window.location.host.split(':')[0] + ':8000' : window.location.host);
    const wsUrl = `ws://${wsHost}/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isBackendConnected = true;
        console.log("SMART-SHIELD C2 Backend WebSocket Connected.");
        this.updateConnectionBadge(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.handleBackendTelemetry(payload);
        } catch (e) {
          console.error("Telemetry parse error:", e);
        }
      };

      this.ws.onclose = () => {
        this.isBackendConnected = false;
        this.updateConnectionBadge(false);
        // Attempt reconnect after 3 seconds
        setTimeout(() => this.initWebSocket(), 3000);
      };

      this.ws.onerror = () => {
        this.isBackendConnected = false;
        this.updateConnectionBadge(false);
      };
    } catch (e) {
      this.isBackendConnected = false;
      this.updateConnectionBadge(false);
    }
  }

  updateConnectionBadge(connected) {
    const uplinkEl = document.getElementById('backend-uplink-status');
    if (uplinkEl) {
      if (connected) {
        uplinkEl.innerHTML = '⚡ BACKEND C2: <strong class="text-green">ONLINE (30Hz)</strong>';
      } else {
        uplinkEl.innerHTML = '⚡ BACKEND C2: <strong class="text-amber">STANDALONE SIM</strong>';
      }
    }
  }

  handleBackendTelemetry(payload) {
    if (!payload) return;

    // 1. Process Targets
    if (payload.targets && Array.isArray(payload.targets)) {
      this.tracks = payload.targets.map((t, idx) => {
        const tid = t.id || `TRK-10${idx + 1}`;
        const score = Math.round(t.threat_score || 0);
        const level = t.threat_level || (score >= 75 ? 'HIGH' : (score >= 40 ? 'MEDIUM' : 'LOW'));
        const category = level === 'HIGH' ? 'CRITICAL' : (level === 'MEDIUM' ? 'ELEVATED' : 'NOMINAL');
        const classification = t.classification || (level === 'HIGH' ? 'HOSTILE' : 'SUSPECT');

        return {
          trackId: tid,
          callsign: classification === 'HOSTILE' ? `HOSTILE (${tid})` : `SUSPECT (${tid})`,
          classification: classification.toUpperCase().includes('HOSTILE') ? 'HOSTILE' : 'SUSPECT',
          x: t.x_m || 0.0,
          y: t.y_m || 50.0,
          z: t.z_m || 15.0,
          vx: t.vx_ms || 0.0,
          vy: t.vy_ms || 0.0,
          range: t.distance_m || Math.hypot(t.x_m || 0, t.y_m || 50),
          bearing: t.azimuth_deg || 0.0,
          altitude: t.z_m || 15.0,
          speed: t.speed_ms || 15.0,
          closureRate: t.vy_ms || -15.0,
          threatScore: score,
          threatCategory: category,
          iffMode: level === 'HIGH' ? 'MODE 4: HOSTILE EMISSION' : 'MODE 4: NO SQUAWK',
          weaponAssigned: t.is_highest_priority ? 'DEW LASER / DIRECTED JAMMER ARMED' : 'EO/IR FCR MONITORING'
        };
      });
    }

    // 2. Process Primary Target Lock & Gimbal
    if (payload.primary_target) {
      this.primaryTrackId = payload.primary_target.id;
    }
    if (payload.gimbal) {
      this.gimbalPan = payload.gimbal.pan_deg || this.gimbalPan;
      this.gimbalTilt = payload.gimbal.tilt_deg || this.gimbalTilt;
    }

    // 3. Process Cyber RF State
    if (payload.cyber_rf) {
      this.isJammingActive = payload.cyber_rf.jamming_active || false;
      this.activeChannel = payload.cyber_rf.active_channel || 6;
    }

    // Render updated state
    this.render();
  }

  initClocks() {
    setInterval(() => {
      const now = new Date();
      const zulu = now.toISOString().substring(11, 19) + ' Z';
      const istOptions = { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
      const ist = now.toLocaleTimeString('en-GB', istOptions) + ' IST';

      this.metSeconds++;
      const metH = String(Math.floor(this.metSeconds / 3600)).padStart(2, '0');
      const metM = String(Math.floor((this.metSeconds % 3600) / 60)).padStart(2, '0');
      const metS = String(this.metSeconds % 60).padStart(2, '0');
      const met = `+${metH}:${metM}:${metS}`;

      if (this.ttiSeconds > 0) this.ttiSeconds--;
      const ttiM = String(Math.floor(this.ttiSeconds / 60)).padStart(2, '0');
      const ttiS = String(this.ttiSeconds % 60).padStart(2, '0');
      const tti = `T-MINUS 00:${ttiM}:${ttiS}`;

      const zuluEl = document.getElementById('clock-zulu');
      const istEl = document.getElementById('clock-ist');
      const metEl = document.getElementById('clock-met');
      const ttiEl = document.getElementById('clock-tti');

      if (zuluEl) zuluEl.innerText = zulu;
      if (istEl) istEl.innerText = ist;
      if (metEl) metEl.innerText = met;
      if (ttiEl) ttiEl.innerText = tti;
    }, 1000);
  }

  startSimulationLoop() {
    setInterval(() => {
      // Only execute local kinematics if backend is NOT connected
      if (!this.isBackendConnected) {
        this.updateKinematics(1 / 30);
        this.render();
      }
    }, 1000 / 30);
  }

  updateKinematics(dt) {
    this.tracks.forEach(track => {
      track.x += track.vx * dt;
      track.y += track.vy * dt;

      track.range = Math.hypot(track.x, track.y);
      track.bearing = (Math.atan2(track.x, track.y) * 180 / Math.PI + 360) % 360;
      track.speed = Math.hypot(track.vx, track.vy);
      track.closureRate = ((track.x * track.vx) + (track.y * track.vy)) / Math.max(track.range, 1);

      // Threat evaluation
      const distTerm = Math.max(0, 1 - (track.range / 200.0)) * 100;
      const speedTerm = Math.min(100, (track.speed / 25.0) * 100);
      const closureTerm = (track.closureRate < 0) ? Math.min(100, (Math.abs(track.closureRate) / 20.0) * 100) : 0;
      const hostileBonus = (track.classification === 'HOSTILE') ? 25 : 0;

      track.threatScore = Math.min(100, Math.round(
        (0.35 * distTerm) + (0.25 * speedTerm) + (0.25 * closureTerm) + (0.15 * hostileBonus)
      ));

      if (track.threatScore >= 75) {
        track.threatCategory = 'CRITICAL';
        track.classification = 'HOSTILE';
      } else if (track.threatScore >= 40) {
        track.threatCategory = 'ELEVATED';
      } else {
        track.threatCategory = 'NOMINAL';
      }

      if (track.range < 12 || track.range > 220) {
        track.vx = -track.vx * 0.8;
        track.vy = -track.vy * 0.8;
      }
    });

    this.tracks.sort((a, b) => b.threatScore - a.threatScore);
    if (this.tracks.length > 0) {
      this.primaryTrackId = this.tracks[0].trackId;
      this.gimbalPan = this.tracks[0].bearing;
      this.gimbalTilt = Math.atan2(this.tracks[0].z, this.tracks[0].range) * (180 / Math.PI);
    }
  }

  render() {
    if (window.cinematicRadar) {
      window.cinematicRadar.updateAndDraw(this.tracks, this.primaryTrackId);
    }

    if (window.cinematicOpticalFLIR) {
      window.cinematicOpticalFLIR.updateAndDraw(this.tracks, this.primaryTrackId, this.gimbalPan, this.gimbalTilt);
    }

    if (window.militaryESM) {
      window.militaryESM.updateAndDraw(this.isJammingActive, this.activeChannel);
    }

    this.updateTelemetryDom();
    this.updateTewaTableDom();
  }

  updateTelemetryDom() {
    const trackCountEl = document.getElementById('track-count-val');
    const closestRangeEl = document.getElementById('closest-range-val');
    const maxClosureEl = document.getElementById('max-closure-val');
    const ttiEl = document.getElementById('tti-val');
    const fcrAzEl = document.getElementById('fcr-az-val');
    const fcrElEl = document.getElementById('fcr-el-val');

    if (trackCountEl) trackCountEl.innerText = this.tracks.length < 10 ? `0${this.tracks.length}` : `${this.tracks.length}`;

    if (this.tracks.length > 0) {
      const primary = this.tracks[0];
      if (closestRangeEl) closestRangeEl.innerText = `${Math.round(primary.range)} m`;
      if (maxClosureEl) maxClosureEl.innerText = `${primary.closureRate.toFixed(1)} m/s`;
      
      const tti = Math.max(0.5, (primary.range / Math.max(Math.abs(primary.closureRate), 5.0))).toFixed(1);
      if (ttiEl) ttiEl.innerText = `${tti} SEC`;

      if (fcrAzEl) fcrAzEl.innerText = `${primary.bearing.toFixed(1)}°`;
      if (fcrElEl) fcrElEl.innerText = `+${Math.abs(this.gimbalTilt).toFixed(1)}°`;

      const desText = document.getElementById('designation-text');
      if (desText) {
        const mach = (primary.speed / 340.0).toFixed(2);
        desText.innerText = `${primary.trackId} • ${primary.callsign} • BRG ${Math.round(primary.bearing)}° • RNG ${Math.round(primary.range)}m • MACH ${mach} • LEAD COMPUTED`;
      }
    }
  }

  updateTewaTableDom() {
    const tbody = document.getElementById('tewa-table-body');
    if (!tbody) return;

    tbody.innerHTML = this.tracks.map(t => {
      const isPri = (t.trackId === this.primaryTrackId);
      const rowClass = isPri ? 'row-hostile-priority' : '';
      const badgeClass = t.threatCategory === 'CRITICAL' ? 'tewa-critical' : (t.threatCategory === 'ELEVATED' ? 'tewa-elevated' : 'tewa-nominal');
      const iffClass = t.classification === 'HOSTILE' ? 'iff-hostile' : (t.classification === 'SUSPECT' ? 'iff-suspect' : 'iff-friendly');
      const tti = Math.max(0.5, (t.range / Math.max(Math.abs(t.closureRate), 5.0))).toFixed(1);

      return `
        <tr class="${rowClass}">
          <td><strong>${t.trackId}</strong></td>
          <td><span class="${iffClass}">${t.callsign}</span></td>
          <td><span class="${iffClass}">${t.classification}</span></td>
          <td>${t.range.toFixed(1)} m</td>
          <td>${t.bearing.toFixed(1)}°</td>
          <td>${t.altitude.toFixed(0)} m</td>
          <td>${t.speed.toFixed(1)} m/s</td>
          <td><strong class="${t.closureRate < 0 ? 'text-red' : 'text-green'}">${t.closureRate.toFixed(1)} m/s</strong></td>
          <td>${tti}s</td>
          <td><span class="${iffClass}">${t.iffMode}</span></td>
          <td><span class="tewa-badge ${badgeClass}">${t.threatScore} / ${t.threatCategory}</span></td>
          <td><strong>${t.weaponAssigned}</strong></td>
          <td>
            <button class="btn-warroom btn-warroom-cyan" style="padding: 2px 8px; font-size: 10px;" onclick="selectPrimaryTrack('${t.trackId}')">
              ${isPri ? '🔒 LOCKED' : 'CUE FCR'}
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }
}

window.warroomC2 = new CinematicWarroomC2();

// OPERATOR ACTION HANDLERS

window.selectPrimaryTrack = function(trackId) {
  if (window.warroomC2) {
    window.warroomC2.primaryTrackId = trackId;
    if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();

    // If WebSocket is active, transmit manual lock command
    if (window.warroomC2.ws && window.warroomC2.ws.readyState === WebSocket.OPEN) {
      const trk = window.warroomC2.tracks.find(t => t.trackId === trackId);
      if (trk) {
        window.warroomC2.ws.send(JSON.stringify({
          cmd: "MANUAL_GIMBAL",
          pan: trk.bearing,
          tilt: Math.abs(window.warroomC2.gimbalTilt)
        }));
      }
    }
  }
};

window.setVisionMode = function(mode) {
  if (window.cinematicOpticalFLIR) {
    window.cinematicOpticalFLIR.setVisionMode(mode);
    if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();
  }
  // Update button active state
  document.querySelectorAll('.btn-vision-mode').forEach(btn => btn.classList.remove('active'));
  const btnMap = {
    'WHITE_HOT': 'mode-flir-white',
    'BLACK_HOT': 'mode-flir-black',
    'NVG_GREEN': 'mode-nvg',
    'DAY_OPTICAL': 'mode-optical'
  };
  const activeBtn = document.getElementById(btnMap[mode]);
  if (activeBtn) activeBtn.classList.add('active');
};

window.setZoomLevel = function(zoom) {
  if (window.cinematicOpticalFLIR) {
    window.cinematicOpticalFLIR.setZoomLevel(zoom);
    if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();
  }
  const zoomText = document.getElementById('zoom-text');
  if (zoomText) zoomText.innerText = `${zoom}.0X OPTICAL`;

  document.querySelectorAll('.btn-zoom').forEach(btn => {
    btn.classList.toggle('active', btn.innerText === `${zoom}X`);
  });
};

window.vectorSquadron = function(squadronName) {
  if (window.warroomAudio) {
    window.warroomAudio.playRadioCommsBeep();
    window.warroomAudio.playScrambleRoar();
  }
  const directiveEl = document.getElementById('directive-text');
  if (directiveEl) {
    directiveEl.innerText = `✈️ ${squadronName} VECTORING ON INTERCEPT BEARING 346° AT MACH 1.8`;
    directiveEl.className = 'text-green';
  }
};

window.executeSoftKill = function() {
  if (window.warroomAudio) window.warroomAudio.playSoftKillBeam();

  const directiveEl = document.getElementById('directive-text');
  if (directiveEl) {
    directiveEl.innerText = '⚡ DIRECTED RF JAMMER ACTIVE: INTRUDER C2 LINK SEVERED (FAILSAFE GROUNDING)';
    directiveEl.className = 'text-cyan';
  }

  if (window.warroomC2 && window.warroomC2.tracks.length > 0) {
    const target = window.warroomC2.tracks[0];
    target.vx *= 0.2;
    target.vy *= 0.2;
    target.callsign = 'NEUTRALIZED (LANDING)';
    target.classification = 'SUSPECT';
    target.weaponAssigned = 'RF DISRUPTED (GROUNDING)';
    target.threatScore = 18;
    target.threatCategory = 'NOMINAL';
  }
};

window.executeHardKill = function() {
  if (window.warroomAudio) window.warroomAudio.playHardKillLaser();

  const directiveEl = document.getElementById('directive-text');
  if (directiveEl) {
    directiveEl.innerText = '💥 DIRECTED ENERGY WEAPON FIRED: TARGET DESTROYED IN AIRSPACE';
    directiveEl.className = 'text-red';
  }

  if (window.warroomC2 && window.warroomC2.tracks.length > 0) {
    const target = window.warroomC2.tracks[0];
    target.callsign = '💥 DESTROYED (KINETIC)';
    setTimeout(() => {
      window.warroomC2.tracks = window.warroomC2.tracks.filter(t => t.trackId !== target.trackId);
    }, 800);
  }
};

window.scrambleInterceptor = function() {
  if (!window.warroomC2) return;
  if (window.warroomAudio) {
    window.warroomAudio.playRadioCommsBeep();
    window.warroomAudio.playScrambleRoar();
  }
  const interceptorId = `TRK-90${window.warroomC2.tracks.length + 1}`;
  window.warroomC2.tracks.push({
    trackId: interceptorId,
    callsign: 'FRIENDLY (QRF INTERCEPTOR)',
    classification: 'FRIENDLY',
    x: 12.0,
    y: 12.0,
    z: 28.0,
    vx: -9.0,
    vy: 19.0,
    range: 16.9,
    bearing: 45.0,
    altitude: 28.0,
    speed: 21.0,
    closureRate: 14.0,
    threatScore: 5,
    threatCategory: 'NOMINAL',
    iffMode: 'MODE 5: SQUAWK AUTHENTICATED',
    weaponAssigned: 'INTERCEPT VECTOR'
  });
};

window.simulateNewIntruder = function() {
  if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();

  // If backend connected, call backend API
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/simulation/add_intruder`, { method: 'POST' })
    .catch(() => {
      // Fallback local injection
      if (!window.warroomC2) return;
      const newId = `TRK-10${window.warroomC2.tracks.length + 1}`;
      window.warroomC2.tracks.push({
        trackId: newId,
        callsign: 'HOSTILE (BANDIT)',
        classification: 'HOSTILE',
        x: (Math.random() * 120) - 60,
        y: 140.0 + (Math.random() * 40),
        z: 16.0 + Math.random() * 10,
        vx: (Math.random() * 12) - 6,
        vy: -(16.0 + Math.random() * 12),
        range: 165.0,
        bearing: 348.0,
        altitude: 18.0,
        speed: 23.0,
        closureRate: -21.0,
        threatScore: 88,
        threatCategory: 'CRITICAL',
        iffMode: 'MODE 4: NO SQUAWK',
        weaponAssigned: 'FCR SLEWING'
      });
    });
};

window.toggleHostileJamming = function() {
  if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();

  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/cyber/toggle_jamming`, { method: 'POST' })
    .catch(() => {});

  if (window.warroomC2) {
    window.warroomC2.isJammingActive = !window.warroomC2.isJammingActive;
  }

  const alertBox = document.getElementById('esm-alert-box');
  const alertTitle = document.getElementById('esm-alert-title');
  const alertDesc = document.getElementById('esm-alert-desc');
  const statusTag = document.getElementById('esm-status-tag');
  const btnJam = document.getElementById('btn-jam-sim');

  if (window.warroomC2 && window.warroomC2.isJammingActive) {
    if (alertBox) alertBox.classList.add('threat-active');
    if (alertTitle) alertTitle.innerText = '⚠️ HOSTILE ELECTRONIC ATTACK DETECTED';
    if (alertDesc) alertDesc.innerText = 'High-power broadband barrage jamming strobe on 2.4GHz / GPS L1. SNR degraded by +28dB.';
    if (statusTag) { statusTag.innerText = 'SPECTRUM COMPROMISED'; statusTag.className = 'mil-status-tag mil-badge-live'; }
    if (btnJam) btnJam.innerText = '🛑 TERMINATE JAMMING ATTACK';
  } else {
    if (alertBox) alertBox.classList.remove('threat-active');
    if (alertTitle) alertTitle.innerText = 'TACTICAL RF SPECTRUM NOMINAL';
    if (alertDesc) alertDesc.innerText = 'Noise floor baseline -88.5 dBm. No hostile jamming strobe or spoofed GPS signal detected on operational bands.';
    if (statusTag) { statusTag.innerText = 'SPECTRUM SECURE'; statusTag.className = 'mil-status-tag tag-secure'; }
    if (btnJam) btnJam.innerText = '⚠️ SIMULATE HOSTILE JAMMING';
  }
};

window.executeEccmFrequencyHop = function() {
  if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();

  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/cyber/frequency_hop`, { method: 'POST' })
    .catch(() => {});

  const channels = [11, 24, 38, 14, 28];
  if (window.warroomC2) {
    window.warroomC2.activeChannel = channels[Math.floor(Math.random() * channels.length)];
    window.warroomC2.isJammingActive = false;
  }

  const alertBox = document.getElementById('esm-alert-box');
  const alertTitle = document.getElementById('esm-alert-title');
  const alertDesc = document.getElementById('esm-alert-desc');
  const statusTag = document.getElementById('esm-status-tag');
  const btnJam = document.getElementById('btn-jam-sim');

  if (alertBox) alertBox.classList.remove('threat-active');
  if (alertTitle) alertTitle.innerText = `🔄 ECCM FREQUENCY HOP EXECUTED: CH-${window.warroomC2 ? window.warroomC2.activeChannel : 11}`;
  if (alertDesc) alertDesc.innerText = `AFNET tactical link secured on Frequency Agility Channel. Direct-sequence spread-spectrum lock active.`;
  if (statusTag) { statusTag.innerText = 'ECCM LINK SECURED'; statusTag.className = 'mil-status-tag tag-secure'; }
  if (btnJam) btnJam.innerText = '⚠️ SIMULATE HOSTILE JAMMING';
};

window.exportMissionReportCsv = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  window.open(`${apiBase}/api/logs/export/csv`, '_blank');
};

window.toggleKlaxonAlert = function() {
  if (!window.warroomAudio) return;
  const statusText = document.getElementById('klaxon-status-text');
  if (window.warroomAudio.isKlaxonPlaying) {
    window.warroomAudio.stopAdaKlaxon();
    if (statusText) statusText.innerText = 'MUTED';
  } else {
    window.warroomAudio.startAdaKlaxon();
    if (statusText) statusText.innerText = 'ARMED (ACTIVE)';
  }
};

window.playRadioCommsBeep = function() {
  if (window.warroomAudio) window.warroomAudio.playRadioCommsBeep();
};

```

========================================================
FILE: frontend/js/radar_scope.js
========================================================

```javascript
/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Display Array 1: 3D Geospatial Airspace Vector Grid & Tactical RASP ("The Big Board")
 * Features SAM Threat Bubbles, Dynamic Intercept Curves & MIL-STD-2525D Symbology
 */

class CinematicRadarBigBoard {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.centerX = this.width / 2;
    this.centerY = this.height / 2;
    this.maxRadius = (this.width / 2) - 25;
    this.sweepAngle = 0;
    this.sweepSpeed = 0.04; // 30 RPM
    this.maxRangeMeters = 200.0;

    // SAM Threat Bubble Radii
    this.dewRadiusMeters = 50.0;
    this.akashSamRadiusMeters = 120.0;
  }

  updateAndDraw(tracks, primaryTrackId) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Perspective 3D Vector Grid
    this.drawTacticalVectorGrid(ctx);

    // 2. Concentric Range Rings
    this.drawRangeRings(ctx);

    // 3. Surface-to-Air Missile (SAM) Threat Engagement Bubbles
    this.drawSamThreatBubbles(ctx);

    // 4. Azimuth Crosshairs & Compass Rose
    this.drawCompassRose(ctx);

    // 5. Phosphor Radar Sweep
    this.drawSweepBeam(ctx);

    // 6. Dynamic Intercept Splines & Predicted Trajectories
    this.drawInterceptTrajectories(ctx, tracks, primaryTrackId);

    // 7. Tactical Air Tracks (MIL-STD-2525D Symbology)
    this.drawAirTracks(ctx, tracks, primaryTrackId);

    // Advance sweep angle
    this.sweepAngle += this.sweepSpeed;
    if (this.sweepAngle >= Math.PI * 2) {
      this.sweepAngle -= Math.PI * 2;
    }
  }

  drawTacticalVectorGrid(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.06)';
    ctx.lineWidth = 1;

    // Isometric grid lines across the scope
    const step = 40;
    for (let x = 0; x <= this.width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0); ctx.lineTo(x, this.height);
      ctx.stroke();
    }
    for (let y = 0; y <= this.height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y); ctx.lineTo(this.width, y);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawRangeRings(ctx) {
    const rings = [50, 100, 150, 200];
    ctx.save();

    rings.forEach(rng => {
      const r = (rng / this.maxRangeMeters) * this.maxRadius;
      ctx.beginPath();
      ctx.arc(this.centerX, this.centerY, r, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(0, 255, 102, 0.2)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Range Label
      ctx.fillStyle = 'rgba(0, 255, 102, 0.7)';
      ctx.font = '9px "Share Tech Mono"';
      ctx.fillText(`${rng}m`, this.centerX + 5, this.centerY - r + 11);
    });
    ctx.restore();
  }

  drawSamThreatBubbles(ctx) {
    ctx.save();
    // 1. Akash SAM Engagement Zone (120m)
    const rAkash = (this.akashSamRadiusMeters / this.maxRangeMeters) * this.maxRadius;
    ctx.beginPath();
    ctx.setLineDash([6, 6]);
    ctx.arc(this.centerX, this.centerY, rAkash, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 170, 0, 0.45)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255, 170, 0, 0.03)';
    ctx.fill();

    // 2. DEW Laser Close-In Kill Zone (50m)
    const rDew = (this.dewRadiusMeters / this.maxRangeMeters) * this.maxRadius;
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.arc(this.centerX, this.centerY, rDew, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 30, 56, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255, 30, 56, 0.05)';
    ctx.fill();

    ctx.restore();
  }

  drawCompassRose(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
    ctx.lineWidth = 1;

    // Major Axis
    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY - this.maxRadius);
    ctx.lineTo(this.centerX, this.centerY + this.maxRadius);
    ctx.moveTo(this.centerX - this.maxRadius, this.centerY);
    ctx.lineTo(this.centerX + this.maxRadius, this.centerY);
    ctx.stroke();

    // Minor Angle Ticks (every 30 degrees)
    for (let deg = 0; deg < 360; deg += 30) {
      const rad = (deg * Math.PI) / 180;
      const x1 = this.centerX + Math.cos(rad) * (this.maxRadius - 6);
      const y1 = this.centerY + Math.sin(rad) * (this.maxRadius - 6);
      const x2 = this.centerX + Math.cos(rad) * this.maxRadius;
      const y2 = this.centerY + Math.sin(rad) * this.maxRadius;

      ctx.beginPath();
      ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawSweepBeam(ctx) {
    ctx.save();
    const grad = ctx.createRadialGradient(
      this.centerX, this.centerY, 5,
      this.centerX, this.centerY, this.maxRadius
    );
    grad.addColorStop(0, 'rgba(0, 255, 102, 0.45)');
    grad.addColorStop(0.8, 'rgba(0, 255, 102, 0.08)');
    grad.addColorStop(1, 'rgba(0, 255, 102, 0.0)');

    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY);
    ctx.arc(this.centerX, this.centerY, this.maxRadius, this.sweepAngle - 0.32, this.sweepAngle, false);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // High intensity leading edge
    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY);
    ctx.lineTo(
      this.centerX + Math.cos(this.sweepAngle) * this.maxRadius,
      this.centerY + Math.sin(this.sweepAngle) * this.maxRadius
    );
    ctx.strokeStyle = 'rgba(0, 255, 102, 0.95)';
    ctx.lineWidth = 1.8;
    ctx.shadowColor = 'rgba(0, 255, 102, 0.8)';
    ctx.shadowBlur = 8;
    ctx.stroke();
    ctx.restore();
  }

  drawInterceptTrajectories(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    ctx.save();
    const scale = this.maxRadius / this.maxRangeMeters;

    tracks.forEach(track => {
      const px = this.centerX + (track.x * scale);
      const py = this.centerY - (track.y * scale);

      // Parabolic predictive trajectory (next 3 seconds)
      if (track.vx !== undefined && track.vy !== undefined) {
        ctx.beginPath();
        ctx.setLineDash([3, 3]);
        ctx.moveTo(px, py);

        for (let t = 0.5; t <= 3.0; t += 0.5) {
          const futureX = px + (track.vx * scale * t);
          const futureY = py - (track.vy * scale * t);
          ctx.lineTo(futureX, futureY);
        }

        ctx.strokeStyle = (track.classification === 'HOSTILE') ? 'rgba(255, 30, 56, 0.65)' : 'rgba(0, 240, 255, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });
    ctx.restore();
  }

  drawAirTracks(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    const scale = this.maxRadius / this.maxRangeMeters;

    tracks.forEach(track => {
      const px = this.centerX + (track.x * scale);
      const py = this.centerY - (track.y * scale);

      const isPrimary = (track.trackId === primaryTrackId);
      const isHostile = track.classification === 'HOSTILE' || track.threatScore >= 75;
      const isSuspect = track.classification === 'SUSPECT' || (track.threatScore >= 40 && track.threatScore < 75);
      const isFriendly = track.classification === 'FRIENDLY';

      ctx.save();

      // Velocity Tail Vector
      if (track.vx !== undefined && track.vy !== undefined) {
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px + (track.vx * 1.8), py - (track.vy * 1.8));
        ctx.strokeStyle = isHostile ? '#ff1e38' : (isFriendly ? '#00ff66' : '#ffaa00');
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // MIL-STD-2525D Symbology
      if (isHostile) {
        // Red Diamond (HOSTILE BANDIT)
        ctx.strokeStyle = '#ff1e38';
        ctx.fillStyle = 'rgba(255, 30, 56, 0.4)';
        ctx.lineWidth = isPrimary ? 2.5 : 1.5;

        const s = isPrimary ? 10 : 8;
        ctx.beginPath();
        ctx.moveTo(px, py - s);
        ctx.lineTo(px + s, py);
        ctx.lineTo(px, py + s);
        ctx.lineTo(px - s, py);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Primary Target: Animated Targeting Ring
        if (isPrimary) {
          ctx.beginPath();
          ctx.arc(px, py, 16, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(255, 30, 56, 0.9)';
          ctx.setLineDash([3, 3]);
          ctx.stroke();
        }
      } else if (isSuspect) {
        // Amber Square (SUSPECT BOGIE)
        ctx.strokeStyle = '#ffaa00';
        ctx.fillStyle = 'rgba(255, 170, 0, 0.35)';
        ctx.lineWidth = 1.5;

        const s = 6;
        ctx.beginPath();
        ctx.rect(px - s, py - s, s * 2, s * 2);
        ctx.fill();
        ctx.stroke();
      } else {
        // Green Circle (FRIENDLY INTERCEPTOR)
        ctx.strokeStyle = '#00ff66';
        ctx.fillStyle = 'rgba(0, 255, 102, 0.4)';
        ctx.lineWidth = 1.8;

        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      // Track Data Block (Top Gun Callout Style)
      ctx.font = 'bold 9px "Share Tech Mono"';
      ctx.fillStyle = isHostile ? '#ff1e38' : (isFriendly ? '#00ff66' : '#ffaa00');
      ctx.fillText(`${track.trackId}`, px + 12, py - 6);

      ctx.font = '8px "Share Tech Mono"';
      ctx.fillStyle = '#7e94b0';
      const mach = (track.speed / 340.0).toFixed(2);
      ctx.fillText(`FL ${(track.altitude * 3.28).toFixed(0)} | M ${mach}`, px + 12, py + 4);
      ctx.fillText(`${Math.round(track.range)}m`, px + 12, py + 14);

      ctx.restore();
    });
  }
}

window.cinematicRadar = new CinematicRadarBigBoard('radarCanvas');
```

========================================================
FILE: frontend/js/optical_hud.js
========================================================

```javascript
/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Display Array 2: Multi-Mode EO/IR FLIR Target Reconnaissance Pod
 * Multi-Spectral Vision Modes (White-Hot, Black-Hot, NVG Green, Day Optical) + Digital Zoom
 */

class CinematicOpticalFLIR {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.visionMode = 'WHITE_HOT'; // 'WHITE_HOT', 'BLACK_HOT', 'NVG_GREEN', 'DAY_OPTICAL'
    this.zoomLevel = 4; // 1, 4, 8, 16
  }

  setVisionMode(mode) {
    this.visionMode = mode;
  }

  setZoomLevel(zoom) {
    this.zoomLevel = zoom;
  }

  updateAndDraw(tracks, primaryTrackId, gimbalPan, gimbalTilt) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Render Thermal/Optical Background based on Vision Mode
    this.drawVisionBackground(ctx, gimbalTilt);

    // 2. Tactical Pitch Ladder & Bank Horizon
    this.drawPitchLadder(ctx, gimbalTilt);

    // 3. Boresight Crosshair & Laser Rangefinder
    this.drawBoresight(ctx);

    // 4. Optical Target Bounding Brackets with Zoom Scaling
    this.drawTargetBrackets(ctx, tracks, primaryTrackId);

    // 5. Thermal Sensor Noise Grain
    this.drawSensorNoise(ctx);
  }

  drawVisionBackground(ctx, tilt) {
    const horizonY = (this.height / 2) + (tilt * 2.2);

    if (this.visionMode === 'WHITE_HOT') {
      // White-Hot FLIR: Dark cold sky, slightly lighter terrain
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#060a10');
      sky.addColorStop(1, '#121a24');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#10161f');
      ground.addColorStop(1, '#080c14');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else if (this.visionMode === 'BLACK_HOT') {
      // Black-Hot FLIR: Light hot background
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#75808d');
      sky.addColorStop(1, '#8c98a6');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#66727f');
      ground.addColorStop(1, '#505963');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else if (this.visionMode === 'NVG_GREEN') {
      // NVG Night-Vision Phosphor Green
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#031408');
      sky.addColorStop(1, '#062810');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#05220d');
      ground.addColorStop(1, '#021106');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else {
      // Day Optical: Natural daylight sky/ground
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#132840');
      sky.addColorStop(1, '#234568');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#182b20');
      ground.addColorStop(1, '#0f1a14');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);
    }

    // Horizon line
    ctx.beginPath();
    ctx.moveTo(0, horizonY);
    ctx.lineTo(this.width, horizonY);
    ctx.strokeStyle = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.4)' : 'rgba(0, 240, 255, 0.35)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  drawPitchLadder(ctx, tilt) {
    const cx = this.width / 2;
    const cy = this.height / 2;
    const horizonY = cy + (tilt * 2.2);

    ctx.save();
    const hudColor = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.7)' : (this.visionMode === 'BLACK_HOT' ? '#000000' : 'rgba(0, 240, 255, 0.7)');
    ctx.strokeStyle = hudColor;
    ctx.fillStyle = hudColor;
    ctx.lineWidth = 1;
    ctx.font = '9px "Share Tech Mono"';

    [-15, -10, -5, 5, 10, 15].forEach(deg => {
      const y = horizonY - (deg * 6.5);
      if (y > 35 && y < this.height - 35) {
        ctx.beginPath();
        ctx.moveTo(cx - 80, y); ctx.lineTo(cx - 35, y); ctx.lineTo(cx - 35, y + (deg > 0 ? 4 : -4));
        ctx.moveTo(cx + 35, y); ctx.lineTo(cx + 80, y); ctx.lineTo(cx + 35, y + (deg > 0 ? 4 : -4));
        ctx.stroke();

        ctx.fillText(`${deg > 0 ? '+' : ''}${deg}`, cx - 100, y + 3);
        ctx.fillText(`${deg > 0 ? '+' : ''}${deg}`, cx + 85, y + 3);
      }
    });
    ctx.restore();
  }

  drawBoresight(ctx) {
    const cx = this.width / 2;
    const cy = this.height / 2;

    ctx.save();
    const hudColor = (this.visionMode === 'NVG_GREEN') ? '#00ff66' : (this.visionMode === 'BLACK_HOT' ? '#000000' : '#00f0ff');
    ctx.strokeStyle = hudColor;
    ctx.lineWidth = 1.2;

    // Crosshair
    ctx.beginPath();
    ctx.moveTo(cx - 35, cy); ctx.lineTo(cx - 10, cy);
    ctx.moveTo(cx + 10, cy); ctx.lineTo(cx + 35, cy);
    ctx.moveTo(cx, cy - 35); ctx.lineTo(cx, cy - 10);
    ctx.moveTo(cx, cy + 10); ctx.lineTo(cx, cy + 35);
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 1.5, 0, Math.PI * 2);
    ctx.fillStyle = hudColor;
    ctx.fill();
    ctx.restore();
  }

  drawTargetBrackets(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    const fovRad = (60 * Math.PI) / 180;
    const zoomFactor = this.zoomLevel / 4.0; // Normalized to 4X default

    tracks.forEach(track => {
      const angleAz = Math.atan2(track.x, track.y);
      const angleEl = Math.atan2(track.z, Math.hypot(track.x, track.y));

      const screenX = (this.width / 2) + (Math.tan(angleAz) / Math.tan(fovRad / 2)) * (this.width / 2) * zoomFactor;
      const screenY = (this.height / 2) - (Math.tan(angleEl) / Math.tan(fovRad / 2)) * (this.height / 2) * zoomFactor;

      const dist = Math.max(track.range, 15);
      const baseBoxSize = Math.max(Math.min(2400 / dist, 120), 28);
      const boxSize = baseBoxSize * Math.sqrt(zoomFactor);

      const isPrimary = (track.trackId === primaryTrackId);
      const isHostile = track.classification === 'HOSTILE' || track.threatScore >= 75;

      ctx.save();

      // Render thermal heat silhouette if White-Hot or Black-Hot
      if (this.visionMode === 'WHITE_HOT') {
        ctx.fillStyle = isHostile ? 'rgba(255, 255, 255, 0.95)' : 'rgba(230, 240, 255, 0.7)';
        ctx.beginPath();
        ctx.arc(screenX, screenY, boxSize * 0.3, 0, Math.PI * 2);
        ctx.fill();
      } else if (this.visionMode === 'BLACK_HOT') {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
        ctx.beginPath();
        ctx.arc(screenX, screenY, boxSize * 0.3, 0, Math.PI * 2);
        ctx.fill();
      }

      // Targeting Corner Brackets
      const color = isHostile ? '#ff1e38' : (this.visionMode === 'NVG_GREEN' ? '#00ff66' : '#ffaa00');
      ctx.strokeStyle = color;
      ctx.lineWidth = isPrimary ? 2.2 : 1.2;

      const half = boxSize / 2;
      const arm = Math.max(boxSize * 0.28, 6);

      const left = screenX - half;
      const right = screenX + half;
      const top = screenY - half;
      const bottom = screenY + half;

      ctx.beginPath(); ctx.moveTo(left, top + arm); ctx.lineTo(left, top); ctx.lineTo(left + arm, top); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(right - arm, top); ctx.lineTo(right, top); ctx.lineTo(right, top + arm); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(left, bottom - arm); ctx.lineTo(left, bottom); ctx.lineTo(left + arm, bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(right - arm, bottom); ctx.lineTo(right, bottom); ctx.lineTo(right, bottom - arm); ctx.stroke();

      if (isPrimary) {
        // Rotating Lock Ring
        ctx.beginPath();
        ctx.arc(screenX, screenY, half + 14, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 30, 56, 0.85)';
        ctx.setLineDash([4, 4]);
        ctx.stroke();

        ctx.fillStyle = '#ff1e38';
        ctx.font = 'bold 9px "Share Tech Mono"';
        ctx.fillText(`FCR LOCK: ${track.trackId}`, left, top - 8);
        ctx.fillText(`TTI: ${(track.range / Math.max(track.speed, 5)).toFixed(1)}s`, left, bottom + 14);
      } else {
        ctx.fillStyle = color;
        ctx.font = '9px "Share Tech Mono"';
        ctx.fillText(`${track.trackId}`, left, top - 4);
      }

      ctx.restore();
    });
  }

  drawSensorNoise(ctx) {
    // Subtle realistic thermal camera grain noise
    ctx.save();
    ctx.fillStyle = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.04)' : 'rgba(255, 255, 255, 0.03)';
    for (let i = 0; i < 120; i++) {
      const rx = Math.random() * this.width;
      const ry = Math.random() * this.height;
      ctx.fillRect(rx, ry, 2, 2);
    }
    ctx.restore();
  }
}

window.cinematicOpticalFLIR = new CinematicOpticalFLIR('opticalCanvas');
```

========================================================
FILE: frontend/js/rf_spectrum.js
========================================================

```javascript
/**
 * INDIAN AIR FORCE - IACCS AIR DEFENCE SECTOR CONSOLE
 * ESM (Electronic Support Measures) & ECCM Spectrum Analyzer
 * Real-time Wideband RF Signal Strobe & Jamming Detection
 */

class MilitaryESMSpectrum {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.numChannels = 40;
    this.noiseFloor = -88; // dBm
    this.isJamming = false;
    this.activeChannel = 6; // Initial channel
  }

  updateAndDraw(isJammingActive, activeChannel) {
    this.isJamming = isJammingActive;
    this.activeChannel = activeChannel || this.activeChannel;

    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Grid & dBm Markers (-100dBm to -20dBm)
    this.drawDbmGrid(ctx);

    // 2. FFT Power Spectral Density Bars
    this.drawFftBars(ctx);

    // 3. Active C2 Frequency Marker & Strobe Alert
    this.drawChannelMarkers(ctx);
  }

  drawDbmGrid(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(26, 54, 93, 0.4)';
    ctx.lineWidth = 1;
    ctx.font = '8px "Share Tech Mono"';
    ctx.fillStyle = '#4a5d78';

    // Horizontal dBm grid lines: -80, -60, -40 dBm
    [-80, -60, -40].forEach(dbm => {
      const y = this.height - ((dbm + 100) / 80) * this.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.width, y);
      ctx.stroke();
      ctx.fillText(`${dbm} dBm`, 4, y - 2);
    });
    ctx.restore();
  }

  drawFftBars(ctx) {
    const ctx = this.ctx;
    const barWidth = this.width / this.numChannels;

    for (let i = 0; i < this.numChannels; i++) {
      // Calculate signal level
      let powerDbm = this.noiseFloor + (Math.random() * 6 - 3);

      // Signal peaks at Drone C2 bands (CH 6, CH 20, CH 36)
      if (i === this.activeChannel) {
        powerDbm += 38; // Normal C2 encrypted link
      } else if (i === 18) {
        powerDbm += 25; // 2.4GHz Telemetry beacon
      } else if (i === 32) {
        powerDbm += 22; // 5.8GHz FLIR downlink
      }

      // If hostile jamming is active: broadband barrage noise across multiple channels
      if (this.isJamming) {
        powerDbm += (Math.random() * 45 + 15);
      }

      // Convert dBm to screen height
      const barHeight = Math.max(Math.min(((powerDbm + 100) / 80) * this.height, this.height), 2);
      const x = i * barWidth;
      const y = this.height - barHeight;

      // Color coding: Red if jamming or high threat, Cyan/Green if nominal
      ctx.fillStyle = this.isJamming ? 'rgba(255, 42, 58, 0.85)' : (i === this.activeChannel ? 'rgba(0, 229, 255, 0.9)' : 'rgba(0, 255, 102, 0.35)');
      ctx.fillRect(x + 1, y, barWidth - 2, barHeight);

      // Peak hold indicator line
      ctx.fillStyle = this.isJamming ? '#ff2a3a' : '#00e5ff';
      ctx.fillRect(x + 1, y - 2, barWidth - 2, 2);
    }
  }

  drawChannelMarkers(ctx) {
    const barWidth = this.width / this.numChannels;
    const activeX = this.activeChannel * barWidth + (barWidth / 2);

    ctx.save();
    if (this.isJamming) {
      // Hostile Jamming Strobe Banner
      ctx.fillStyle = 'rgba(255, 42, 58, 0.2)';
      ctx.fillRect(0, 0, this.width, 22);
      ctx.fillStyle = '#ff2a3a';
      ctx.font = 'bold 9px "Share Tech Mono"';
      ctx.fillText('⚠️ HOSTILE ELECTRONIC ATTACK (BARRAGE NOISE DETECTED)', 10, 14);
    } else {
      // Active Frequency Hopped Channel Indicator
      ctx.strokeStyle = '#00e5ff';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.moveTo(activeX, 0);
      ctx.lineTo(activeX, this.height);
      ctx.stroke();

      ctx.fillStyle = '#00e5ff';
      ctx.font = 'bold 8px "Share Tech Mono"';
      ctx.fillText(`AFNET SECURE CH-${this.activeChannel}`, Math.max(activeX - 35, 6), 14);
    }
    ctx.restore();
  }
}

window.militaryESM = new MilitaryESMSpectrum('spectrumCanvas');
```

========================================================
FILE: frontend/js/gimbal_controls.js
========================================================

```javascript
/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Master Web Audio API Sound Effects Engine (Movie-Grade Radio Beeps, Klaxon, Lock Tones)
 */

class CinematicWarroomAudio {
  constructor() {
    this.ctx = null;
    this.klaxonOsc = null;
    this.isKlaxonPlaying = false;
  }

  initAudio() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  // Classic Top Gun / Military VHF Radio Mic-Click Squawk Beep
  playRadioCommsBeep() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(2450, this.ctx.currentTime);
      osc.frequency.setValueAtTime(1750, this.ctx.currentTime + 0.04);

      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.08);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.08);
    } catch (e) {}
  }

  // Master ADA Dual-Tone Warble Klaxon Siren
  startAdaKlaxon() {
    this.initAudio();
    if (this.isKlaxonPlaying) return;
    try {
      this.isKlaxonPlaying = true;
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc1.type = 'sawtooth';
      osc2.type = 'square';
      osc1.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc2.frequency.setValueAtTime(1200, this.ctx.currentTime);

      const lfo = this.ctx.createOscillator();
      const lfoGain = this.ctx.createGain();
      lfo.frequency.setValueAtTime(2.2, this.ctx.currentTime);
      lfoGain.gain.setValueAtTime(300, this.ctx.currentTime);

      lfo.connect(osc1.frequency);
      lfo.connect(osc2.frequency);

      gain.gain.setValueAtTime(0.07, this.ctx.currentTime);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.ctx.destination);

      lfo.start();
      osc1.start();
      osc2.start();

      this.klaxonOsc = [osc1, osc2, lfo];
    } catch (e) {}
  }

  stopAdaKlaxon() {
    if (this.klaxonOsc) {
      this.klaxonOsc.forEach(osc => {
        try { osc.stop(); } catch (e) {}
      });
      this.klaxonOsc = null;
    }
    this.isKlaxonPlaying = false;
  }

  // Jet Scramble / Afterburner Sound Burst
  playScrambleRoar() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(80, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(350, this.ctx.currentTime + 0.8);

      gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.9);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.9);
    } catch (e) {}
  }

  // Laser DEW Pulse Sound
  playHardKillLaser() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(160, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(30, this.ctx.currentTime + 0.5);

      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.5);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.5);
    } catch (e) {}
  }

  // Directed RF Jammer Chirp
  playSoftKillBeam() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(2400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.4);

      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.4);
    } catch (e) {}
  }
}

window.warroomAudio = new CinematicWarroomAudio();
```

========================================================
FILE: backend/requirements.txt
========================================================

```text
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
websockets>=11.0.3
numpy>=1.24.0
opencv-python>=4.8.0
ultralytics>=8.0.0
pyserial>=3.5
pyserial-asyncio>=0.6
asyncpg>=0.28.0
requests>=2.31.0
```

========================================================
FILE: backend/config.py
========================================================

```python
"""
SMART-SHIELD v3.0 Configuration Parameters
Contains hardware pin mappings, threat equation weights, radar specs, and server settings.
"""

import os
from pydantic import BaseModel

class ThreatWeights(BaseModel):
    w_distance: float = 0.30     # w1: Proximity weight
    w_speed: float = 0.25        # w2: Approach velocity weight
    w_direction: float = 0.20    # w3: Trajectory vector heading weight
    w_confidence: float = 0.15   # w4: Visual classification confidence weight
    w_behavior: float = 0.10     # w5: Erratic behavior / acceleration anomaly weight

    max_detection_range_m: float = 200.0
    max_expected_speed_ms: float = 30.0
    high_threat_threshold: float = 75.0
    medium_threat_threshold: float = 40.0

class RadarConfig(BaseModel):
    serial_port: str = "COM3"
    baud_rate: int = 256000
    frame_header: bytes = bytes([0xAA, 0xFF, 0x03, 0x00])
    frame_tail: bytes = bytes([0x55, 0xCC])
    max_targets: int = 3
    fov_azimuth_deg: float = 120.0
    update_rate_hz: int = 10

class GimbalConfig(BaseModel):
    pan_min_deg: float = 0.0
    pan_max_deg: float = 180.0
    tilt_min_deg: float = 15.0
    tilt_max_deg: float = 90.0
    pan_center_deg: float = 90.0
    tilt_center_deg: float = 45.0
    
    # PID gains for visual servoing
    kp_pan: float = 0.08
    ki_pan: float = 0.002
    kd_pan: float = 0.015
    
    kp_tilt: float = 0.08
    ki_tilt: float = 0.002
    kd_tilt: float = 0.015

class CyberRFConfig(BaseModel):
    baseline_noise_floor_dbm: float = -88.5
    jamming_delta_threshold_db: float = 18.0
    monitored_channels: list = [1, 6, 11, 36, 149]
    default_c2_channel: int = 6
    backup_channels: list = [1, 11, 40, 153]

class SystemConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    db_dsn: str = os.getenv("DATABASE_URL", "")
    simulation_mode: bool = True
    ai_inference_fps: int = 30
    threat: ThreatWeights = ThreatWeights()
    radar: RadarConfig = RadarConfig()
    gimbal: GimbalConfig = GimbalConfig()
    cyber_rf: CyberRFConfig = CyberRFConfig()

config = SystemConfig()
```

========================================================
FILE: backend/main.py
========================================================

```python
"""
SMART-SHIELD v3.0 Main FastAPI & WebSocket Hub
Coordinates Vision, Radar, Sensor Fusion, Cyber-Defence, Actuation, and Telemetry Broadcast.
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .config import config
from .hardware.esp32_serial import ESP32SerialController
from .vision.detector import DroneObjectDetector, CameraStreamManager
from .vision.tracker import ByteTracker
from .vision.velocity_estimator import OpticalVelocityEstimator
from .fusion.threat_matrix import ThreatEvaluationEngine
from .fusion.sensor_fusion import SensorFusionEngine
from .fusion.trajectory_predictor import TrajectoryPredictor
from .gimbal.pid import PIDGimbalController
from .cyber_defense.rf_monitor import CyberRFMonitor
from .simulator import ScenarioSimulator
try:
    from database.db_manager import DatabaseManager
except (ImportError, ValueError):
    from ..database.db_manager import DatabaseManager
import os

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SmartShield.Main")

app = FastAPI(title="SMART-SHIELD v3.0 C2 Backend", version="3.0.0")

# CORS middleware for open dashboard connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Subsystems
db = DatabaseManager(config.db_dsn)
serial_ctrl = ESP32SerialController(config.radar.serial_port, config.radar.baud_rate)
detector = DroneObjectDetector()
cam_manager = CameraStreamManager(detector=detector)
tracker = ByteTracker()
velocity_estimator = OpticalVelocityEstimator()
fusion_engine = SensorFusionEngine()
trajectory_predictor = TrajectoryPredictor()
threat_engine = ThreatEvaluationEngine()
gimbal_ctrl = PIDGimbalController()
rf_monitor = CyberRFMonitor()
simulator = ScenarioSimulator()

# Cached state for video streamer
latest_targets: List[Dict[str, Any]] = []
latest_detections: List[Dict[str, Any]] = []
latest_primary_id: Optional[str] = None

# Active WebSocket client connections
connected_clients: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    await db.initialize()
    serial_ctrl.connect()
    asyncio.create_task(fusion_orchestration_loop())
    logger.info("SMART-SHIELD v3.0 Backend Services initialized and running.")

@app.on_event("shutdown")
async def shutdown_event():
    await db.close()

# ----------------- WEBSOCKET BROADCASTING -----------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Keep-alive receive
            data = await websocket.receive_text()
            msg = json.loads(data)
            # Handle incoming commands from UI
            if msg.get("cmd") == "TOGGLE_AUTOTRACK":
                gimbal_ctrl.auto_track_enabled = msg.get("enabled", True)
            elif msg.get("cmd") == "MANUAL_GIMBAL":
                gimbal_ctrl.set_manual_angles(msg.get("pan", 90.0), msg.get("tilt", 45.0))
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_telemetry(payload: Dict[str, Any]):
    """Dispatches full system state to all connected dashboard WebSockets."""
    if not connected_clients:
        return
    msg = json.dumps(payload)
    for ws in list(connected_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            if ws in connected_clients:
                connected_clients.remove(ws)

# ----------------- MAIN FUSION & THREAT EVALUATION LOOP -----------------

async def fusion_orchestration_loop():
    """Runs at ~30Hz: Updates simulations/sensors, evaluates threats, controls gimbal, broadcasts telemetry."""
    while True:
        try:
            start_time = time.time()

            # 1. Acquire Target Kinematics (Hardware Radar or Simulator)
            if config.simulation_mode:
                raw_targets = simulator.update_simulation()
            else:
                raw_targets = serial_ctrl.read_radar_data()

            # 2. Vision Target Detection & 2D Projection
            synthetic_dets = detector.generate_synthetic_detections(raw_targets)
            tracked_boxes = tracker.update(synthetic_dets)

            # 3. Sensor Fusion & Threat Scoring
            evaluated_targets = []
            for t in raw_targets:
                scoring = threat_engine.calculate_threat_score(
                    distance_m=t.get("distance_m", 50.0),
                    speed_ms=t.get("speed_ms", 15.0),
                    azimuth_deg=t.get("azimuth_deg", 0.0),
                    heading_deg=t.get("heading_deg", 0.0),
                    optical_confidence=t.get("optical_confidence", 0.90),
                    classification=t.get("classification", "Drone"),
                    behavior_factor=t.get("behavior_factor", 0.4)
                )
                t_fused = {**t, **scoring}
                evaluated_targets.append(t_fused)
                
                # Persist telemetry async
                await db.save_telemetry({
                    "target_id": t["id"],
                    "x_pos_m": t["x_m"],
                    "y_pos_m": t["y_m"],
                    "z_pos_m": t["z_m"],
                    "distance_m": t["distance_m"],
                    "azimuth_deg": t["azimuth_deg"],
                    "speed_ms": t["speed_ms"],
                    "optical_confidence": t["optical_confidence"],
                    "radar_snr": t["radar_snr"],
                    "threat_score": scoring["threat_score"],
                    "threat_level": scoring["threat_level"]
                })

            # 4. Elect Primary Threat Target
            prioritized_targets = threat_engine.prioritize_targets(evaluated_targets)
            primary_target = prioritized_targets[0] if prioritized_targets else None

            # 5. Pan/Tilt PID Gimbal Tracking
            pan_deg, tilt_deg = gimbal_ctrl.pan_angle, gimbal_ctrl.tilt_angle
            if primary_target and gimbal_ctrl.auto_track_enabled:
                # Find matching visual bounding box for primary target
                matching_det = next((d for d in synthetic_dets if d.get("id") == primary_target["id"]), None)
                if matching_det:
                    pan_deg, tilt_deg = gimbal_ctrl.compute_tracking_angles(
                        target_center_u=matching_det["center_u"],
                        target_center_v=matching_det["center_v"]
                    )
                else:
                    # Coarse slewing to target azimuth
                    target_pan = 90.0 + primary_target["azimuth_deg"]
                    pan_deg, tilt_deg = gimbal_ctrl.compute_tracking_angles(
                        target_center_u=(640/2) + (primary_target["x_m"]/primary_target["y_m"])*300,
                        target_center_v=(460/2) - (primary_target["z_m"]/primary_target["y_m"])*300
                    )

            # Transmit hardware command to ESP32
            has_high_threat = any(t.get("threat_level") == "HIGH" for t in prioritized_targets)
            serial_ctrl.send_gimbal_command(
                pan_deg=pan_deg,
                tilt_deg=tilt_deg,
                threat_level="HIGH" if has_high_threat else "LOW",
                buzzer=has_high_threat
            )

            # 6. Cyber RF Spectrum & Electronic Warfare State
            rf_status = rf_monitor.get_spectrum_scan()

            # 7. Assemble Full C2 Telemetry Payload
            global latest_targets, latest_detections, latest_primary_id
            latest_targets = prioritized_targets
            latest_detections = synthetic_dets
            latest_primary_id = primary_target["id"] if primary_target else None

            telemetry_payload = {
                "timestamp": time.time(),
                "targets": prioritized_targets,
                "primary_target": primary_target,
                "detections_2d": synthetic_dets,
                "gimbal": {
                    "pan_deg": pan_deg,
                    "tilt_deg": tilt_deg,
                    "auto_track": gimbal_ctrl.auto_track_enabled
                },
                "cyber_rf": rf_status,
                "system": {
                    "battery_voltage": 12.6,
                    "status": "ARMED",
                    "high_threat_active": has_high_threat,
                    "buzzer_active": has_high_threat
                }
            }

            # Broadcast to UI
            await broadcast_telemetry(telemetry_payload)

            # Target 30Hz loop execution
            elapsed = time.time() - start_time
            sleep_time = max(0.005, (1.0 / config.ai_inference_fps) - elapsed)
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Error in fusion loop: {e}")
            await asyncio.sleep(0.1)

# ----------------- VIDEO STREAMING & REST APIS -----------------

async def generate_mjpeg_stream():
    """Async generator yielding multipart JPEG frames for browser HUD."""
    while True:
        frame_bytes = cam_manager.get_annotated_frame_bytes(
            targets=latest_targets,
            detections=latest_detections,
            primary_id=latest_primary_id
        )
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        await asyncio.sleep(0.04) # ~25 FPS

@app.get("/api/video_feed")
async def get_video_feed():
    """MJPEG live camera / synthetic reconnaissance stream endpoint."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/status")
async def get_system_status():
    return {
        "status": "ONLINE",
        "version": "3.0.0",
        "time": time.time(),
        "active_targets": len(simulator.targets),
        "db_mode": "PostgreSQL" if db.is_connected else ("SQLite (Persistent)" if db.use_sqlite else "In-Memory")
    }

@app.post("/api/simulation/add_intruder")
async def api_add_intruder():
    new_drone = simulator.add_intruder()
    return {"status": "SUCCESS", "intruder": new_drone}

@app.post("/api/cyber/toggle_jamming")
async def api_toggle_jamming():
    state = rf_monitor.toggle_jamming_simulation()
    return {"status": "SUCCESS", "jamming_active": state}

@app.post("/api/cyber/frequency_hop")
async def api_frequency_hop():
    hop_event = rf_monitor.execute_frequency_hop()
    await db.save_cyber_event(hop_event)
    return {"status": "SUCCESS", "hop_event": hop_event}

@app.get("/api/telemetry/replay")
async def get_telemetry_replay(limit: int = 150):
    """Retrieves recent recorded trajectory points for tactical mission replay."""
    history = db.get_historical_telemetry(limit=limit)
    return {"status": "SUCCESS", "count": len(history), "telemetry": history}

@app.get("/api/logs/export/csv")
async def export_telemetry_csv():
    """Exports recorded target flight data as a downloadable CSV audit report."""
    csv_data = db.export_csv_report()
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smart_shield_mission_report.csv"}
    )

@app.get("/api/logs/cyber")
async def get_cyber_logs():
    return db.ring_buffer.get_recent_cyber_events()

# Mount C2 Operator Dashboard Frontend Static Files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
```

========================================================
FILE: backend/simulator.py
========================================================

```python
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
```

========================================================
FILE: backend/__init__.py
========================================================

```python
"""
SMART-SHIELD v3.0 Backend Core Module Exports
"""

from .vision.velocity_estimator import OpticalVelocityEstimator
from .vision.detector import DroneObjectDetector, CameraStreamManager
from .vision.tracker import ByteTracker
from .vision.calibration import HomographyCalibrator, PinholeCalibrator
from .hardware.radar_interface import LD2450RadarParser, ESP32SerialController
from .fusion.state_estimator import TargetEKFFilter, StateEstimator
from .fusion.sensor_fusion import SensorFusionEngine, fuse_velocities_weighted
from .fusion.threat_matrix import ThreatEvaluationEngine
from .fusion.trajectory_predictor import TrajectoryPredictor
from .gimbal.servo_control import PIDGimbalController, ServoController
from .cyber_defense.rf_monitor import CyberRFMonitor

__all__ = [
    "OpticalVelocityEstimator",
    "DroneObjectDetector",
    "CameraStreamManager",
    "ByteTracker",
    "HomographyCalibrator",
    "PinholeCalibrator",
    "LD2450RadarParser",
    "ESP32SerialController",
    "TargetEKFFilter",
    "StateEstimator",
    "SensorFusionEngine",
    "fuse_velocities_weighted",
    "ThreatEvaluationEngine",
    "TrajectoryPredictor",
    "PIDGimbalController",
    "ServoController",
    "CyberRFMonitor"
]
```

========================================================
FILE: backend/vision/__init__.py
========================================================

```python
# Vision package
```

========================================================
FILE: backend/vision/detector.py
========================================================

```python
"""
SMART-SHIELD v3.0 YOLO Vision Detection Engine
Performs aerial target recognition (Drone, Quadcopter, Fixed-Wing, Bird).
Includes synthetic generation mode for standalone testing without camera hardware.
"""

import time
import math
import random
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("SmartShield.Vision")

class DroneObjectDetector:
    """YOLOv8 Aerial Target Detector wrapper with support for live inference & simulation."""
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.45):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.classes = ["Drone", "Quadcopter", "Fixed-Wing", "Bird"]
        self._init_model()

    def _init_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded YOLO model: {self.model_path}")
        except Exception as e:
            logger.warning(f"YOLO weights or PyTorch not available ({e}). Vision engine operating in Synthetic Inference Mode.")
            self.model = None

    def detect_frame(self, frame_image: Any) -> List[Dict[str, Any]]:
        """Runs YOLO inference on camera frame and returns standard bounding box dicts."""
        if self.model and frame_image is not None:
            results = self.model(frame_image, conf=self.confidence_threshold, verbose=False)
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cls_name = self.model.names.get(cls_id, "Drone")

                    detections.append({
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "center_u": round((x1 + x2) / 2.0, 1),
                        "center_v": round((y1 + y2) / 2.0, 1),
                        "width": round(x2 - x1, 1),
                        "height": round(y2 - y1, 1),
                        "confidence": round(conf, 2),
                        "class_name": cls_name
                    })
            return detections
        return []

    def generate_synthetic_detections(self, sim_targets: List[Dict[str, Any]], frame_w: int = 640, frame_h: int = 460) -> List[Dict[str, Any]]:
        """Maps 3D simulated spatial targets into 2D camera viewport bounding boxes."""
        detections = []
        for t in sim_targets:
            # Perspective projection of target X, Y, Z
            x_m = t.get("x_m", 0.0)
            y_m = max(1.0, t.get("y_m", 10.0))  # Forward range
            z_m = t.get("z_m", 15.0)            # Altitude

            # Pinhole camera focal scale
            f_scale = 400.0
            u = (frame_w / 2.0) + (x_m / y_m) * f_scale
            v = (frame_h / 2.0) - (z_m / y_m) * f_scale

            # Bounding box size scales inversely with distance
            box_w = max(20.0, min(140.0, (1.0 / y_m) * 1800.0))
            box_h = box_w * 0.65

            # Only include if in camera FOV
            if 0 <= u <= frame_w and 0 <= v <= frame_h:
                detections.append({
                    "id": t.get("id"),
                    "bbox": [
                        round(u - box_w / 2, 1),
                        round(v - box_h / 2, 1),
                        round(u + box_w / 2, 1),
                        round(v + box_h / 2, 1)
                    ],
                    "center_u": round(u, 1),
                    "center_v": round(v, 1),
                    "width": round(box_w, 1),
                    "height": round(box_h, 1),
                    "confidence": t.get("optical_confidence", 0.92),
                    "class_name": t.get("classification", "Drone")
                })
        return detections


class CameraStreamManager:
    """Manages physical/synthetic camera streams and generates MJPEG frames for UI."""
    def __init__(self, camera_index: Optional[int] = None, detector: Optional[DroneObjectDetector] = None):
        self.camera_index = camera_index
        self.detector = detector or DroneObjectDetector()
        self.cap = None
        self.is_live = False
        if self.camera_index is not None:
            self._init_camera()

    def _init_camera(self):
        try:
            import cv2
            # Open camera only if index is explicitly provided
            self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                self.is_live = True
                logger.info(f"Live hardware camera initialized on index {self.camera_index}")
            else:
                self.is_live = False
                logger.info("No physical webcam detected. Operating in high-performance Synthetic Video Mode.")
        except Exception as e:
            self.is_live = False
            logger.warning(f"OpenCV video capture unavailable ({e}). Using synthetic video stream.")

    def get_annotated_frame_bytes(self, targets: List[Dict[str, Any]], detections: List[Dict[str, Any]], primary_id: Optional[str] = None) -> bytes:
        """Generates a JPEG-compressed frame buffer with tactical HUD overlays."""
        try:
            import cv2
            import numpy as np

            width, height = 640, 460

            if self.is_live and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.resize(frame, (width, height))
                else:
                    frame = self._render_synthetic_frame(width, height, detections, primary_id)
            else:
                frame = self._render_synthetic_frame(width, height, detections, primary_id)

            # Draw tactical HUD overlays on frame
            for det in detections:
                x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
                t_id = det.get("id", "DRONE")
                is_pri = (t_id == primary_id)
                color = (0, 0, 255) if is_pri else (0, 215, 255) # BGR
                thickness = 2 if is_pri else 1

                # Bounding box corners
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                label = f"{t_id} {det.get('class_name', 'Drone')} ({int(det.get('confidence', 0.9)*100)}%)"
                cv2.putText(frame, label, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

            # Crosshairs
            cx, cy = width // 2, height // 2
            cv2.line(frame, (cx - 20, cy), (cx - 5, cy), (255, 240, 0), 1)
            cv2.line(frame, (cx + 5, cy), (cx + 20, cy), (255, 240, 0), 1)
            cv2.line(frame, (cx, cy - 20), (cx, cy - 5), (255, 240, 0), 1)
            cv2.line(frame, (cx, cy + 5), (cx, cy + 20), (255, 240, 0), 1)

            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                return jpeg.tobytes()
        except Exception:
            pass

        # Fallback minimal JPEG header
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'

    def _render_synthetic_frame(self, width: int, height: int, detections: List[Dict[str, Any]], primary_id: Optional[str]):
        """Renders tactical FLIR thermal background with artificial aerial silhouettes."""
        import numpy as np
        import cv2

        # Create gradient thermal background
        img = np.zeros((height, width, 3), dtype=np.uint8)
        horizon = height // 2
        
        # Sky: dark gradient
        for y in range(horizon):
            val = int(12 + (y / horizon) * 20)
            img[y, :] = (val + 10, val + 5, val)

        # Ground: darker terrain
        for y in range(horizon, height):
            val = int(22 - ((y - horizon) / (height - horizon)) * 12)
            img[y, :] = (val, val + 5, val + 8)

        # Draw horizon line
        cv2.line(img, (0, horizon), (width, horizon), (50, 60, 70), 1)

        # Draw drone silhouettes
        for det in detections:
            u, v = int(det["center_u"]), int(det["center_v"])
            w, h = int(det["width"]), int(det["height"])
            if 0 <= u < width and 0 <= v < height:
                # Quadcopter body and rotors
                cv2.circle(img, (u, v), max(3, w // 6), (220, 230, 240), -1)
                cv2.line(img, (u - w//2, v - h//3), (u + w//2, v + h//3), (180, 190, 200), 2)
                cv2.line(img, (u - w//2, v + h//3), (u + w//2, v - h//3), (180, 190, 200), 2)

        return img

```

========================================================
FILE: backend/vision/tracker.py
========================================================

```python
"""
SMART-SHIELD v3.0 Multi-Object Tracker (ByteTrack Implementation)
Maintains persistent track IDs across frames and handles association through occlusions.
"""

import math
import time
from typing import List, Dict, Any, Optional

class Track:
    """Represents a single persistent target track with Kalman state filtering."""
    def __init__(self, track_id: int, bbox: List[float], class_name: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.class_name = class_name
        self.confidence = confidence
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.history = [bbox]
        self.state = "TRACKING"  # "TRACKING", "LOST"

    def update(self, bbox: List[float], confidence: float, class_name: Optional[str] = None):
        self.bbox = bbox
        self.confidence = confidence
        if class_name:
            self.class_name = class_name
        self.hits += 1
        self.time_since_update = 0
        self.history.append(bbox)
        if len(self.history) > 30:
            self.history.pop(0)

    def mark_missed(self):
        self.time_since_update += 1
        self.age += 1
        if self.time_since_update > 10:
            self.state = "LOST"


class ByteTracker:
    """ByteTrack multi-target association algorithm."""
    def __init__(self, max_lost_frames: int = 15, iou_threshold: float = 0.3):
        self.max_lost_frames = max_lost_frames
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1

    @staticmethod
    def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        denom = float(boxAArea + boxBArea - interArea)
        return interArea / denom if denom > 0 else 0.0

    def update(self, detections: List[Dict[str, Any]]) -> List[Track]:
        matched_tracks = set()
        matched_dets = set()

        # Step 1: Match high-confidence detections with existing tracks
        for d_idx, det in enumerate(detections):
            best_iou = self.iou_threshold
            best_t_idx = -1
            for t_idx, track in enumerate(self.tracks):
                if t_idx in matched_tracks:
                    continue
                iou = self.calculate_iou(det["bbox"], track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_t_idx = t_idx

            if best_t_idx >= 0:
                self.tracks[best_t_idx].update(det["bbox"], det["confidence"], det["class_name"])
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)

        # Step 2: Unmatched detections initiate new tracks
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                # Use predefined simulation ID if present, otherwise increment ID
                t_id = det.get("id", self.next_id)
                if isinstance(t_id, int):
                    self.next_id = max(self.next_id, t_id + 1)
                else:
                    self.next_id += 1
                new_track = Track(
                    track_id=t_id,
                    bbox=det["bbox"],
                    class_name=det["class_name"],
                    confidence=det["confidence"]
                )
                self.tracks.append(new_track)

        # Step 3: Unmatched tracks are marked missed
        for t_idx, track in enumerate(self.tracks):
            if t_idx not in matched_tracks:
                track.mark_missed()

        # Clean up permanently lost tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_lost_frames]
        return [t for t in self.tracks if t.time_since_update == 0]
```

========================================================
FILE: backend/vision/velocity_estimator.py
========================================================

```python
"""
SMART-SHIELD v3.0 Optical Velocity Estimator
Computes 2D pixel velocity, optical expansion rates, and metric Cartesian velocity from track history.
"""

import time
import math
from typing import List, Dict, Any, Tuple, Optional

class OpticalVelocityEstimator:
    """Estimates velocity vectors (pixel and metric) from consecutive bounding box track history."""
    def __init__(self, ema_alpha: float = 0.6, focal_length_px: float = 400.0):
        self.ema_alpha = ema_alpha
        self.focal_length_px = focal_length_px
        self.velocity_cache: Dict[str, Dict[str, float]] = {}

    def estimate_velocity_from_history(
        self,
        track_id: str,
        history_bboxes: List[List[float]],
        timestamps: Optional[List[float]] = None,
        estimated_depth_m: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Computes smoothed velocity (du/dt, dv/dt) and metric (vx, vy, vz) from track history.
        history_bboxes: List of [x1, y1, x2, y2] in chronological order (latest is last).
        """
        if not history_bboxes or len(history_bboxes) < 2:
            return {
                "vel_u_px_s": 0.0,
                "vel_v_px_s": 0.0,
                "scale_expansion_rate": 0.0,
                "vx_est_ms": 0.0,
                "vy_est_ms": 0.0,
                "vz_est_ms": 0.0,
                "speed_est_ms": 0.0
            }

        # Use latest two frames
        curr_box = history_bboxes[-1]
        prev_box = history_bboxes[-2]

        curr_cx = (curr_box[0] + curr_box[2]) / 2.0
        curr_cy = (curr_box[1] + curr_box[3]) / 2.0
        curr_size = math.sqrt((curr_box[2] - curr_box[0]) * (curr_box[3] - curr_box[1]))

        prev_cx = (prev_box[0] + prev_box[2]) / 2.0
        prev_cy = (prev_box[1] + prev_box[3]) / 2.0
        prev_size = math.sqrt((prev_box[2] - prev_box[0]) * (prev_box[3] - prev_box[1]))

        # Time delta
        dt = 0.033  # Default ~30Hz
        if timestamps and len(timestamps) >= 2:
            dt = max(0.005, min(0.5, timestamps[-1] - timestamps[-2]))

        # Instantaneous 2D pixel velocities
        raw_du = (curr_cx - prev_cx) / dt
        raw_dv = (curr_cy - prev_cy) / dt
        scale_rate = (curr_size - prev_size) / (max(prev_size, 1.0) * dt)

        # Exponential Moving Average (EMA) smoothing
        cached = self.velocity_cache.get(track_id, {"du": raw_du, "dv": raw_dv})
        smooth_du = self.ema_alpha * raw_du + (1.0 - self.ema_alpha) * cached["du"]
        smooth_dv = self.ema_alpha * raw_dv + (1.0 - self.ema_alpha) * cached["dv"]
        self.velocity_cache[track_id] = {"du": smooth_du, "dv": smooth_dv}

        # Metric velocity projection if distance / depth is provided
        # X = (u - cx) * Z / f  ==>  v_X = (du/dt * Z / f)
        # Y = Z (depth)         ==>  v_Y = - (Z * scale_rate) (approaching if expanding)
        # Z = (cy - v) * Z / f  ==>  v_Z = - (dv/dt * Z / f)
        depth = estimated_depth_m if estimated_depth_m and estimated_depth_m > 0 else 50.0
        vx_metric = (smooth_du * depth) / self.focal_length_px
        vz_metric = -(smooth_dv * depth) / self.focal_length_px
        vy_metric = -scale_rate * depth * 2.0  # Inbound radial rate from optical expansion

        speed_3d = math.sqrt(vx_metric**2 + vy_metric**2 + vz_metric**2)

        return {
            "vel_u_px_s": round(smooth_du, 1),
            "vel_v_px_s": round(smooth_dv, 1),
            "scale_expansion_rate": round(scale_rate, 3),
            "vx_est_ms": round(vx_metric, 2),
            "vy_est_ms": round(vy_metric, 2),
            "vz_est_ms": round(vz_metric, 2),
            "speed_est_ms": round(speed_3d, 2)
        }
```

========================================================
FILE: backend/vision/calibration.py
========================================================

```python
"""
SMART-SHIELD v3.0 Camera-to-World Calibration Module
Implements Homography / Planar perspective mapping and Pinhole Intrinsic/Extrinsic 3D coordinate conversion.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Any

class HomographyCalibrator:
    """Computes and applies a 3x3 Homography perspective matrix from 4-point image-to-world correspondences."""
    def __init__(self, image_points: Optional[List[Tuple[float, float]]] = None, world_points: Optional[List[Tuple[float, float]]] = None):
        self.H = np.eye(3, dtype=float)
        self.H_inv = np.eye(3, dtype=float)
        self.is_calibrated = False

        if image_points and world_points and len(image_points) >= 4 and len(world_points) >= 4:
            self.compute_homography(image_points, world_points)

    def compute_homography(self, image_points: List[Tuple[float, float]], world_points: List[Tuple[float, float]]) -> bool:
        """
        Calculates homography matrix H mapping image points (u, v) to world points (X, Y).
        Uses OpenCV cv2.findHomography if available, or Direct Linear Transformation (DLT) fallback.
        """
        try:
            import cv2
            src_pts = np.array(image_points, dtype=np.float32).reshape(-1, 1, 2)
            dst_pts = np.array(world_points, dtype=np.float32).reshape(-1, 1, 2)
            H_mat, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H_mat is not None:
                self.H = H_mat
                self.H_inv = np.linalg.inv(self.H)
                self.is_calibrated = True
                return True
        except Exception:
            pass

        # Manual DLT (Direct Linear Transformation) Fallback
        if len(image_points) >= 4 and len(world_points) >= 4:
            A = []
            for (u, v), (X, Y) in zip(image_points[:4], world_points[:4]):
                A.append([-u, -v, -1, 0, 0, 0, u * X, v * X, X])
                A.append([0, 0, 0, -u, -v, -1, u * Y, v * Y, Y])
            A = np.array(A, dtype=float)
            _, _, Vh = np.linalg.svd(A)
            L = Vh[-1, :] / Vh[-1, -1]
            self.H = L.reshape(3, 3)
            self.H_inv = np.linalg.inv(self.H)
            self.is_calibrated = True
            return True

        return False

    def pixel_to_world(self, u: float, v: float) -> Tuple[float, float]:
        """Transforms 2D pixel coordinates (u, v) to real-world ground coordinates (X, Y)."""
        vec = np.array([u, v, 1.0], dtype=float)
        world_homo = self.H @ vec
        if abs(world_homo[2]) > 1e-6:
            X = world_homo[0] / world_homo[2]
            Y = world_homo[1] / world_homo[2]
            return round(float(X), 2), round(float(Y), 2)
        return 0.0, 0.0

    def world_to_pixel(self, X: float, Y: float) -> Tuple[float, float]:
        """Transforms real-world ground coordinates (X, Y) back to 2D image pixels (u, v)."""
        vec = np.array([X, Y, 1.0], dtype=float)
        img_homo = self.H_inv @ vec
        if abs(img_homo[2]) > 1e-6:
            u = img_homo[0] / img_homo[2]
            v = img_homo[1] / img_homo[2]
            return round(float(u), 1), round(float(v), 1)
        return 0.0, 0.0


class PinholeCalibrator:
    """Pinhole camera intrinsic calibration model with radar-assisted depth projection."""
    def __init__(self, focal_length_px: float = 400.0, principal_point: Tuple[float, float] = (320.0, 230.0)):
        self.fx = focal_length_px
        self.fy = focal_length_px
        self.cx, self.cy = principal_point

        # Intrinsic Camera Matrix K
        self.K = np.array([
            [self.fx, 0.0, self.cx],
            [0.0, self.fy, self.cy],
            [0.0, 0.0, 1.0]
        ], dtype=float)
        self.K_inv = np.linalg.inv(self.K)

    def pixel_to_3d_point(self, u: float, v: float, depth_m: float) -> Tuple[float, float, float]:
        """
        Converts 2D pixel coordinate (u, v) and radar-measured range / depth (m) to 3D Cartesian coordinates (X, Y, Z).
        X = (u - cx) * depth / fx
        Y = depth (forward range)
        Z = (cy - v) * depth / fy (altitude)
        """
        X = (u - self.cx) * depth_m / self.fx
        Y = depth_m
        Z = (self.cy - v) * depth_m / self.fy
        return round(float(X), 2), round(float(Y), 2), round(float(Z), 2)

    def point_3d_to_pixel(self, X: float, Y: float, Z: float) -> Tuple[float, float]:
        """Projects 3D Cartesian point (X, Y, Z) onto camera 2D image plane (u, v)."""
        depth = max(0.1, Y)
        u = (X * self.fx / depth) + self.cx
        v = self.cy - (Z * self.fy / depth)
        return round(float(u), 1), round(float(v), 1)
```

========================================================
FILE: backend/fusion/__init__.py
========================================================

```python
# Subpackages init
```

========================================================
FILE: backend/fusion/sensor_fusion.py
========================================================

```python
"""
SMART-SHIELD v3.0 Sensor Fusion Engine
Coordinates multi-sensor fusion across mmWave Radar and Optical Camera.
"""

from typing import Dict, List, Any, Optional
from .ekf import TargetEKFFilter
from .threat_matrix import ThreatEvaluationEngine
from .trajectory_predictor import TrajectoryPredictor

class SensorFusionEngine:
    """Orchestrates multi-sensor data fusion combining Radar, Camera, and EKF filtering."""
    def __init__(self):
        self.ekf_filters: Dict[str, TargetEKFFilter] = {}
        self.threat_engine = ThreatEvaluationEngine()
        self.trajectory_predictor = TrajectoryPredictor()

    def get_or_create_filter(self, target_id: str, init_x: float, init_y: float, init_z: float = 15.0, init_vx: float = 0.0, init_vy: float = -10.0, init_vz: float = 0.0) -> TargetEKFFilter:
        if target_id not in self.ekf_filters:
            self.ekf_filters[target_id] = TargetEKFFilter(init_x, init_y, init_z, init_vx, init_vy, init_vz)
        return self.ekf_filters[target_id]

    def fuse_target(self, target_data: Dict[str, Any], dt: float = 0.033) -> Dict[str, Any]:
        """Runs EKF prediction, updates with radar measurements, and returns fused state."""
        tid = target_data.get("id", "DRONE-01")
        ekf = self.get_or_create_filter(
            target_id=tid,
            init_x=target_data.get("x_m", 0.0),
            init_y=target_data.get("y_m", 50.0),
            init_z=target_data.get("z_m", 15.0),
            init_vx=target_data.get("vx_ms", 0.0),
            init_vy=target_data.get("vy_ms", -10.0),
            init_vz=target_data.get("vz_ms", 0.0)
        )

        # 1. State prediction
        ekf.predict(dt=dt)

        # 2. Update with radar if available
        r = target_data.get("distance_m", 50.0)
        theta_rad = target_data.get("azimuth_deg", 0.0) * (3.14159 / 180.0)
        vr = target_data.get("speed_ms", -15.0)
        ekf.update_radar(r_meas=r, theta_rad_meas=theta_rad, vr_meas=vr)

        # 3. Retrieve fused kinematics
        fused = ekf.get_fused_state()

        # 4. Trajectory forward projection & CPA
        cpa = self.trajectory_predictor.calculate_closest_point_of_approach(
            fused["x_m"], fused["y_m"], fused["z_m"],
            fused["vx_ms"], fused["vy_ms"], fused["vz_ms"]
        )

        return {
            **target_data,
            **fused,
            "cpa": cpa
        }

def fuse_velocities_weighted(
    v_camera: Optional[float],
    v_radar: Optional[float],
    w_camera: float = 0.4,
    w_radar: float = 0.6,
    disagreement_threshold: float = 15.0
) -> float:
    """
    Combines radar and camera velocity estimates using a confidence-weighted average:
    V_final = (w_r * V_radar + w_c * V_camera) / (w_r + w_c)
    Includes disagreement detection and handles single-sensor dropouts.
    """
    if v_camera is None and v_radar is None:
        return 0.0
    if v_camera is None:
        return float(v_radar)
    if v_radar is None:
        return float(v_camera)

    # Disagreement / outlier detection
    diff = abs(v_camera - v_radar)
    if diff > disagreement_threshold:
        # Heavily favor radar Doppler velocity as ground-truth when large disparity occurs
        w_radar = 0.9
        w_camera = 0.1

    v_final = (w_radar * v_radar + w_camera * v_camera) / (w_radar + w_camera)
    return round(float(v_final), 2)

```

========================================================
FILE: backend/fusion/threat_matrix.py
========================================================

```python
"""
SMART-SHIELD v3.0 Threat Scoring Matrix & Prioritization Engine
Implements multi-variable mathematical threat evaluation and priority target election.
"""

import math
from typing import List, Dict, Any, Optional
from ..config import config

class ThreatEvaluationEngine:
    """Evaluates real-time threat scores (0-100) and elects primary priority targets."""
    
    @staticmethod
    def calculate_threat_score(
        distance_m: float,
        speed_ms: float,
        azimuth_deg: float,
        heading_deg: float,
        optical_confidence: float,
        classification: str,
        behavior_factor: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculates threat score S_threat in [0, 100]:
        S_threat = w1*f_D + w2*f_V + w3*f_theta + w4*C_class + w5*B_err
        """
        weights = config.threat
        
        # 1. Proximity Term f_D (Closer targets have higher threat weight)
        d_norm = max(0.0, min(1.0, distance_m / weights.max_detection_range_m))
        f_D = (1.0 - d_norm) * 100.0

        # 2. Speed / Velocity Term f_V (Faster moving targets increase threat level)
        v_norm = max(0.0, min(1.0, abs(speed_ms) / weights.max_expected_speed_ms))
        f_V = v_norm * 100.0

        # 3. Trajectory / Heading Vector Term f_theta (Heading directly towards base increases risk)
        # alpha is relative angle between target velocity vector and sensor origin
        alpha_rad = math.radians(abs(heading_deg - azimuth_deg))
        cos_alpha = math.cos(alpha_rad)
        f_theta = max(0.0, (cos_alpha + 1.0) / 2.0) * 100.0

        # 4. Classification Confidence Term C_class (Drones/Quadcopters have higher risk multiplier)
        class_multiplier = 1.0 if classification in ["Drone", "Quadcopter"] else (0.8 if classification == "Fixed-Wing" else 0.2)
        f_class = optical_confidence * class_multiplier * 100.0

        # 5. Behavior Anomaly Factor B_err (Erratic maneuvers / non-ballistic high jerk)
        f_behavior = max(0.0, min(1.0, behavior_factor)) * 100.0

        # Total Weighted Score
        raw_score = (
            weights.w_distance * f_D +
            weights.w_speed * f_V +
            weights.w_direction * f_theta +
            weights.w_confidence * f_class +
            weights.w_behavior * f_behavior
        )
        total_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Classify Threat Level
        if total_score >= weights.high_threat_threshold:
            threat_level = "HIGH"
        elif total_score >= weights.medium_threat_threshold:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"

        return {
            "threat_score": total_score,
            "threat_level": threat_level,
            "components": {
                "proximity_score": round(f_D, 1),
                "speed_score": round(f_V, 1),
                "trajectory_score": round(f_theta, 1),
                "classification_score": round(f_class, 1),
                "behavior_score": round(f_behavior, 1)
            }
        }

    @staticmethod
    def prioritize_targets(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts all active targets descending by threat score and flags Priority Target #01."""
        sorted_targets = sorted(targets, key=lambda t: t.get("threat_score", 0.0), reverse=True)
        for idx, t in enumerate(sorted_targets):
            t["priority_rank"] = idx + 1
            t["is_highest_priority"] = (idx == 0)
        return sorted_targets
```

========================================================
FILE: backend/fusion/trajectory_predictor.py
========================================================

```python
"""
SMART-SHIELD v3.0 Trajectory & Intercept Predictor
Projects future 3D multi-target flight paths, Closest Point of Approach (CPA), and Time-to-Impact (TTI).
"""

import math
from typing import List, Dict, Any, Tuple, Optional

class TrajectoryPredictor:
    """Predicts future target positions and computes tactical intercept / threat metrics."""
    def __init__(self, default_horizon_seconds: float = 3.0, step_dt: float = 0.5):
        self.default_horizon = default_horizon_seconds
        self.step_dt = step_dt

    def predict_future_trajectory(
        self,
        x_m: float,
        y_m: float,
        z_m: float,
        vx_ms: float,
        vy_ms: float,
        vz_ms: float = 0.0,
        horizon_s: Optional[float] = None
    ) -> List[Dict[str, float]]:
        """
        Projects future (x, y, z) waypoints over time using a Constant Velocity (CV) kinematic motion model.
        Returns a list of timestamped waypoints {t_sec, x_m, y_m, z_m, distance_m}.
        """
        horizon = horizon_s or self.default_horizon
        waypoints = []
        num_steps = int(horizon / self.step_dt)

        for step in range(1, num_steps + 1):
            t = step * self.step_dt
            fut_x = x_m + (vx_ms * t)
            fut_y = y_m + (vy_ms * t)
            fut_z = z_m + (vz_ms * t)
            fut_dist = math.sqrt(fut_x**2 + fut_y**2 + fut_z**2)
            fut_az = math.degrees(math.atan2(fut_x, fut_y))

            waypoints.append({
                "t_sec": round(t, 2),
                "x_m": round(fut_x, 2),
                "y_m": round(fut_y, 2),
                "z_m": round(fut_z, 2),
                "distance_m": round(fut_dist, 2),
                "azimuth_deg": round(fut_az, 2)
            })

        return waypoints

    def calculate_closest_point_of_approach(
        self,
        x_m: float,
        y_m: float,
        z_m: float,
        vx_ms: float,
        vy_ms: float,
        vz_ms: float = 0.0
    ) -> Dict[str, float]:
        """
        Computes Closest Point of Approach (CPA):
        t_CPA = - (r . v) / ||v||^2
        d_CPA = || r + v * t_CPA ||
        """
        v_sq = vx_ms**2 + vy_ms**2 + vz_ms**2
        speed = math.sqrt(v_sq)

        if speed < 0.1:
            curr_dist = math.sqrt(x_m**2 + y_m**2 + z_m**2)
            return {
                "t_cpa_sec": 0.0,
                "d_cpa_m": round(curr_dist, 2),
                "is_inbound": False,
                "closure_rate_ms": 0.0
            }

        # Dot product r . v
        r_dot_v = (x_m * vx_ms) + (y_m * vy_ms) + (z_m * vz_ms)
        curr_dist = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        closure_rate = r_dot_v / curr_dist  # Negative means closing in

        t_cpa = - r_dot_v / v_sq
        is_inbound = (t_cpa > 0.0)

        if is_inbound:
            cpa_x = x_m + (vx_ms * t_cpa)
            cpa_y = y_m + (vy_ms * t_cpa)
            cpa_z = z_m + (vz_ms * t_cpa)
            d_cpa = math.sqrt(cpa_x**2 + cpa_y**2 + cpa_z**2)
        else:
            t_cpa = 0.0
            d_cpa = curr_dist

        return {
            "t_cpa_sec": round(t_cpa, 2),
            "d_cpa_m": round(d_cpa, 2),
            "is_inbound": is_inbound,
            "closure_rate_ms": round(closure_rate, 2)
        }
```

========================================================
FILE: backend/fusion/ekf.py
========================================================

```python
"""
SMART-SHIELD v3.0 Extended Kalman Filter (EKF) Sensor Fusion
Fuses 2D optical bounding box centroids with 3D mmWave radar polar/cartesian vectors.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple

class TargetEKFFilter:
    """
    State vector x = [X, Y, Z, Vx, Vy, Vz]^T
    Fuses:
      - Radar measurements: [Range r, Azimuth theta, Radial Velocity vr]
      - Camera measurements: [Pixel u, Pixel v]
    """
    def __init__(self, init_x: float, init_y: float, init_z: float = 15.0, init_vx: float = 0.0, init_vy: float = -10.0, init_vz: float = 0.0):
        # State vector [X, Y, Z, Vx, Vy, Vz]
        self.x = np.array([init_x, init_y, init_z, init_vx, init_vy, init_vz], dtype=float)
        
        # State covariance P
        self.P = np.diag([5.0, 5.0, 5.0, 2.0, 2.0, 2.0])
        
        # Process noise Q
        self.Q = np.diag([0.2, 0.2, 0.2, 0.5, 0.5, 0.5])
        
        # Measurement noise R for Radar [r, theta, vr]
        self.R_radar = np.diag([1.0, math.radians(2.0)**2, 0.8])
        
        # Measurement noise R for Camera [u, v]
        self.R_cam = np.diag([4.0, 4.0])

    def predict(self, dt: float = 0.033):
        """State transition update: x_k = F * x_{k-1}"""
        F = np.eye(6)
        F[0, 3] = dt
        F[1, 4] = dt
        F[2, 5] = dt
        
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q

    def update_radar(self, r_meas: float, theta_rad_meas: float, vr_meas: float):
        """EKF non-linear update for radar polar coordinates."""
        px, py, pz, vx, vy, vz = self.x
        r_pred = math.sqrt(px**2 + py**2 + pz**2)
        if r_pred < 0.01:
            return

        theta_pred = math.atan2(px, py)
        vr_pred = (px * vx + py * vy + pz * vz) / r_pred

        # Measurement residual y
        z = np.array([r_meas, theta_rad_meas, vr_meas])
        h_x = np.array([r_pred, theta_pred, vr_pred])
        y = z - h_x

        # Jacobian Matrix H
        H = np.zeros((3, 6))
        # dr / d[px, py, pz]
        H[0, 0] = px / r_pred
        H[0, 1] = py / r_pred
        H[0, 2] = pz / r_pred

        # dtheta / d[px, py]
        d_denom = px**2 + py**2
        if d_denom > 0.01:
            H[1, 0] = py / d_denom
            H[1, 1] = -px / d_denom

        # dvr / d[x, v]
        H[2, 0] = (vx * r_pred - (px * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 1] = (vy * r_pred - (py * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 2] = (vz * r_pred - (pz * (px*vx + py*vy + pz*vz)) / r_pred) / (r_pred**2)
        H[2, 3] = px / r_pred
        H[2, 4] = py / r_pred
        H[2, 5] = pz / r_pred

        # Kalman Gain K
        S = H @ self.P @ H.T + self.R_radar
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(6) - K @ H) @ self.P

    def get_fused_state(self) -> Dict[str, float]:
        px, py, pz, vx, vy, vz = self.x
        distance = math.sqrt(px**2 + py**2 + pz**2)
        azimuth_deg = math.degrees(math.atan2(px, py))
        speed = math.sqrt(vx**2 + vy**2 + vz**2)
        return {
            "x_m": round(float(px), 2),
            "y_m": round(float(py), 2),
            "z_m": round(float(pz), 2),
            "vx_ms": round(float(vx), 2),
            "vy_ms": round(float(vy), 2),
            "vz_ms": round(float(vz), 2),
            "distance_m": round(float(distance), 2),
            "azimuth_deg": round(float(azimuth_deg), 2),
            "speed_ms": round(float(speed), 2)
        }
```

========================================================
FILE: backend/fusion/state_estimator.py
========================================================

```python
"""
SMART-SHIELD v3.0 State Estimator Module
Re-exports the Extended Kalman Filter (EKF) state estimator from ekf.py.
"""

from .ekf import TargetEKFFilter

# Alias for standard naming
StateEstimator = TargetEKFFilter

__all__ = ["TargetEKFFilter", "StateEstimator"]
```

========================================================
FILE: backend/gimbal/__init__.py
========================================================

```python
# Gimbal package
```

========================================================
FILE: backend/gimbal/pid.py
========================================================

```python
"""
SMART-SHIELD v3.0 Pan/Tilt Gimbal Closed-Loop PID Controller
Calculates servo angle adjustments to center the highest priority target in optical feed.
"""

import time
from typing import Tuple
from ..config import config

class PIDGimbalController:
    """Dual-axis PID controller for PCA9685 pan/tilt servos."""
    def __init__(self):
        cfg = config.gimbal
        self.pan_angle = cfg.pan_center_deg
        self.tilt_angle = cfg.tilt_center_deg

        self.kp_pan = cfg.kp_pan
        self.ki_pan = cfg.ki_pan
        self.kd_pan = cfg.kd_pan

        self.kp_tilt = cfg.kp_tilt
        self.ki_tilt = cfg.ki_tilt
        self.kd_tilt = cfg.kd_tilt

        self.prev_error_x = 0.0
        self.integral_x = 0.0
        self.prev_error_y = 0.0
        self.integral_y = 0.0
        self.last_time = time.time()
        self.auto_track_enabled = True

    def reset_integrators(self):
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0

    def compute_tracking_angles(
        self,
        target_center_u: float,
        target_center_v: float,
        frame_width: int = 640,
        frame_height: int = 460
    ) -> Tuple[float, float]:
        """Calculates updated Pan and Tilt angles based on optical pixel offset from center."""
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_time))
        self.last_time = now

        if not self.auto_track_enabled:
            return self.pan_angle, self.tilt_angle

        # Pixel error relative to optical center
        error_x = target_center_u - (frame_width / 2.0)
        error_y = (frame_height / 2.0) - target_center_v  # Inverted for elevation

        # Pan axis PID
        self.integral_x += error_x * dt
        derivative_x = (error_x - self.prev_error_x) / dt
        self.prev_error_x = error_x
        pan_correction = (self.kp_pan * error_x) + (self.ki_pan * self.integral_x) + (self.kd_pan * derivative_x)

        # Tilt axis PID
        self.integral_y += error_y * dt
        derivative_y = (error_y - self.prev_error_y) / dt
        self.prev_error_y = error_y
        tilt_correction = (self.kp_tilt * error_y) + (self.ki_tilt * self.integral_y) + (self.kd_tilt * derivative_y)

        # Apply corrections to current angles (constrained by hardware limits)
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, self.pan_angle + pan_correction))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, self.tilt_angle + tilt_correction))

        return round(self.pan_angle, 1), round(self.tilt_angle, 1)

    def set_manual_angles(self, pan_deg: float, tilt_deg: float):
        """Allows direct operator manual joystick control."""
        cfg = config.gimbal
        self.pan_angle = max(cfg.pan_min_deg, min(cfg.pan_max_deg, pan_deg))
        self.tilt_angle = max(cfg.tilt_min_deg, min(cfg.tilt_max_deg, tilt_deg))
        self.reset_integrators()
```

========================================================
FILE: backend/gimbal/servo_control.py
========================================================

```python
"""
SMART-SHIELD v3.0 Servo Control Module
Re-exports the closed-loop PID gimbal controller from pid.py.
"""

from .pid import PIDGimbalController

# Standard alias
ServoController = PIDGimbalController

__all__ = ["PIDGimbalController", "ServoController"]
```

========================================================
FILE: backend/hardware/__init__.py
========================================================

```python
# Hardware package
```

========================================================
FILE: backend/hardware/esp32_serial.py
========================================================

```python
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
```

========================================================
FILE: backend/hardware/radar_interface.py
========================================================

```python
"""
SMART-SHIELD v3.0 Radar Interface Module
Re-exports the LD2450RadarParser and serial reader from esp32_serial.
"""

from .esp32_serial import LD2450RadarParser, ESP32SerialController

__all__ = ["LD2450RadarParser", "ESP32SerialController"]
```

========================================================
FILE: backend/cyber_defense/__init__.py
========================================================

```python
# Cyber defense package
```

========================================================
FILE: backend/cyber_defense/rf_monitor.py
========================================================

```python
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
```

========================================================
FILE: database/__init__.py
========================================================

```python
# Package init
```

========================================================
FILE: database/schema.sql
========================================================

```sql
-- ============================================================================
-- SMART-SHIELD v3.0 Database Schema
-- Database: PostgreSQL 14+ with TimescaleDB Extension (or standard PostgreSQL)
-- ============================================================================

-- Enable TimescaleDB extension if available
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. Persistent Targets Master Table
CREATE TABLE IF NOT EXISTS targets (
    target_id VARCHAR(32) PRIMARY KEY,
    first_detected TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    classification VARCHAR(32) NOT NULL DEFAULT 'Unknown', -- 'Drone', 'Quadcopter', 'Fixed-Wing', 'Unknown'
    initial_distance_m FLOAT NOT NULL,
    max_threat_score FLOAT NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' -- 'ACTIVE', 'NEUTRALIZED', 'LOST', 'DISMISSED'
);

-- 2. Timeseries Target Kinematic Telemetry Table
CREATE TABLE IF NOT EXISTS target_telemetry (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_id VARCHAR(32) NOT NULL REFERENCES targets(target_id) ON DELETE CASCADE,
    x_pos_m FLOAT NOT NULL,
    y_pos_m FLOAT NOT NULL,
    z_pos_m FLOAT DEFAULT 0.0,
    distance_m FLOAT NOT NULL,
    azimuth_deg FLOAT NOT NULL,
    elevation_deg FLOAT DEFAULT 0.0,
    speed_ms FLOAT NOT NULL,
    heading_deg FLOAT DEFAULT 0.0,
    optical_confidence FLOAT NOT NULL,
    radar_snr FLOAT NOT NULL,
    threat_score FLOAT NOT NULL,
    threat_level VARCHAR(10) NOT NULL -- 'LOW', 'MEDIUM', 'HIGH'
);

-- Create optimized index for fast spatial-temporal queries
CREATE INDEX IF NOT EXISTS idx_telemetry_time_target ON target_telemetry (timestamp DESC, target_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_threat ON target_telemetry (threat_score DESC);

-- Convert to hypertable if TimescaleDB is loaded
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('target_telemetry', 'timestamp', if_not_exists => TRUE);
    END IF;
END $$;

-- 3. Cyber-Defence & RF Spectrum Incident Log Table
CREATE TABLE IF NOT EXISTS cyber_rf_events (
    event_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(32) NOT NULL, -- 'JAMMING_ATTEMPT', 'SIGNAL_SPOOFING', 'UNAUTHORIZED_C2', 'FREQ_ANOMALY'
    frequency_mhz FLOAT NOT NULL,
    rssi_dbm FLOAT NOT NULL,
    noise_floor_delta_db FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL DEFAULT 'WARNING', -- 'INFO', 'WARNING', 'CRITICAL'
    countermeasure_taken VARCHAR(64) DEFAULT NULL, -- 'CHANNEL_HOP_CH11', 'ANTENNA_HARDENING', 'ALERT_OPERATOR'
    resolved_at TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_rf_events_time ON cyber_rf_events (timestamp DESC);

-- 4. System Health & Hardware Audit Logs Table
CREATE TABLE IF NOT EXISTS system_audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subsystem VARCHAR(32) NOT NULL, -- 'ESP32', 'LD2450_RADAR', 'GIMBAL_PCA9685', 'AI_ENGINE', 'RF_MONITOR', 'OPERATOR'
    event_message TEXT NOT NULL,
    battery_voltage FLOAT DEFAULT 12.6,
    core_temp_c FLOAT DEFAULT 42.0,
    gimbal_pan_deg FLOAT DEFAULT 90.0,
    gimbal_tilt_deg FLOAT DEFAULT 45.0
);

CREATE INDEX IF NOT EXISTS idx_system_logs_time ON system_audit_logs (timestamp DESC);
```

========================================================
FILE: database/db_manager.py
========================================================

```python
"""
SMART-SHIELD v3.0 Database & In-Memory Ring Buffer Manager
Handles async persistence of telemetry, targets, cyber events, and audit logs.
Provides an automatic in-memory fallback when external DB is not connected.
"""

import asyncio
import time
import logging
from collections import deque
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SmartShield.DBManager")

class TelemetryRingBuffer:
    """High-speed in-memory circular buffer for 30Hz telemetry data."""
    def __init__(self, max_len: int = 1000):
        self.buffer = deque(maxlen=max_len)
        self.targets_cache: Dict[str, Dict[str, Any]] = {}
        self.cyber_events: deque = deque(maxlen=200)
        self.audit_logs: deque = deque(maxlen=500)

    def record_telemetry(self, telemetry_data: Dict[str, Any]):
        timestamp = time.time()
        telemetry_data["timestamp"] = timestamp
        self.buffer.append(telemetry_data)

        # Update targets cache
        target_id = telemetry_data.get("target_id")
        if target_id:
            if target_id not in self.targets_cache:
                self.targets_cache[target_id] = {
                    "target_id": target_id,
                    "first_detected": timestamp,
                    "last_detected": timestamp,
                    "classification": telemetry_data.get("classification", "Unknown"),
                    "initial_distance_m": telemetry_data.get("distance_m", 0.0),
                    "max_threat_score": telemetry_data.get("threat_score", 0.0),
                    "status": "ACTIVE"
                }
            else:
                target = self.targets_cache[target_id]
                target["last_detected"] = timestamp
                if telemetry_data.get("threat_score", 0.0) > target["max_threat_score"]:
                    target["max_threat_score"] = telemetry_data["threat_score"]

    def log_cyber_event(self, event_data: Dict[str, Any]):
        event_data["timestamp"] = time.time()
        self.cyber_events.append(event_data)
        logger.warning(f"CYBER EVENT LOGGED: {event_data.get('event_type')} - {event_data.get('severity')}")

    def log_audit(self, subsystem: str, message: str, **kwargs):
        log_entry = {
            "timestamp": time.time(),
            "subsystem": subsystem,
            "message": message,
            **kwargs
        }
        self.audit_logs.append(log_entry)
        logger.info(f"[{subsystem}] {message}")

    def get_active_targets(self) -> List[Dict[str, Any]]:
        now = time.time()
        active = []
        for tid, data in list(self.targets_cache.items()):
            # Consider active if seen in last 3 seconds
            if now - data["last_detected"] < 3.0:
                active.append(data)
            else:
                data["status"] = "LOST"
        return active

    def get_recent_cyber_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(self.cyber_events)[-limit:]


import sqlite3
import os
import csv
import io
import json

class DatabaseManager:
    """Async & Local Persistent Database Manager supporting SQLite & PostgreSQL."""
    def __init__(self, dsn: Optional[str] = None, sqlite_path: str = "database/smart_shield.db"):
        self.dsn = dsn
        self.sqlite_path = sqlite_path
        self.ring_buffer = TelemetryRingBuffer()
        self.is_connected = False
        self.use_sqlite = True
        self._pool = None
        self._sqlite_conn = None

    async def initialize(self):
        """Initializes PostgreSQL connection pool if DSN provided, otherwise initializes local SQLite database."""
        if self.dsn:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
                self.is_connected = True
                self.use_sqlite = False
                logger.info("Connected to PostgreSQL/TimescaleDB cluster successfully.")
                return
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed ({e}). Defaulting to Local SQLite Persistent Mode.")
        
        # Initialize Local SQLite database
        try:
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            self._sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self._init_sqlite_tables()
            self.use_sqlite = True
            logger.info(f"Local SQLite database initialized at {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite ({e}). Operating in in-memory mode only.")
            self.use_sqlite = False

    def _init_sqlite_tables(self):
        """Creates target_telemetry and cyber_rf_events SQLite tables if not present."""
        if not self._sqlite_conn:
            return
        cur = self._sqlite_conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                target_id TEXT PRIMARY KEY,
                first_detected REAL,
                last_detected REAL,
                classification TEXT,
                initial_distance_m REAL,
                max_threat_score REAL,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS target_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                target_id TEXT,
                x_pos_m REAL,
                y_pos_m REAL,
                z_pos_m REAL,
                distance_m REAL,
                azimuth_deg REAL,
                elevation_deg REAL,
                speed_ms REAL,
                heading_deg REAL,
                optical_confidence REAL,
                radar_snr REAL,
                threat_score REAL,
                threat_level TEXT
            );

            CREATE TABLE IF NOT EXISTS cyber_rf_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                frequency_mhz REAL,
                rssi_dbm REAL,
                noise_floor_delta_db REAL,
                severity TEXT,
                countermeasure_taken TEXT
            );
        """)
        self._sqlite_conn.commit()

    async def save_telemetry(self, telemetry_data: Dict[str, Any]):
        self.ring_buffer.record_telemetry(telemetry_data)
        
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    INSERT INTO target_telemetry (
                        timestamp, target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                        azimuth_deg, elevation_deg, speed_ms, heading_deg,
                        optical_confidence, radar_snr, threat_score, threat_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    telemetry_data["target_id"], telemetry_data["x_pos_m"], telemetry_data["y_pos_m"],
                    telemetry_data.get("z_pos_m", 0.0), telemetry_data["distance_m"], telemetry_data["azimuth_deg"],
                    telemetry_data.get("elevation_deg", 0.0), telemetry_data["speed_ms"], telemetry_data.get("heading_deg", 0.0),
                    telemetry_data["optical_confidence"], telemetry_data["radar_snr"], telemetry_data["threat_score"],
                    telemetry_data["threat_level"]
                ))
                self._sqlite_conn.commit()
            except Exception as e:
                logger.error(f"SQLite telemetry persist failed: {e}")

        elif self.is_connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO target_telemetry (
                            target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                            azimuth_deg, elevation_deg, speed_ms, heading_deg,
                            optical_confidence, radar_snr, threat_score, threat_level
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, 
                    telemetry_data["target_id"], telemetry_data["x_pos_m"], telemetry_data["y_pos_m"],
                    telemetry_data.get("z_pos_m", 0.0), telemetry_data["distance_m"], telemetry_data["azimuth_deg"],
                    telemetry_data.get("elevation_deg", 0.0), telemetry_data["speed_ms"], telemetry_data.get("heading_deg", 0.0),
                    telemetry_data["optical_confidence"], telemetry_data["radar_snr"], telemetry_data["threat_score"],
                    telemetry_data["threat_level"])
            except Exception as e:
                logger.error(f"PostgreSQL telemetry persist failed: {e}")

    async def save_cyber_event(self, event_data: Dict[str, Any]):
        self.ring_buffer.log_cyber_event(event_data)
        
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    INSERT INTO cyber_rf_events (
                        timestamp, event_type, frequency_mhz, rssi_dbm, noise_floor_delta_db,
                        severity, countermeasure_taken
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    event_data["event_type"], event_data.get("frequency_mhz", 2412.0),
                    event_data.get("rssi_dbm", -85.0), event_data.get("delta_db", 0.0),
                    event_data.get("severity", "WARNING"), event_data.get("message", "N/A")
                ))
                self._sqlite_conn.commit()
            except Exception as e:
                logger.error(f"SQLite cyber event persist failed: {e}")

    def get_historical_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent recorded trajectory points for mission playback."""
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    SELECT timestamp, target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                           azimuth_deg, speed_ms, threat_score, threat_level
                    FROM target_telemetry
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cur.fetchall()
                results = []
                for r in reversed(rows):
                    results.append({
                        "timestamp": r[0], "target_id": r[1], "x_m": r[2], "y_m": r[3],
                        "z_m": r[4], "distance_m": r[5], "azimuth_deg": r[6], "speed_ms": r[7],
                        "threat_score": r[8], "threat_level": r[9]
                    })
                return results
            except Exception as e:
                logger.error(f"Failed to query SQLite history: {e}")
        
        # Fallback to ring buffer
        return list(self.ring_buffer.buffer)[-limit:]

    def export_csv_report(self) -> str:
        """Exports recent telemetry & threat scoring as a CSV string."""
        history = self.get_historical_telemetry(limit=500)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Target_ID", "X_m", "Y_m", "Z_m", "Distance_m", "Azimuth_deg", "Speed_ms", "Threat_Score", "Threat_Level"])
        for h in history:
            writer.writerow([
                h.get("timestamp"), h.get("target_id"), h.get("x_m") or h.get("x_pos_m"),
                h.get("y_m") or h.get("y_pos_m"), h.get("z_m") or h.get("z_pos_m", 0.0),
                h.get("distance_m"), h.get("azimuth_deg"), h.get("speed_ms"),
                h.get("threat_score"), h.get("threat_level")
            ])
        return output.getvalue()

    async def close(self):
        if self._sqlite_conn:
            self._sqlite_conn.close()
            logger.info("SQLite database connection closed.")
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL database connection pool closed.")

```

========================================================
FILE: firmware/esp32_smart_shield/README.md
========================================================

```markdown
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
```

========================================================
FILE: firmware/esp32_smart_shield/esp32_smart_shield.ino
========================================================

```cpp
/*
 * =====================================================================================
 * SMART-SHIELD v3.0: Microcontroller Firmware (ESP32)
 * AI-Powered Multi-Target Drone Detection, Tracking & Cyber-Defence Edge Controller
 * =====================================================================================
 * Pinout / Interfaces:
 * - LD2450 mmWave Radar: Serial2 (RX2: GPIO 16, TX2: GPIO 17 @ 256000 bps)
 * - PCA9685 16-Ch PWM Servo Driver: I2C (SDA: GPIO 21, SCL: GPIO 22, Addr: 0x40)
 * - SSD1306 128x64 OLED Display: I2C (SDA: GPIO 21, SCL: GPIO 22, Addr: 0x3C)
 * - WS2812B RGB Alert LEDs: GPIO 18 (8 LEDs NeoPixel Ring / Strip)
 * - Active Piezo Threat Buzzer: GPIO 19
 * - HC-SR04 Ultrasonic Sensor: Trig: GPIO 4, Echo: GPIO 5
 * - Battery Voltage Divider: ADC GPIO 34 (100k / 22k divider, 12V Li-ion monitor)
 * - AI Engine / Laptop CDC Link: Serial (USB @ 115200 bps)
 * =====================================================================================
 */

#include <Wire.h>
#include <ArduinoJson.h>
#include <Adafruit_PWMServoDriver.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>

// ----------------- PIN DEFINITIONS -----------------
#define RADAR_RX_PIN        16
#define RADAR_TX_PIN        17
#define I2C_SDA_PIN         21
#define I2C_SCL_PIN         22
#define RGB_LED_PIN         18
#define BUZZER_PIN          19
#define ULTRASONIC_TRIG_PIN 4
#define ULTRASONIC_ECHO_PIN 5
#define BATTERY_ADC_PIN     34

#define NUM_LEDS            8
#define SCREEN_WIDTH        128
#define SCREEN_HEIGHT       64
#define OLED_RESET          -1

// PCA9685 Servo Channels & Pulse Lengths
#define SERVO_PAN_CH        0
#define SERVO_TILT_CH       1
#define SERVOMIN            150  // 0 degrees (~500us at 50Hz)
#define SERVOMAX            600  // 180 degrees (~2500us at 50Hz)

// ----------------- HARDWARE OBJECTS -----------------
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_NeoPixel strip(NUM_LEDS, RGB_LED_PIN, NEO_GRB + NEO_KHZ800);

// ----------------- SYSTEM STATE VARIABLES -----------------
struct RadarTarget {
  int16_t x_mm;
  int16_t y_mm;
  int16_t speed_cms;
  uint16_t snr_resolution;
  bool valid;
};

RadarTarget radarTargets[3];
float currentPanAngle = 90.0;
float currentTiltAngle = 45.0;
String currentThreatLevel = "LOW";
bool buzzerActive = false;
float batteryVoltage = 12.4;
float ultrasonicDistanceMeters = 0.0;
uint32_t lastTelemetryTime = 0;
uint32_t lastOledUpdateTime = 0;
uint32_t lastUltrasonicTime = 0;
uint32_t strobeTimer = 0;
bool strobeState = false;

// ----------------- HELPER FUNCTIONS -----------------

uint16_t angleToPwm(float angleDeg) {
  angleDeg = constrain(angleDeg, 0.0, 180.0);
  return map((int)(angleDeg * 10), 0, 1800, SERVOMIN, SERVOMAX);
}

void setGimbalServos(float pan, float tilt) {
  currentPanAngle = constrain(pan, 0.0, 180.0);
  currentTiltAngle = constrain(tilt, 15.0, 90.0);
  
  pwm.setPWM(SERVO_PAN_CH, 0, angleToPwm(currentPanAngle));
  pwm.setPWM(SERVO_TILT_CH, 0, angleToPwm(currentTiltAngle));
}

void updateLeds() {
  uint32_t now = millis();
  if (currentThreatLevel == "HIGH") {
    // Fast Red Strobe for Critical High Threat
    if (now - strobeTimer > 100) {
      strobeTimer = now;
      strobeState = !strobeState;
      uint32_t color = strobeState ? strip.Color(255, 0, 0) : strip.Color(0, 0, 0);
      for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, color);
      strip.show();
    }
  } else if (currentThreatLevel == "MEDIUM") {
    // Steady Amber/Yellow for Elevated Threat
    for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(255, 140, 0));
    strip.show();
  } else {
    // Calm Green Breathing Pulse for Nominal State
    uint8_t brightness = (sin(now / 400.0) + 1.0) * 40 + 10;
    for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, strip.Color(0, brightness, 0));
    strip.show();
  }
}

void updateBuzzer() {
  if (buzzerActive || currentThreatLevel == "HIGH") {
    // Pulsed warning tone (2.4kHz)
    if ((millis() / 150) % 2 == 0) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
}

void readUltrasonicSensor() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  
  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration > 0) {
    ultrasonicDistanceMeters = (duration * 0.0343) / 2.0 / 100.0; // in meters
  } else {
    ultrasonicDistanceMeters = 4.0; // Out of range
  }
}

void readBatteryVoltage() {
  int rawAdc = analogRead(BATTERY_ADC_PIN);
  // Divider: R1=100k, R2=22k -> Ratio = (100+22)/22 = 5.545
  // ESP32 ADC: 3.3V / 4095
  float pinVoltage = (rawAdc / 4095.0) * 3.3;
  batteryVoltage = pinVoltage * 5.545;
}

void updateOledDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Header
  display.setCursor(0, 0);
  display.print("SMART-SHIELD v3.0 C2");
  display.drawFastHLine(0, 10, SCREEN_WIDTH, SSD1306_WHITE);
  
  // System Status
  display.setCursor(0, 14);
  display.print("STATE: ARMED");
  display.setCursor(75, 14);
  display.print(batteryVoltage, 1);
  display.print("V");
  
  // Threat Level
  display.setCursor(0, 26);
  display.print("THREAT: ");
  display.print(currentThreatLevel);
  
  // Gimbal Coordinates
  display.setCursor(0, 38);
  display.print("PAN: ");
  display.print(currentPanAngle, 1);
  display.print((char)247);
  display.print(" TILT: ");
  display.print(currentTiltAngle, 1);
  display.print((char)247);
  
  // Radar & Proximity
  int activeCount = 0;
  for (int i = 0; i < 3; i++) if (radarTargets[i].valid) activeCount++;
  display.setCursor(0, 50);
  display.print("RADAR TRK: 0");
  display.print(activeCount);
  display.print(" PROX:");
  display.print(ultrasonicDistanceMeters, 1);
  display.print("m");
  
  display.display();
}

// ----------------- LD2450 RADAR PARSER -----------------

void parseRadarFrame() {
  // LD2450 Frame: Header 0xAA 0xFF 0x03 0x00 (4B) + 3 targets (8B each) + Tail 0x55 0xCC (2B) = 30 Bytes
  while (Serial2.available() >= 30) {
    if (Serial2.read() == 0xAA && Serial2.peek() == 0xFF) {
      uint8_t buffer[29];
      Serial2.readBytes(buffer, 29);
      
      if (buffer[0] == 0xFF && buffer[1] == 0x03 && buffer[2] == 0x00 &&
          buffer[27] == 0x55 && buffer[28] == 0xCC) {
        
        // Parse 3 target slots
        for (int i = 0; i < 3; i++) {
          int offset = 3 + i * 8;
          int16_t x = (int16_t)(buffer[offset] | (buffer[offset + 1] << 8));
          int16_t y = (int16_t)(buffer[offset + 2] | (buffer[offset + 3] << 8));
          int16_t speed = (int16_t)(buffer[offset + 4] | (buffer[offset + 5] << 8));
          uint16_t res = (uint16_t)(buffer[offset + 6] | (buffer[offset + 7] << 8));
          
          if (x != 0 || y != 0) {
            radarTargets[i].x_mm = x;
            radarTargets[i].y_mm = y;
            radarTargets[i].speed_cms = speed;
            radarTargets[i].snr_resolution = res;
            radarTargets[i].valid = true;
          } else {
            radarTargets[i].valid = false;
          }
        }
      }
    }
  }
}

// ----------------- JSON HOST COMMUNICATION -----------------

void sendTelemetryToHost() {
  StaticJsonDocument<512> doc;
  doc["timestamp"] = millis();
  doc["status"] = "ARMED";
  doc["battery_v"] = round(batteryVoltage * 10.0) / 10.0;
  doc["ultrasonic_m"] = round(ultrasonicDistanceMeters * 10.0) / 10.0;
  
  JsonObject gimbal = doc.createNestedObject("gimbal");
  gimbal["pan"] = currentPanAngle;
  gimbal["tilt"] = currentTiltAngle;
  
  JsonArray targetsArray = doc.createNestedArray("radar_targets");
  for (int i = 0; i < 3; i++) {
    if (radarTargets[i].valid) {
      JsonObject t = targetsArray.createNestedObject();
      t["slot"] = i + 1;
      t["x_mm"] = radarTargets[i].x_mm;
      t["y_mm"] = radarTargets[i].y_mm;
      t["speed_cms"] = radarTargets[i].speed_cms;
      t["snr"] = radarTargets[i].snr_resolution;
    }
  }
  
  serializeJson(doc, Serial);
  Serial.println();
}

void processIncomingHostCommands() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;
    
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, line);
    if (!error) {
      if (doc.containsKey("pan") && doc.containsKey("tilt")) {
        float p = doc["pan"];
        float t = doc["tilt"];
        setGimbalServos(p, t);
      }
      if (doc.containsKey("threat")) {
        currentThreatLevel = doc["threat"].as<String>();
      }
      if (doc.containsKey("buzzer")) {
        buzzerActive = doc["buzzer"].as<bool>();
      }
    }
  }
}

// ----------------- ARDUINO SETUP & LOOP -----------------

void setup() {
  // 1. USB Serial Link to Laptop AI Engine
  Serial.begin(115200);
  
  // 2. Hardware Serial2 for LD2450 mmWave Radar
  Serial2.begin(256000, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);
  
  // 3. I2C Bus initialization
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  
  // 4. Initialize PCA9685 PWM Servo Driver
  pwm.begin();
  pwm.setPWMFreq(50); // 50Hz standard for servos
  setGimbalServos(90.0, 45.0); // Center positions
  
  // 5. Initialize SSD1306 OLED Display
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
    display.display();
  }
  
  // 6. Initialize WS2812B RGB LEDs
  strip.begin();
  strip.setBrightness(80);
  strip.show();
  
  // 7. GPIO Pin Modes
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  pinMode(BATTERY_ADC_PIN, INPUT);
  
  // Initial Display Splash
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(15, 20);
  display.println("SMART-SHIELD v3.0");
  display.setCursor(10, 35);
  display.println("SYSTEM INITIALIZED");
  display.display();
  delay(800);
}

void loop() {
  uint32_t now = millis();
  
  // 1. Process LD2450 Radar Packets
  parseRadarFrame();
  
  // 2. Process Host JSON Commands
  processIncomingHostCommands();
  
  // 3. Read Ultrasonic Distance Sensor (every 100ms)
  if (now - lastUltrasonicTime > 100) {
    lastUltrasonicTime = now;
    readUltrasonicSensor();
    readBatteryVoltage();
  }
  
  // 4. Update Indicators & Actuation
  updateLeds();
  updateBuzzer();
  
  // 5. Update Local OLED Display (10Hz)
  if (now - lastOledUpdateTime > 100) {
    lastOledUpdateTime = now;
    updateOledDisplay();
  }
  
  // 6. Transmit Telemetry Packet to AI Engine (20Hz)
  if (now - lastTelemetryTime > 50) {
    lastTelemetryTime = now;
    sendTelemetryToHost();
  }
}
```

========================================================
FILE: tests/__init__.py
========================================================

```python
# Package init
```

========================================================
FILE: tests/test_system.py
========================================================

```python
"""
SMART-SHIELD v3.0 Automated Test Suite
Verifies Threat Scoring Math, LD2450 Radar Parsing, EKF State Estimation, and RF Jamming Detection.
"""

import math
import struct
import unittest

# Import system modules
from backend.hardware.esp32_serial import LD2450RadarParser
from backend.fusion.threat_matrix import ThreatEvaluationEngine
from backend.fusion.ekf import TargetEKFFilter
from backend.cyber_defense.rf_monitor import CyberRFMonitor

class TestSmartShieldCore(unittest.TestCase):

    def test_threat_scoring_math(self):
        """Validates that a fast, close-proximity drone yields HIGH threat while a distant slow object yields LOW threat."""
        # Hostile close inbound drone
        high_threat = ThreatEvaluationEngine.calculate_threat_score(
            distance_m=45.0,
            speed_ms=25.0,
            azimuth_deg=10.0,
            heading_deg=10.0,
            optical_confidence=0.98,
            classification="Drone (Hostile)",
            behavior_factor=0.9
        )
        self.assertGreaterEqual(high_threat["threat_score"], 75.0)
        self.assertEqual(high_threat["threat_level"], "HIGH")

        # Distant slow peripheral drone
        low_threat = ThreatEvaluationEngine.calculate_threat_score(
            distance_m=190.0,
            speed_ms=5.0,
            azimuth_deg=45.0,
            heading_deg=-90.0,
            optical_confidence=0.70,
            classification="Bird",
            behavior_factor=0.1
        )
        self.assertLess(low_threat["threat_score"], 40.0)
        self.assertEqual(low_threat["threat_level"], "LOW")

    def test_ld2450_radar_frame_parsing(self):
        """Validates binary unpacking of LD2450 30-byte radar packet."""
        header = bytes([0xAA, 0xFF, 0x03, 0x00])
        tail = bytes([0x55, 0xCC])
        
        # Target 1: X=-500mm, Y=3000mm, Speed=-150cm/s, Resolution=80
        t1 = struct.pack("<hhhH", -500, 3000, -150, 80)
        # Target 2 & 3 empty
        t2 = struct.pack("<hhhH", 0, 0, 0, 0)
        t3 = struct.pack("<hhhH", 0, 0, 0, 0)
        
        packet = header + t1 + t2 + t3 + tail
        self.assertEqual(len(packet), 30)

        targets = LD2450RadarParser.parse_frame(packet)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["x_m"], -0.5)
        self.assertEqual(targets[0]["y_m"], 3.0)
        self.assertEqual(targets[0]["speed_ms"], -1.5)

    def test_ekf_state_prediction_and_update(self):
        """Validates Extended Kalman Filter state propagation and radar update."""
        ekf = TargetEKFFilter(init_x=0.0, init_y=50.0, init_z=10.0, init_vx=0.0, init_vy=-10.0, init_vz=0.0)
        ekf.predict(dt=0.1)
        
        state = ekf.get_fused_state()
        self.assertAlmostEqual(state["y_m"], 49.0, delta=0.5)
        
        # Update with radar measurement at range 49.0m, azimuth 0 rad, vr -10.0 m/s
        ekf.update_radar(r_meas=49.0, theta_rad_meas=0.0, vr_meas=-10.0)
        updated_state = ekf.get_fused_state()
        self.assertGreater(updated_state["distance_m"], 0.0)

    def test_cyber_rf_jamming_and_frequency_hop(self):
        """Validates RF spectrum anomaly detection and automatic frequency hopping."""
        rf = CyberRFMonitor()
        nominal_scan = rf.get_spectrum_scan()
        self.assertEqual(nominal_scan["status"], "SECURE")

        # Inject Jamming
        rf.toggle_jamming_simulation()
        jammed_scan = rf.get_spectrum_scan()
        self.assertEqual(jammed_scan["status"], "ATTACK_DETECTED")
        self.assertEqual(jammed_scan["severity"], "CRITICAL")

        # Execute Countermeasure
        old_ch = rf.active_channel
        hop_res = rf.execute_frequency_hop()
        self.assertEqual(hop_res["status"], "SUCCESS")
        self.assertNotEqual(rf.active_channel, old_ch)

        # After frequency hop, C2 link should be secure
        cleared_scan = rf.get_spectrum_scan()
        self.assertEqual(cleared_scan["status"], "SECURE")

    def test_sqlite_persistence_and_replay(self):
        """Validates SQLite database initialization, telemetry insertion, and CSV report generation."""
        import os
        import asyncio
        from database.db_manager import DatabaseManager

        test_db_path = "database/test_smart_shield.db"
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

        async def run_db_test():
            db = DatabaseManager(sqlite_path=test_db_path)
            await db.initialize()
            self.assertTrue(db.use_sqlite)

            # Insert sample telemetry
            await db.save_telemetry({
                "target_id": "DRONE-99",
                "x_pos_m": -12.5,
                "y_pos_m": 48.0,
                "z_pos_m": 15.0,
                "distance_m": 49.6,
                "azimuth_deg": -14.6,
                "speed_ms": 22.0,
                "optical_confidence": 0.95,
                "radar_snr": 92.0,
                "threat_score": 88.5,
                "threat_level": "HIGH"
            })

            # Query replay
            history = db.get_historical_telemetry(limit=10)
            self.assertGreaterEqual(len(history), 1)
            self.assertEqual(history[0]["target_id"], "DRONE-99")
            self.assertEqual(history[0]["threat_level"], "HIGH")

            # Export CSV
            csv_text = db.export_csv_report()
            self.assertIn("DRONE-99", csv_text)
            self.assertIn("Timestamp,Target_ID", csv_text)

            await db.close()

        asyncio.run(run_db_test())
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

    def test_multitarget_swarm_prioritization(self):
        """Validates that a swarm of 6 drones is correctly evaluated and ranked by threat score."""
        targets = [
            {"id": "DRONE-01", "distance_m": 150.0, "speed_ms": 5.0, "azimuth_deg": 30.0, "heading_deg": 0.0, "optical_confidence": 0.8, "classification": "Drone", "behavior_factor": 0.2},
            {"id": "DRONE-02", "distance_m": 120.0, "speed_ms": 10.0, "azimuth_deg": -20.0, "heading_deg": 0.0, "optical_confidence": 0.85, "classification": "Quadcopter", "behavior_factor": 0.3},
            {"id": "DRONE-03", "distance_m": 35.0, "speed_ms": 26.0, "azimuth_deg": 0.0, "heading_deg": 0.0, "optical_confidence": 0.98, "classification": "Drone (Hostile)", "behavior_factor": 0.9},
            {"id": "DRONE-04", "distance_m": 180.0, "speed_ms": 4.0, "azimuth_deg": 45.0, "heading_deg": -90.0, "optical_confidence": 0.6, "classification": "Bird", "behavior_factor": 0.1},
            {"id": "DRONE-05", "distance_m": 60.0, "speed_ms": 18.0, "azimuth_deg": 10.0, "heading_deg": 10.0, "optical_confidence": 0.92, "classification": "Drone", "behavior_factor": 0.6},
            {"id": "DRONE-06", "distance_m": 90.0, "speed_ms": 12.0, "azimuth_deg": -15.0, "heading_deg": 0.0, "optical_confidence": 0.88, "classification": "Fixed-Wing", "behavior_factor": 0.4}
        ]

        scored_targets = []
        for t in targets:
            score_data = ThreatEvaluationEngine.calculate_threat_score(
                distance_m=t["distance_m"],
                speed_ms=t["speed_ms"],
                azimuth_deg=t["azimuth_deg"],
                heading_deg=t["heading_deg"],
                optical_confidence=t["optical_confidence"],
                classification=t["classification"],
                behavior_factor=t["behavior_factor"]
            )
            scored_targets.append({**t, **score_data})

        ranked = ThreatEvaluationEngine.prioritize_targets(scored_targets)
        self.assertEqual(len(ranked), 6)
        self.assertEqual(ranked[0]["id"], "DRONE-03")
        self.assertTrue(ranked[0]["is_highest_priority"])
        self.assertEqual(ranked[0]["threat_level"], "HIGH")
        self.assertGreater(ranked[0]["threat_score"], ranked[1]["threat_score"])

    def test_camera_stream_manager_synthetic_feed(self):
        """Validates that CameraStreamManager generates valid JPEG image bytes for the HUD."""
        from backend.vision.detector import CameraStreamManager
        cam = CameraStreamManager()
        detections = [
            {"id": "DRONE-01", "bbox": [100.0, 100.0, 160.0, 140.0], "center_u": 130.0, "center_v": 120.0, "width": 60.0, "height": 40.0, "confidence": 0.95, "class_name": "Drone"}
        ]
        jpeg_bytes = cam.get_annotated_frame_bytes(targets=[], detections=detections, primary_id="DRONE-01")
        self.assertIsInstance(jpeg_bytes, bytes)
        self.assertGreater(len(jpeg_bytes), 100)
        # JPEG SOI marker (0xFFD8)
        self.assertEqual(jpeg_bytes[:2], b'\xff\xd8')

    def test_optical_velocity_estimator(self):
        """Validates that OpticalVelocityEstimator calculates smooth pixel velocities and metric rates."""
        from backend.vision.velocity_estimator import OpticalVelocityEstimator
        estimator = OpticalVelocityEstimator()

        history = [
            [100.0, 100.0, 150.0, 130.0], # Frame 1 center: (125, 115)
            [110.0, 105.0, 162.0, 136.0]  # Frame 2 center: (136, 120.5) (expanding)
        ]
        timestamps = [0.0, 0.033]

        vel = estimator.estimate_velocity_from_history("TRK-01", history, timestamps, estimated_depth_m=60.0)
        self.assertIn("vel_u_px_s", vel)
        self.assertIn("speed_est_ms", vel)
        self.assertGreater(vel["vel_u_px_s"], 0.0)
        self.assertGreater(vel["speed_est_ms"], 0.0)

    def test_trajectory_predictor_and_cpa(self):
        """Validates forward trajectory prediction and Closest Point of Approach calculation."""
        from backend.fusion.trajectory_predictor import TrajectoryPredictor
        predictor = TrajectoryPredictor()

        # Inbound drone: x=20m, y=100m, moving inbound vy=-20m/s
        waypoints = predictor.predict_future_trajectory(x_m=20.0, y_m=100.0, z_m=15.0, vx_ms=0.0, vy_ms=-20.0, horizon_s=3.0)
        self.assertEqual(len(waypoints), 6) # 3.0s / 0.5s step
        self.assertLess(waypoints[-1]["y_m"], 100.0)

        # CPA test
        cpa = predictor.calculate_closest_point_of_approach(x_m=20.0, y_m=100.0, z_m=0.0, vx_ms=0.0, vy_ms=-20.0)
        self.assertTrue(cpa["is_inbound"])
        self.assertAlmostEqual(cpa["t_cpa_sec"], 5.0, delta=0.1) # 100m / 20m/s = 5s
        self.assertAlmostEqual(cpa["d_cpa_m"], 20.0, delta=0.5)

    def test_sensor_fusion_engine(self):
        """Validates SensorFusionEngine multi-sensor coordination and EKF state integration."""
        from backend.fusion.sensor_fusion import SensorFusionEngine, fuse_velocities_weighted
        fusion = SensorFusionEngine()

        sample_target = {
            "id": "DRONE-01",
            "x_m": 15.0,
            "y_m": 60.0,
            "z_m": 12.0,
            "distance_m": 61.8,
            "azimuth_deg": 14.0,
            "speed_ms": -18.0
        }
        fused = fusion.fuse_target(sample_target, dt=0.033)
        self.assertEqual(fused["id"], "DRONE-01")
        self.assertIn("cpa", fused)
        self.assertIn("vx_ms", fused)

        # Weighted velocity fusion tests (formula from Page 3)
        # Case 1: Normal agreement
        v_fused = fuse_velocities_weighted(v_camera=20.0, v_radar=18.0, w_camera=0.4, w_radar=0.6)
        self.assertAlmostEqual(v_fused, 18.8, delta=0.2)

        # Case 2: Outlier disagreement (>15m/s difference -> down-weights camera)
        v_outlier = fuse_velocities_weighted(v_camera=50.0, v_radar=10.0, disagreement_threshold=15.0)
        self.assertLess(v_outlier, 16.0) # Heavily pulled toward radar (10 m/s)

        # Case 3: Single sensor failure / missing radar
        v_cam_only = fuse_velocities_weighted(v_camera=22.0, v_radar=None)
        self.assertEqual(v_cam_only, 22.0)

    def test_camera_calibration_homography_and_pinhole(self):
        """Validates Homography planar transformation and Pinhole 3D projection."""
        from backend.vision.calibration import HomographyCalibrator, PinholeCalibrator

        # 1. Homography 4-point mapping
        img_pts = [(0.0, 0.0), (640.0, 0.0), (640.0, 460.0), (0.0, 460.0)]
        world_pts = [(-50.0, 100.0), (50.0, 100.0), (50.0, 10.0), (-50.0, 10.0)]
        homo = HomographyCalibrator(img_pts, world_pts)
        self.assertTrue(homo.is_calibrated)

        # Transform center pixel (320, 230)
        world_x, world_y = homo.pixel_to_world(320.0, 230.0)
        self.assertAlmostEqual(world_x, 0.0, delta=2.0)
        self.assertGreater(world_y, 10.0)
        self.assertLess(world_y, 100.0)

        # Reverse transformation
        pix_u, pix_v = homo.world_to_pixel(world_x, world_y)
        self.assertAlmostEqual(pix_u, 320.0, delta=5.0)
        self.assertAlmostEqual(pix_v, 230.0, delta=5.0)

        # 2. Pinhole 3D Projection
        pinhole = PinholeCalibrator(focal_length_px=400.0, principal_point=(320.0, 230.0))
        X, Y, Z = pinhole.pixel_to_3d_point(u=320.0, v=150.0, depth_m=50.0)
        self.assertAlmostEqual(X, 0.0, delta=0.1) # Center azimuth
        self.assertEqual(Y, 50.0)                 # Forward range
        self.assertGreater(Z, 0.0)                # Above horizon (positive altitude)

        # Reverse 3D to 2D
        u_proj, v_proj = pinhole.point_3d_to_pixel(X, Y, Z)
        self.assertAlmostEqual(u_proj, 320.0, delta=0.5)
        self.assertAlmostEqual(v_proj, 150.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
```

