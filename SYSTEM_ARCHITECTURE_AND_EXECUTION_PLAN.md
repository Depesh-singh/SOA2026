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
