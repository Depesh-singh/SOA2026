# वायुNetra (VayuNetra) — AI-Powered Counter-UAS & Airspace Defence C2 System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%20Accelerated-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8%20Object%20Detection-00FFFF.svg)](https://ultralytics.com)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

> **VayuNetra (वायुNetra)** is a military-grade, real-time Autonomous Counter-Unmanned Aerial System (C-UAS) and Airspace Defence Command & Control (C2) console. Built for low-altitude drone detection, multi-sensor fusion (Optical EO/IR + Radar Doppler), predictive 3D trajectory tracking, and Electronic Warfare (RF Jamming / ECCM frequency hopping) countermeasures.

---

## 🌟 Key Architecture & Capabilities

### 1. 🎯 Optical & Multi-Modal AI Detection
* **Dual YOLO Vision Pipeline**: Real-time multi-class drone detection and classification (`drone`, `quadcopter`, `fixed-wing`).
* **ByteTrack Multi-Object Tracking**: Continuous track association across camera frames with trajectory history.
* **FLIR / Night Vision Modes**: Dynamic HUD shaders including Optical, FLIR White-Hot, and NVG Green modes.

### 2. 📡 Multi-Sensor Fusion & State Estimation
* **Extended Kalman Filtering (EKF)**: Fuses camera optical angular velocity with mmWave radar Doppler velocity.
* **Dynamic Risk & Threat Evaluation**: Continuous scoring factoring proximity, closure rate, bearing vector, and AI classification confidence.
* **TEWA Master Air Picture**: Threat Evaluation & Target Assignment priority queuing with Time-To-Impact (TTI) calculations.

### 3. 📈 3D Trajectory Prediction
* **3D Isometric Vector Plotting**: Real-time rendered flight paths, actual tracked waypoints, and AI-extrapolated predictive trajectories.
* **Orthogonal Sub-Views**: Multi-perspective Lateral (X-Z) and Vertical (Y-Z) altitude profiles.

### 4. ⚡ Electronic Warfare & Countermeasures
* **Directional RF Soft-Kill Beam**: Jamming beam actuation across 2.4GHz / 5.8GHz channels.
* **Electronic Counter-Countermeasures (ECCM)**: Dynamic frequency agility hopping algorithms to secure C2 links during barrage jamming.
* **Gimbal Servo Fire Control**: Autonomous 2-axis Pan-Tilt servo tracking targeting detected hostiles.

---

## 🛠️ Quick Start & Execution

### Prerequisites
* Python 3.10+
* (Optional) CUDA-capable GPU with PyTorch for hardware acceleration

### Installation

```bash
# Clone the repository
git clone https://github.com/Depesh-singh/VayuNetra.git
cd VayuNetra

# Install dependencies
pip install fastapi uvicorn opencv-python ultralytics numpy torch torchvision websockets
```

### Launch VayuNetra C2 Server

```bash
# Start the backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open your browser and navigate to:
* **C2 Command Console**: [http://localhost:8000/](http://localhost:8000/)
* **Live Optical Feed**: [http://localhost:8000/api/video_feed](http://localhost:8000/api/video_feed)
* **REST API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Repository Structure

```
.
├── backend/                  # FastAPI C2 server, telemetry WebSocket, PID gimbal controller
│   ├── config.py             # System configuration parameters
│   ├── main.py               # Application entry point and streaming pipelines
│   └── gimbal/               # Gimbal pan/tilt PID control routines
├── smart_shield_ai/          # Core AI / ML Algorithms
│   ├── models/               # Pretrained YOLO & custom drone weights (.pt)
│   ├── sensor_fusion.py      # Radar + Optical velocity fusion
│   ├── state_estimator.py    # Kalman filter state estimation
│   ├── trajectory_predictor.py # Multi-step trajectory extrapolation
│   └── risk_engine.py        # Threat evaluation engine
├── frontend/                 # High-performance HTML5/Canvas C2 Console
│   ├── index.html            # Tactical Airspace command dashboard
│   ├── styles.css            # Cyber-tactical HUD styles and animations
│   ├── app.js                # WebSocket data binder and C2 coordinator
│   └── js/                   # Specialized canvas modules (Radar, HUD, Trajectory)
├── firmware/                 # Microcontroller (ESP32 / Arduino) drivers for Radar & Gimbal
├── database/                 # SQLite audit logger & event storage schema
└── tests/                    # System unit & integration tests
```

---

## 📄 License & Attribution
Developed for Strategic Airspace Defence and Counter-UAS Operations.
