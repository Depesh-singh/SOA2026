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
