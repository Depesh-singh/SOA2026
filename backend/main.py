"""
SMART-SHIELD v3.0 Main FastAPI & Real-Time AI Hub
Integrates YOLO Detection, ByteTrack Tracking, Sensor Fusion, State Estimation,
Trajectory Prediction, Risk Engine, Alert Management, Event Logging, and Telemetry Broadcast.
"""

import asyncio
import json
import logging
import math
import os
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

# Serial library for ESP32 / Radar
try:
    import serial
    from serial import SerialException
except ImportError:
    serial = None
    SerialException = Exception

# Project modules
from .config import config
from .gimbal.pid import PIDGimbalController
from .cyber_defense.rf_monitor import CyberRFMonitor
from .simulator import ScenarioSimulator
from .fusion.trajectory_predictor import TrajectoryPredictor as FusionTrajectoryPredictor

# Core AI Engine (Preserved algorithms)
try:
    import smart_shield_ai
    from smart_shield_ai.sensor_fusion import fuse_velocity, calculate_camera_speed
    from smart_shield_ai.state_estimator import StateEstimator
    from smart_shield_ai.trajectory_predictor import TrajectoryPredictor
    from smart_shield_ai.risk_engine import RiskEngine, RiskResult
    from smart_shield_ai.alert_manager import AlertManager, AlertState
    from smart_shield_ai.event_logger import EventLogger
except (ImportError, ModuleNotFoundError):
    # Ensure package root is in sys.path
    pkg_root = str(Path(__file__).resolve().parent.parent)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    import smart_shield_ai
    from smart_shield_ai.sensor_fusion import fuse_velocity, calculate_camera_speed
    from smart_shield_ai.state_estimator import StateEstimator
    from smart_shield_ai.trajectory_predictor import TrajectoryPredictor
    from smart_shield_ai.risk_engine import RiskEngine, RiskResult
    from smart_shield_ai.alert_manager import AlertManager, AlertState
    from smart_shield_ai.event_logger import EventLogger

try:
    from database.db_manager import DatabaseManager
except (ImportError, ValueError):
    from ..database.db_manager import DatabaseManager

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SmartShield.Main")

app = FastAPI(title="VayuNetra (वायुNetra) v3.0 AI-C2 Backend", version="3.0.0")

# CORS middleware for open dashboard connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# BACKGROUND RADAR / ESP32 SERIAL READER
# Supports both CSV (range_m,velocity_mps) and JSON formats seamlessly
# ============================================================================

class RadarReader:
    """
    Background asynchronous radar/ESP32 serial reader.
    The reader never blocks the main video/AI loop. If disconnected,
    system continues operating with camera data only.
    """
    def __init__(self, port: str = "COM5", baudrate: int = 115200):
        self.port = port
        self.baudrate = int(baudrate)
        self.range_m: Optional[float] = None
        self.velocity_mps: Optional[float] = None
        self.raw_data: Dict[str, Any] = {}
        self.connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if not self.port:
            logger.info("[RADAR] No serial port configured. Radar disabled.")
            return
        if serial is None:
            logger.warning("[RADAR] pyserial is not installed. Radar disabled.")
            return
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._read_loop,
            name="SmartShield-RadarThread",
            daemon=True
        )
        self.thread.start()
        logger.info(f"[RADAR] Background reader started on {self.port} @ {self.baudrate}")

    def _read_loop(self):
        while self.running:
            try:
                with serial.Serial(self.port, self.baudrate, timeout=1.0) as ser:
                    self.connected = True
                    logger.info(f"[RADAR] Hardware Connected: {self.port} @ {self.baudrate}")

                    while self.running:
                        raw = ser.readline()
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue

                        # 1. Try parsing JSON format:
                        # {"timestamp": 123456, "temperature": 29.4, "rf_signal": 72, "radar_distance": 45.2, "radar_velocity": 8.3}
                        if line.startswith("{") and line.endswith("}"):
                            try:
                                data = json.loads(line)
                                self.raw_data = data
                                r = data.get("radar_distance", data.get("distance_m", data.get("range_m")))
                                v = data.get("radar_velocity", data.get("velocity_mps", data.get("speed_ms")))
                                if r is not None and np.isfinite(float(r)):
                                    self.range_m = float(r)
                                if v is not None and np.isfinite(float(v)):
                                    self.velocity_mps = float(v)
                                continue
                            except Exception:
                                pass

                        # 2. Try parsing CSV format: range_m,velocity_mps
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 2:
                            try:
                                r = float(parts[0])
                                v = float(parts[1])
                                if np.isfinite(r) and np.isfinite(v):
                                    self.range_m = r
                                    self.velocity_mps = v
                                    self.raw_data = {"range_m": r, "velocity_mps": v}
                            except ValueError:
                                continue

            except SerialException:
                self.connected = False
                if self.running:
                    time.sleep(2.0)
            except Exception as e:
                self.connected = False
                if self.running:
                    time.sleep(2.0)

        self.connected = False

    def get_latest(self) -> Tuple[Optional[float], Optional[float], bool, Dict[str, Any]]:
        return self.range_m, self.velocity_mps, self.connected, self.raw_data

    def stop(self):
        self.running = False
        self.connected = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)


# ============================================================================
# SPEED ESTIMATOR (AI ENGINE LOGIC)
# ============================================================================

class TrackSpeedEstimator:
    """Estimates camera image-space and metric velocity from tracked centroids."""
    def __init__(self, fps: float = 30.0, meters_per_pixel: Optional[float] = None, smoothing: int = 5):
        self.fps = max(float(fps), 1.0)
        self.mpp = meters_per_pixel
        self.history = defaultdict(lambda: deque(maxlen=max(int(smoothing), 2)))

    def update(self, track_id: int, center: Tuple[float, float]) -> Tuple[float, float]:
        """
        Returns:
            pixel_speed: speed in pixels/sec
            kmh: speed in km/h if calibration is provided, else 0.0
        """
        now = time.perf_counter()
        cx, cy = float(center[0]), float(center[1])
        history = self.history[track_id]
        history.append((cx, cy, now))

        if len(history) < 2:
            return 0.0, 0.0

        x0, y0, t0 = history[0]
        x1, y1, t1 = history[-1]

        dt = max(t1 - t0, 1e-6)
        pixel_distance = float(np.hypot(x1 - x0, y1 - y0))
        pixel_speed = pixel_distance / dt

        if self.mpp is None:
            return pixel_speed, 0.0

        mps = pixel_speed * float(self.mpp)
        kmh = mps * 3.6
        return pixel_speed, float(kmh)

    def remove_old(self, active_ids: List[int]):
        active = set(active_ids)
        for tid in list(self.history.keys()):
            if tid not in active:
                self.history.pop(tid, None)


# ============================================================================
# CAMERA STREAM MANAGER (THREADED CAPTURE)
# ============================================================================

class CameraStreamManager:
    """Threaded camera and video grabber to maintain smooth frame ingestion without blocking."""
    def __init__(self, source: Union[int, str] = 0):
        self.source = int(source) if str(source).isdigit() else str(source)
        self.source_name = f"Webcam (Index {self.source})" if isinstance(self.source, int) else os.path.basename(str(self.source))
        self.is_video_file = isinstance(self.source, str) and os.path.isfile(str(self.source))
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[np.ndarray] = None
        self.connected = False
        self.running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.fps = 30.0

    def set_source(self, new_source: Union[int, str], source_name: str = ""):
        with self.lock:
            self.source = int(new_source) if str(new_source).isdigit() else str(new_source)
            self.is_video_file = isinstance(self.source, str) and os.path.isfile(str(self.source))
            if source_name:
                self.source_name = source_name
            else:
                self.source_name = f"Webcam (Index {self.source})" if isinstance(self.source, int) else os.path.basename(str(self.source))
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.connected = False
        logger.info(f"[CAPTURE] Switched video source to: {self.source_name} (is_file={self.is_video_file})")

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, name="SmartShield-CamThread", daemon=True)
        self.thread.start()

    def _capture_loop(self):
        consecutive_fails = 0
        while self.running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    with self.lock:
                        curr_src = self.source
                        curr_is_file = self.is_video_file
                        curr_name = self.source_name

                    if curr_is_file:
                        logger.info(f"[VIDEO] Opening video file: {curr_src}")
                        self.cap = cv2.VideoCapture(curr_src)
                    elif isinstance(curr_src, int):
                        # Windows DirectShow for primary webcam
                        self.cap = cv2.VideoCapture(curr_src, cv2.CAP_DSHOW)
                        if not self.cap.isOpened():
                            self.cap = cv2.VideoCapture(curr_src)
                        if not self.cap.isOpened() and curr_src != 0:
                            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    else:
                        self.cap = cv2.VideoCapture(curr_src)

                    if self.cap.isOpened():
                        if not curr_is_file:
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        src_fps = self.cap.get(cv2.CAP_PROP_FPS)
                        if src_fps and src_fps > 1.0:
                            self.fps = src_fps
                        self.connected = True
                        logger.info(f"[CAPTURE] Source {curr_name} opened successfully (FPS: {self.fps}).")
                    else:
                        self.connected = False
                        time.sleep(2.0)
                        continue

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if self.is_video_file:
                        # Auto-loop video file for continuous tracking demonstration
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        time.sleep(0.05)
                        continue
                    else:
                        consecutive_fails += 1
                        if consecutive_fails >= 10:
                            self.connected = False
                            if self.cap:
                                self.cap.release()
                            self.cap = None
                            time.sleep(1.0)
                        else:
                            time.sleep(0.03)
                        continue

                consecutive_fails = 0
                self.connected = True
                with self.lock:
                    self.current_frame = frame.copy()

                time.sleep(1.0 / max(self.fps, 10.0))

            except Exception as e:
                self.connected = False
                logger.error(f"[CAPTURE] Error in capture loop: {e}")
                time.sleep(1.0)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self.lock:
            if self.current_frame is not None:
                return True, self.current_frame.copy()
        return False, None

    def stop(self):
        self.running = False
        self.connected = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            self.cap = None


# ============================================================================
# SYSTEM INITIALIZATION & STATE
# ============================================================================

db = DatabaseManager(config.db_dsn)
radar_reader = RadarReader(
    port=config.radar.serial_port,
    baudrate=config.radar.baud_rate
)
cam_stream = CameraStreamManager(source=config.ai.camera_source)
speed_estimator = TrackSpeedEstimator(
    fps=config.ai.camera_fps,
    meters_per_pixel=config.ai.meters_per_pixel,
    smoothing=config.ai.speed_smoothing
)

# Core AI Engine Module Instances
risk_engine = RiskEngine(
    low_confidence_threshold=config.ai.low_confidence_threshold,
    medium_threshold=config.ai.medium_risk_threshold,
    high_threshold=config.ai.high_risk_threshold
)
alert_manager = AlertManager(hold_seconds=3.0)
event_logger = EventLogger(log_dir=config.ai.log_dir, filename="events.jsonl")
trajectory_predictor = TrajectoryPredictor(
    horizon=config.ai.prediction_horizon,
    step=config.ai.prediction_step
)
fusion_trajectory_predictor = FusionTrajectoryPredictor(
    default_horizon_seconds=config.ai.prediction_horizon,
    step_dt=config.ai.prediction_step
)
state_estimators: Dict[int, StateEstimator] = {}

# Other controllers
gimbal_ctrl = PIDGimbalController()
rf_monitor = CyberRFMonitor()
simulator = ScenarioSimulator()

# Global YOLO model holder
yolo_model: Optional[YOLO] = None
secondary_yolo_model: Optional[YOLO] = None

# Global runtime state for MJPEG video feed and WebSockets
latest_annotated_frame: Optional[np.ndarray] = None
latest_telemetry: Dict[str, Any] = {}
latest_targets: List[Dict[str, Any]] = []
latest_primary_target: Optional[Dict[str, Any]] = None
connected_clients: List[WebSocket] = []
frame_lock = threading.Lock()


# ============================================================================
# FASTAPI LIFECYCLE HANDLERS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    global yolo_model, secondary_yolo_model
    logger.info("Initializing SMART-SHIELD v3.0 Core Services...")

    # 1. Initialize Database
    try:
        await db.initialize()
    except Exception as e:
        logger.warning(f"Database initialization fallback: {e}")

    # 2. Select Device (GPU NVIDIA CUDA if available)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    logger.info(f"[ACCELERATION] Using Device: {device} ({device_name})")

    # Load YOLO Model ONCE at startup
    model_path = Path(config.ai.model_path).resolve()
    if not model_path.is_file():
        alt_path = Path(__file__).resolve().parent.parent / "smart_shield_ai" / "models" / "best.pt"
        if alt_path.is_file():
            model_path = alt_path
        else:
            logger.warning(f"Model file not found at {model_path}. Checking default YOLO weights...")
            model_path = Path("best.pt") if Path("best.pt").is_file() else Path("yolo11n.pt")

    logger.info(f"Loading Primary YOLO Model from: {model_path}")
    try:
        yolo_model = YOLO(str(model_path)).to(device)
        logger.info(f"Primary YOLO Model loaded on {device}. Classes: {yolo_model.names}")
    except Exception as e:
        logger.error(f"Failed to load YOLO model from {model_path}: {e}")
        try:
            yolo_model = YOLO("yolo11n.pt").to(device)
        except Exception as e2:
            logger.critical(f"Critical: Could not load any YOLO model: {e2}")

    # Load Secondary Universal Drone Model (Internet Pretrained)
    sec_path = Path(__file__).resolve().parent.parent / "smart_shield_ai" / "models" / "drone_yolo_v1.pt"
    if sec_path.is_file():
        try:
            secondary_yolo_model = YOLO(str(sec_path)).to(device)
            logger.info(f"Secondary Universal Drone Model loaded on {device}. Classes: {secondary_yolo_model.names}")
        except Exception as e_sec:
            logger.warning(f"Could not load secondary model: {e_sec}")
            secondary_yolo_model = None
    else:
        secondary_yolo_model = None

    # 3. Start Camera Capture Thread
    cam_stream.start()

    # 4. Start AI Dedicated GPU Worker Thread
    ai_worker.start()

    # 5. Start Radar Background Reader
    if config.radar.enabled or config.radar.serial_port:
        radar_reader.start()

    # 6. Start Real-Time Fast Telemetry Broadcast Loop
    asyncio.create_task(fusion_orchestration_loop())
    logger.info("SMART-SHIELD v3.0 Real-Time AI Pipeline Started.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SMART-SHIELD services...")
    ai_worker.stop()
    cam_stream.stop()
    radar_reader.stop()
    try:
        await db.close()
    except Exception:
        pass


# ============================================================================
# WEBSOCKET TELEMETRY BROADCAST
# ============================================================================

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(connected_clients)}")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("cmd") == "TOGGLE_AUTOTRACK":
                    gimbal_ctrl.auto_track_enabled = msg.get("enabled", True)
                elif msg.get("cmd") == "MANUAL_GIMBAL":
                    gimbal_ctrl.set_manual_angles(msg.get("pan", 90.0), msg.get("tilt", 45.0))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info("WebSocket client disconnected.")


async def broadcast_telemetry(payload: Dict[str, Any]):
    if not connected_clients:
        return
    msg = json.dumps(payload)
    for ws in list(connected_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            if ws in connected_clients:
                connected_clients.remove(ws)


# ============================================================================
# HUD DRAWING UTILITY
# ============================================================================

def draw_dashboard_hud(
    frame: np.ndarray,
    fps: float,
    active_tracks: int,
    radar_speed: Optional[float] = None,
    radar_range: Optional[float] = None,
    radar_connected: bool = False,
    high_threat: bool = False
):
    """Draws the tactical military HUD overlay across the video frame."""
    h, w = frame.shape[:2]

    # Top Status Bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (460, 130), (10, 15, 25), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    cv2.rectangle(frame, (10, 10), (460, 130), (0, 240, 255) if not high_threat else (0, 0, 255), 1)

    cv2.putText(frame, "SMART SHIELD — AI C2 DEFENCE", (22, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 240, 255), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}   TARGETS: {active_tracks:02d}", (22, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

    radar_status_str = "CONNECTED" if radar_connected else "STANDBY / OFFLINE"
    status_color = (0, 255, 100) if radar_connected else (100, 180, 255)
    cv2.putText(frame, f"RADAR: {radar_status_str}", (22, 91), cv2.FONT_HERSHEY_SIMPLEX, 0.54, status_color, 2)

    r_spd_txt = f"R-VEL: {radar_speed:.1f} m/s" if radar_speed is not None else "R-VEL: ---"
    r_rng_txt = f"R-RNG: {radar_range:.1f} m" if radar_range is not None else "R-RNG: ---"
    cv2.putText(frame, f"{r_spd_txt}   {r_rng_txt}", (22, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1)

    # Crosshairs & Boresight
    cx, cy = w // 2, h // 2
    cv2.drawMarker(frame, (cx, cy), (0, 240, 255), markerType=cv2.MARKER_CROSS, markerSize=20, thickness=1)


# ============================================================================
# DEDICATED GPU-ACCELERATED AI PIPELINE WORKER THREAD
# ============================================================================

class AIPipelineWorker:
    """Dedicated background worker thread for GPU-accelerated YOLO detection & AI Sensor Fusion."""
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.live_fps = 30.0
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, name="SmartShield-AIWorker", daemon=True)
        self.thread.start()
        logger.info(f"[AI WORKER] GPU AI Worker Thread started on device {self.device}.")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _worker_loop(self):
        global latest_annotated_frame, latest_telemetry, latest_targets, latest_primary_target, state_estimators
        prev_time = time.perf_counter()

        while self.running:
            try:
                loop_start = time.perf_counter()

                # 1. Acquire Camera Frame
                has_frame, frame = cam_stream.get_frame()
                radar_range, radar_speed, radar_connected, raw_radar_dict = radar_reader.get_latest()

                evaluated_targets: List[Dict[str, Any]] = []
                active_track_ids: List[int] = []

                # ================================================================
                # CASE A: LIVE CAMERA / VIDEO AVAILABLE -> RUN FULL GPU AI PIPELINE
                # ================================================================
                if has_frame and frame is not None:
                    annotated_frame = frame.copy()
                    h, w = frame.shape[:2]

                    # Run GPU YOLO Inference
                    if yolo_model is not None:
                        try:
                            results = yolo_model.predict(
                                frame,
                                device=self.device,
                                conf=config.ai.yolo_confidence,
                                iou=config.ai.yolo_iou,
                                imgsz=config.ai.yolo_imgsz,
                                verbose=False
                            )
                        except Exception:
                            results = yolo_model.predict(
                                frame,
                                conf=config.ai.yolo_confidence,
                                iou=config.ai.yolo_iou,
                                imgsz=config.ai.yolo_imgsz,
                                verbose=False
                            )

                        # If primary model didn't detect, fallback to secondary universal model
                        if (results[0].boxes is None or len(results[0].boxes) == 0) and secondary_yolo_model is not None:
                            try:
                                sec_results = secondary_yolo_model.predict(
                                    frame,
                                    device=self.device,
                                    conf=config.ai.yolo_confidence,
                                    iou=config.ai.yolo_iou,
                                    imgsz=config.ai.yolo_imgsz,
                                    verbose=False
                                )
                                if sec_results[0].boxes is not None and len(sec_results[0].boxes) > 0:
                                    results = sec_results
                            except Exception:
                                pass

                        result = results[0]

                        if result.boxes is not None and len(result.boxes) > 0:
                            boxes = result.boxes.xyxy.cpu().numpy()
                            confs = result.boxes.conf.cpu().numpy()
                            ids_tensor = result.boxes.id
                            cls_tensor = result.boxes.cls

                            if ids_tensor is not None:
                                track_ids = ids_tensor.int().cpu().tolist()
                            else:
                                track_ids = list(range(1, len(boxes) + 1))

                            if cls_tensor is not None and result.names:
                                class_names = [result.names.get(int(c), "drone") for c in cls_tensor.cpu().tolist()]
                            else:
                                class_names = ["drone"] * len(boxes)

                            for box, score, tid, cls_name in zip(boxes, confs, track_ids, class_names):
                                x1, y1, x2, y2 = map(int, box)
                                cx = (x1 + x2) / 2.0
                                cy = (y1 + y2) / 2.0
                                active_track_ids.append(tid)

                                # 1. Camera Speed Estimation
                                pixel_speed, kmh = speed_estimator.update(tid, (cx, cy))
                                cam_speed_mps = (kmh / 3.6) if kmh > 0 else (pixel_speed * 0.02)

                                # 2. Sensor Fusion (fuse_velocity from smart_shield_ai)
                                fused_vel_res = fuse_velocity(
                                    radar_velocity=radar_speed,
                                    radar_confidence=0.85 if radar_connected else 0.0,
                                    camera_velocity=cam_speed_mps,
                                    camera_confidence=float(score),
                                    disagreement_threshold=10.0
                                )
                                fused_spd = fused_vel_res.get("fused_velocity", cam_speed_mps)

                                # 3. Kalman Filter State Estimation (smart_shield_ai.state_estimator)
                                if tid not in state_estimators:
                                    est = StateEstimator(dt=1.0 / max(config.ai.camera_fps, 10.0))
                                    est.initialize(cx, cy)
                                    state_estimators[tid] = est
                                estimator = state_estimators[tid]
                                estimator.predict()
                                estimator.update_position(cx, cy)
                                state_dict = estimator.get_state()

                                # 3b. Tactical 3D Metric Coordinates
                                target_range = radar_range if (radar_range is not None and radar_range > 0) else max(10.0, 200.0 - (max(x2 - x1, y2 - y1) * 0.8))
                                az_deg = ((cx - (w / 2.0)) / (w / 2.0)) * 45.0
                                dist_m = target_range
                                x_m = dist_m * math.sin(math.radians(az_deg))
                                y_m = dist_m * math.cos(math.radians(az_deg))
                                z_m = 15.0

                                # 4. Trajectory Prediction (smart_shield_ai.trajectory_predictor)
                                traj_points = trajectory_predictor.predict_from_state(state_dict)

                                # 4b. 3D Metric Future Trajectory & Intercept Prediction (0.0s -> 3.0s)
                                vx_ms_val = round(fused_spd * math.sin(math.radians(az_deg)), 2)
                                vy_ms_val = round(-fused_spd * math.cos(math.radians(az_deg)), 2)
                                vz_ms_val = 0.0

                                future_waypoints_3d = fusion_trajectory_predictor.predict_future_trajectory(
                                    x_m=x_m, y_m=y_m, z_m=z_m,
                                    vx_ms=vx_ms_val, vy_ms=vy_ms_val, vz_ms=vz_ms_val,
                                    horizon_s=3.0,
                                    base_uncertainty_m=2.0
                                )
                                cpa_metrics = fusion_trajectory_predictor.calculate_closest_point_of_approach(
                                    x_m=x_m, y_m=y_m, z_m=z_m,
                                    vx_ms=vx_ms_val, vy_ms=vy_ms_val, vz_ms=vz_ms_val
                                )
                                zone_analysis = fusion_trajectory_predictor.check_protected_zone_approach(
                                    waypoints=future_waypoints_3d,
                                    zone_radius_m=50.0
                                )
                                end_pt = future_waypoints_3d[-1] if future_waypoints_3d else {
                                    "x_m": x_m, "y_m": y_m, "z_m": z_m, "t_sec": 3.0, "uncertainty_m": 2.0
                                }

                                # 5. Risk Assessment (smart_shield_ai.risk_engine)
                                risk_result = risk_engine.assess(
                                    detection_confidence=float(score),
                                    speed_mps=float(fused_spd),
                                    radar_speed_mps=radar_speed,
                                    trajectory_risk=0.5,
                                    range_m=float(target_range)
                                )

                                # 6. Alert Manager (smart_shield_ai.alert_manager)
                                alert_state = alert_manager.update(
                                    level=risk_result.level,
                                    score=risk_result.score,
                                    reasons=risk_result.reasons
                                )

                                # 7. Event Logger (smart_shield_ai.event_logger)
                                event_logger.log_detection(
                                    track_id=tid,
                                    confidence=float(score),
                                    speed_mps=float(fused_spd),
                                    risk={"score": float(risk_result.score), "level": str(risk_result.level)}
                                )

                                # Assemble Target Payload
                                target_info = {
                                    "id": f"TRK-{tid:03d}",
                                    "track_id": tid,
                                    "callsign": f"{cls_name.upper()} (TRK-{tid})",
                                    "classification": cls_name.capitalize(),
                                    "confidence": round(float(score), 2),
                                    "bbox": [x1, y1, x2, y2],
                                    "centroid": [round(cx, 1), round(cy, 1)],
                                    "center_u": cx,
                                    "center_v": cy,
                                    "x_m": round(x_m, 1),
                                    "y_m": round(y_m, 1),
                                    "z_m": round(z_m, 1),
                                    "vx_ms": vx_ms_val,
                                    "vy_ms": vy_ms_val,
                                    "vz_ms": vz_ms_val,
                                    "distance_m": round(dist_m, 1),
                                    "azimuth_deg": round(az_deg, 1),
                                    "speed_ms": round(fused_spd, 1),
                                    "speed_kmh": round(fused_spd * 3.6, 1),
                                    "closure_rate_ms": round(-fused_spd, 1),
                                    "camera_speed_px_s": round(pixel_speed, 1),
                                    "radar_speed_mps": radar_speed,
                                    "radar_range_m": radar_range,
                                    "fused_velocity": fused_vel_res,
                                    "trajectory_prediction": traj_points,
                                    "future_waypoints": future_waypoints_3d,
                                    "predicted_endpoint_3s": {
                                        "x_m": end_pt["x_m"],
                                        "y_m": end_pt["y_m"],
                                        "z_m": end_pt["z_m"],
                                        "t_sec": end_pt["t_sec"]
                                    },
                                    "prediction_horizon": 3.0,
                                    "cpa": cpa_metrics,
                                    "protected_zone": zone_analysis,
                                    "uncertainty_m": end_pt.get("uncertainty_m", 2.0),
                                    "threat_score": int(risk_result.score),
                                    "threat_level": risk_result.level,
                                    "threat_category": "CRITICAL" if risk_result.level == "HIGH" else ("ELEVATED" if risk_result.level == "MEDIUM" else "NOMINAL"),
                                    "threat_reasons": risk_result.reasons,
                                    "alert_state": {
                                        "level": alert_state.level,
                                        "score": alert_state.score,
                                        "message": alert_state.message
                                    }
                                }
                                evaluated_targets.append(target_info)

                                # Visual Annotations on Frame
                                box_color = (0, 0, 255) if risk_result.level == "HIGH" else ((0, 180, 255) if risk_result.level == "MEDIUM" else (0, 255, 100))
                                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
                                cv2.circle(annotated_frame, (int(cx), int(cy)), 4, (0, 0, 255), -1)

                                # Draw Trajectory Prediction Line
                                for i in range(len(traj_points) - 1):
                                    pt1 = (int(traj_points[i]["x"]), int(traj_points[i]["y"]))
                                    pt2 = (int(traj_points[i+1]["x"]), int(traj_points[i+1]["y"]))
                                    cv2.line(annotated_frame, pt1, pt2, (0, 240, 255), 2)

                                label_top = f"{cls_name.upper()} | Conf: {float(score):.2f}"
                                label_sub = f"Spd: {fused_spd:.1f} m/s | Risk: {risk_result.score}"
                                cv2.putText(annotated_frame, label_top, (x1, max(22, y1 - 22)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, box_color, 2)
                                cv2.putText(annotated_frame, label_sub, (x1, max(38, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)

                    speed_estimator.remove_old(active_track_ids)
                    for tid in list(state_estimators.keys()):
                        if tid not in active_track_ids:
                            state_estimators.pop(tid, None)

                # ================================================================
                # CASE B: CAMERA OFFLINE -> FALLBACK TO SIMULATION KINEMATICS
                # ================================================================
                else:
                    sim_targets = simulator.update_simulation()
                    annotated_frame = np.zeros((config.ai.camera_height, config.ai.camera_width, 3), dtype=np.uint8)

                    for t in sim_targets:
                        tid_num = int(t["id"].split("-")[-1]) if "-" in t["id"] else 1
                        active_track_ids.append(tid_num)

                        r_risk = risk_engine.assess(
                            detection_confidence=t.get("optical_confidence", 0.90),
                            speed_mps=t.get("speed_ms", 15.0),
                            radar_speed_mps=t.get("vy_ms", -10.0),
                            trajectory_risk=0.6,
                            range_m=t.get("distance_m", 60.0)
                        )

                        future_waypoints_3d = fusion_trajectory_predictor.predict_future_trajectory(
                            x_m=t["x_m"], y_m=t["y_m"], z_m=t["z_m"],
                            vx_ms=t["vx_ms"], vy_ms=t["vy_ms"], vz_ms=0.0,
                            horizon_s=3.0,
                            base_uncertainty_m=1.5
                        )
                        cpa_metrics = fusion_trajectory_predictor.calculate_closest_point_of_approach(
                            x_m=t["x_m"], y_m=t["y_m"], z_m=t["z_m"],
                            vx_ms=t["vx_ms"], vy_ms=t["vy_ms"], vz_ms=0.0
                        )
                        zone_analysis = fusion_trajectory_predictor.check_protected_zone_approach(
                            waypoints=future_waypoints_3d,
                            zone_radius_m=50.0
                        )
                        end_pt = future_waypoints_3d[-1] if future_waypoints_3d else {
                            "x_m": t["x_m"], "y_m": t["y_m"], "z_m": t["z_m"], "t_sec": 3.0, "uncertainty_m": 1.5
                        }

                        t_info = {
                            "id": t["id"],
                            "track_id": tid_num,
                            "callsign": f"HOSTILE ({t['id']})" if r_risk.level == "HIGH" else f"SUSPECT ({t['id']})",
                            "classification": t.get("classification", "Drone"),
                            "confidence": t.get("optical_confidence", 0.90),
                            "x_m": t["x_m"],
                            "y_m": t["y_m"],
                            "z_m": t["z_m"],
                            "vx_ms": t["vx_ms"],
                            "vy_ms": t["vy_ms"],
                            "vz_ms": 0.0,
                            "distance_m": t["distance_m"],
                            "azimuth_deg": t["azimuth_deg"],
                            "speed_ms": t["speed_ms"],
                            "closure_rate_ms": t["vy_ms"],
                            "camera_speed_px_s": 0.0,
                            "radar_speed_mps": t.get("vy_ms"),
                            "radar_range_m": t.get("distance_m"),
                            "fused_velocity": {"fused_velocity": t["speed_ms"], "source": "simulated"},
                            "future_waypoints": future_waypoints_3d,
                            "predicted_endpoint_3s": {
                                "x_m": end_pt["x_m"],
                                "y_m": end_pt["y_m"],
                                "z_m": end_pt["z_m"],
                                "t_sec": end_pt["t_sec"]
                            },
                            "prediction_horizon": 3.0,
                            "cpa": cpa_metrics,
                            "protected_zone": zone_analysis,
                            "uncertainty_m": end_pt.get("uncertainty_m", 1.5),
                            "threat_score": int(r_risk.score),
                            "threat_level": r_risk.level,
                            "threat_category": "CRITICAL" if r_risk.level == "HIGH" else ("ELEVATED" if r_risk.level == "MEDIUM" else "NOMINAL"),
                            "threat_reasons": r_risk.reasons,
                            "alert_state": {"level": r_risk.level, "score": r_risk.score, "changed": False}
                        }
                        evaluated_targets.append(t_info)

                    cv2.putText(annotated_frame, "CAMERA INPUT: STANDBY / SIMULATION ACTIVE", (30, config.ai.camera_height // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 180, 255), 2)

                # Sort targets by threat score descending
                evaluated_targets.sort(key=lambda x: x.get("threat_score", 0), reverse=True)
                primary_target = evaluated_targets[0] if evaluated_targets else None
                has_high_threat = any(t.get("threat_level") == "HIGH" for t in evaluated_targets)

                # Calculate True Inference FPS
                now_perf = time.perf_counter()
                self.live_fps = 1.0 / max(now_perf - prev_time, 1e-6)
                prev_time = now_perf

                # Draw tactical HUD status overlay on frame
                draw_dashboard_hud(
                    annotated_frame,
                    fps=self.live_fps,
                    active_tracks=len(evaluated_targets),
                    radar_speed=radar_speed,
                    radar_range=radar_range,
                    radar_connected=radar_connected,
                    high_threat=has_high_threat
                )

                # Update latest frame cache for MJPEG streamer atomically
                with frame_lock:
                    latest_annotated_frame = annotated_frame.copy()

                # Gimbal Pan/Tilt Tracking
                pan_deg, tilt_deg = gimbal_ctrl.pan_angle, gimbal_ctrl.tilt_angle
                if primary_target and gimbal_ctrl.auto_track_enabled:
                    if "center_u" in primary_target and "center_v" in primary_target:
                        pan_deg, tilt_deg = gimbal_ctrl.compute_tracking_angles(
                            target_center_u=primary_target["center_u"],
                            target_center_v=primary_target["center_v"],
                            frame_width=config.ai.camera_width,
                            frame_height=config.ai.camera_height
                        )
                    else:
                        target_pan = 90.0 + primary_target["azimuth_deg"]
                        gimbal_ctrl.set_manual_angles(target_pan, 45.0)
                        pan_deg, tilt_deg = gimbal_ctrl.pan_angle, gimbal_ctrl.tilt_angle

                # Cyber RF Spectrum Status
                rf_status = rf_monitor.get_spectrum_scan()

                # Assemble Full Standard Telemetry Payload
                telemetry_payload = {
                    "timestamp": time.time(),
                    "system_status": {
                        "camera_connected": has_frame,
                        "radar_connected": radar_connected,
                        "ai_engine_running": True,
                        "fps": round(self.live_fps, 1),
                        "device": self.device,
                        "mode": "LIVE_AI_ENGINE" if has_frame else "STANDALONE_SIM"
                    },
                    "targets": evaluated_targets,
                    "primary_target": primary_target,
                    "gimbal": {
                        "pan_deg": pan_deg,
                        "tilt_deg": tilt_deg,
                        "auto_track": gimbal_ctrl.auto_track_enabled
                    },
                    "cyber_rf": rf_status,
                    "sensor_data": {
                        "radar_raw": raw_radar_dict,
                        "radar_connected": radar_connected,
                        "radar_port": config.radar.serial_port
                    },
                    "system": {
                        "battery_voltage": 12.6,
                        "status": "ARMED",
                        "high_threat_active": has_high_threat,
                        "buzzer_active": has_high_threat
                    }
                }

                latest_telemetry = telemetry_payload
                latest_targets = evaluated_targets
                latest_primary_target = primary_target

                # Pace thread to maintain smooth target FPS
                elapsed = time.perf_counter() - loop_start
                sleep_time = max(0.001, (1.0 / 30.0) - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"[AI PIPELINE] Worker thread exception: {e}", exc_info=True)
                time.sleep(0.05)


ai_worker = AIPipelineWorker()


async def fusion_orchestration_loop():
    """Lightweight broadcast loop running at ~30 FPS without blocking the server."""
    while True:
        try:
            if latest_telemetry:
                await broadcast_telemetry(latest_telemetry)
            await asyncio.sleep(1.0 / 30.0)
        except Exception:
            await asyncio.sleep(0.1)


# ============================================================================
# MJPEG VIDEO STREAM & REST ENDPOINTS
# ============================================================================

async def generate_mjpeg_stream():
    """Async generator streaming compressed JPEG frames to browser."""
    while True:
        frame_to_encode = None
        with frame_lock:
            if latest_annotated_frame is not None:
                frame_to_encode = latest_annotated_frame.copy()

        if frame_to_encode is not None:
            ret, jpeg = cv2.imencode(".jpg", frame_to_encode, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                frame_bytes = jpeg.tobytes()
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        await asyncio.sleep(0.033) # ~30 FPS


@app.get("/api/video_feed")
async def get_video_feed():
    """MJPEG live camera reconnaissance stream with YOLO bounding boxes and HUD overlay."""
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
        "camera_connected": cam_stream.connected,
        "radar_connected": radar_reader.connected,
        "active_targets": len(latest_targets),
        "primary_target": latest_primary_target["id"] if latest_primary_target else None
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
    return {"status": "SUCCESS", "hop_event": hop_event}


@app.get("/api/telemetry/replay")
async def get_telemetry_replay(limit: int = 150):
    try:
        history = db.get_historical_telemetry(limit=limit)
        return {"status": "SUCCESS", "count": len(history), "telemetry": history}
    except Exception:
        return {"status": "SUCCESS", "count": len(latest_targets), "telemetry": latest_targets}


@app.get("/api/logs/export/csv")
async def export_telemetry_csv():
    try:
        csv_data = db.export_csv_report()
    except Exception:
        csv_data = "timestamp,target_id,distance_m,speed_ms,threat_score,threat_level\n"
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smart_shield_mission_report.csv"}
    )


@app.get("/api/logs/cyber")
async def get_cyber_logs():
    return rf_monitor.hop_history


# ============================================================================
# VIDEO UPLOAD & SOURCE SWITCHING ENDPOINTS
# ============================================================================

@app.post("/api/video/upload")
async def upload_drone_video(file: UploadFile = File(...)):
    """Accepts uploaded drone flight video and switches AI ingestion to it."""
    try:
        upload_dir = Path(__file__).resolve().parent.parent / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = int(time.time())
        clean_filename = f"drone_{timestamp_str}_{file.filename}"
        save_path = upload_dir / clean_filename

        with open(save_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        cam_stream.set_source(str(save_path), source_name=f"Video: {file.filename}")
        logger.info(f"[VIDEO UPLOAD] Saved and activated video: {save_path}")

        return {
            "status": "SUCCESS",
            "message": f"Drone flight video '{file.filename}' uploaded and active.",
            "source_type": "VIDEO_FILE",
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"[VIDEO UPLOAD] Upload error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})


@app.post("/api/video/switch_source")
async def switch_video_source(req: Dict[str, Any]):
    """Switches active video source between USB Webcam and uploaded video."""
    src = req.get("source", "usb")
    if src in ("usb", "webcam", "0", "internal"):
        cam_stream.set_source(0, source_name="Webcam (Index 0)")
        return {"status": "SUCCESS", "source_type": "USB_CAMERA", "source_name": "Webcam (Index 0)"}
    elif src in ("external", "1"):
        cam_stream.set_source(1, source_name="External Camera (Index 1)")
        return {"status": "SUCCESS", "source_type": "EXTERNAL_CAMERA", "source_name": "External Camera (Index 1)"}
    elif os.path.isfile(str(src)):
        cam_stream.set_source(str(src), source_name=f"Video: {os.path.basename(str(src))}")
        return {"status": "SUCCESS", "source_type": "VIDEO_FILE", "source_name": os.path.basename(str(src))}
    else:
        return JSONResponse(status_code=400, content={"status": "ERROR", "message": f"Invalid source: {src}"})


@app.get("/api/video/source")
async def get_video_source():
    """Returns the current active video input stream metadata."""
    return {
        "source_name": cam_stream.source_name,
        "is_video_file": cam_stream.is_video_file,
        "connected": cam_stream.connected,
        "fps": round(cam_stream.fps, 1)
    }


# Mount Frontend Static Files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
