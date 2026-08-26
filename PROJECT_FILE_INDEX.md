# PROJECT FILE INDEX: SMART-SHIELD v3.0

This index lists all 42 files included in `PROJECT_COMPLETE_SOURCE.md`.

---

## 1. Documentation & Architecture Specifications (4 files)
- `PRD_Product_Requirements_Document.md`
- `TRD_Technical_Requirements_Document.md`
- `ICD_Interface_Control_Document.md`
- `SYSTEM_ARCHITECTURE_AND_EXECUTION_PLAN.md`

## 2. Frontend Subsystem (7 files)
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `frontend/js/radar_scope.js`
- `frontend/js/optical_hud.js`
- `frontend/js/rf_spectrum.js`
- `frontend/js/gimbal_controls.js`

## 3. Backend Subsystem (24 files)
- `backend/requirements.txt`
- `backend/config.py`
- `backend/main.py`
- `backend/simulator.py`
- `backend/__init__.py`
- `backend/vision/__init__.py`
- `backend/vision/detector.py`
- `backend/vision/tracker.py`
- `backend/vision/velocity_estimator.py`
- `backend/vision/calibration.py`
- `backend/fusion/__init__.py`
- `backend/fusion/sensor_fusion.py`
- `backend/fusion/threat_matrix.py`
- `backend/fusion/trajectory_predictor.py`
- `backend/fusion/ekf.py`
- `backend/fusion/state_estimator.py`
- `backend/gimbal/__init__.py`
- `backend/gimbal/pid.py`
- `backend/gimbal/servo_control.py`
- `backend/hardware/__init__.py`
- `backend/hardware/esp32_serial.py`
- `backend/hardware/radar_interface.py`
- `backend/cyber_defense/__init__.py`
- `backend/cyber_defense/rf_monitor.py`

## 4. Database Architecture (3 files)
- `database/__init__.py`
- `database/schema.sql`
- `database/db_manager.py`

## 5. Microcontroller Firmware (2 files)
- `firmware/esp32_smart_shield/README.md`
- `firmware/esp32_smart_shield/esp32_smart_shield.ino`

## 6. Automated Testing Suite (2 files)
- `tests/__init__.py`
- `tests/test_system.py`

---

## Intentionally Excluded Files (3 items)
- `yolov8n.pt` (6.5 MB binary PyTorch model weights)
- `database/smart_shield.db` (Generated SQLite local database binary)
- `__pycache__/` (Python compiled bytecode directories)
