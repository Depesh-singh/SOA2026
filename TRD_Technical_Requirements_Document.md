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
