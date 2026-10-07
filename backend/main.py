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
import queue

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
# BIDIRECTIONAL ESP32 SERIAL BRIDGE
# Reads radar/sensor telemetry AND sends servo tracking commands over COM5
# ============================================================================

class ESP32SerialBridge:
    """
    Bidirectional serial bridge to ESP32 over a single COM port.
    - READS: Radar telemetry, servo acknowledgments, sensor data (JSON or CSV)
    - WRITES: Servo pan angle commands, threat level, buzzer control
    Thread-safe command queue ensures non-blocking writes from the main loop.
    """
    def __init__(self, port: str = "COM5", baudrate: int = 115200):
        self.port = port
        self.baudrate = int(baudrate)
        # Radar telemetry state
        self.range_m: Optional[float] = None
        self.velocity_mps: Optional[float] = None
        self.raw_data: Dict[str, Any] = {}
        self.connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        # Servo tracking state
        self.servo_pan: float = 90.0
        self.servo_tilt: float = 90.0
        self.servo_status: str = "IDLE"
        self.servo_connected = False
        # Thread-safe command queue (outbound to ESP32)
        self._cmd_queue: "queue.Queue[str]" = queue.Queue(maxsize=20)
        self._last_cmd_time: float = 0.0

    def start(self):
        if not self.port:
            logger.info("[ESP32] No serial port configured. ESP32 bridge disabled.")
            return
        if serial is None:
            logger.warning("[ESP32] pyserial is not installed. ESP32 bridge disabled.")
            return
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._bridge_loop,
            name="SmartShield-ESP32Bridge",
            daemon=True
        )
        self.thread.start()
        logger.info(f"[ESP32] Bidirectional bridge started on {self.port} @ {self.baudrate}")

    def _bridge_loop(self):
        """Main serial loop: interleaves reading telemetry and writing servo commands with auto-reconnect."""
        while self.running:
            ser = None
            try:
                ser = serial.Serial(self.port, self.baudrate, timeout=0.08, write_timeout=0.2)
                self.connected = True
                self.servo_connected = True
                logger.info(f"[ESP32] Hardware Connected: {self.port} @ {self.baudrate}")

                while self.running:
                    # --- WRITE: Send latest queued servo command (non-blocking) ---
                    try:
                        latest_cmd = None
                        while not self._cmd_queue.empty():
                            latest_cmd = self._cmd_queue.get_nowait()
                        if latest_cmd is not None:
                            ser.write(latest_cmd.encode('utf-8'))
                    except queue.Empty:
                        pass
                    except Exception as e_write:
                        logger.error(f"[ESP32] Serial write error, reconnecting: {e_write}")
                        break  # Exit inner loop to re-open serial handle cleanly

                    # --- READ: Process incoming telemetry lines ---
                    try:
                        if ser.in_waiting > 0:
                            raw = ser.readline()
                            if raw:
                                line = raw.decode("utf-8", errors="ignore").strip()
                                if line:
                                    self._parse_incoming(line)
                    except Exception as e_read:
                        if not self.running:
                            break

                    # Small sleep to prevent CPU spin
                    time.sleep(0.01)

            except Exception as e:
                self.connected = False
                self.servo_connected = False
                if self.running:
                    logger.warning(f"[ESP32] Serial link offline ({e}). Reconnecting in 2.0s...")
                    time.sleep(2.0)
            finally:
                if ser is not None:
                    try:
                        ser.close()
                    except Exception:
                        pass

        self.connected = False
        self.servo_connected = False

    def _parse_incoming(self, line: str):
        """Parse incoming JSON or CSV telemetry from ESP32."""
        # 1. Try JSON format
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                self.raw_data = data

                # Servo acknowledgment
                if "servo_pan" in data:
                    self.servo_pan = float(data["servo_pan"])
                if "servo_tilt" in data or "tilt" in data:
                    self.servo_tilt = float(data.get("servo_tilt", data.get("tilt", 90.0)))
                if "status" in data:
                    self.servo_status = str(data["status"])

                # Radar telemetry
                r = data.get("radar_distance", data.get("distance_m", data.get("range_m")))
                v = data.get("radar_velocity", data.get("velocity_mps", data.get("speed_ms")))
                if r is not None and np.isfinite(float(r)):
                    self.range_m = float(r)
                if v is not None and np.isfinite(float(v)):
                    self.velocity_mps = float(v)
                return
            except Exception:
                pass

        # 2. Try CSV format: range_m,velocity_mps
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
                pass

    def send_servo_command(self, pan_deg: float, tilt_deg: Optional[float] = None, threat_level: str = "LOW", force: bool = False, tracking: bool = True):
        """Queue a dual-axis servo positioning command to ESP32 (non-blocking, rate-limited to ~15Hz)."""
        now = time.time()
        min_interval = 1.0 / max(1, config.gimbal.servo_update_hz)
        if not force and (now - self._last_cmd_time < min_interval):
            return  # Rate limit

        pan_deg = max(0.0, min(180.0, pan_deg))
        cmd_dict = {
            "pan": round(pan_deg, 1),
            "threat": threat_level,
            "tracking": bool(tracking)
        }
        if tilt_deg is not None:
            cmd_dict["tilt"] = round(max(65.0, min(115.0, float(tilt_deg))), 1)
        cmd = json.dumps(cmd_dict) + "\n"
        try:
            # Drain older unread commands so queue always delivers the freshest position
            while not self._cmd_queue.empty():
                try:
                    self._cmd_queue.get_nowait()
                except Exception:
                    break
            self._cmd_queue.put_nowait(cmd)
            self._last_cmd_time = now
        except Exception:
            pass

    def get_latest(self) -> Tuple[Optional[float], Optional[float], bool, Dict[str, Any]]:
        """Backward-compatible radar data accessor."""
        return self.range_m, self.velocity_mps, self.connected, self.raw_data

    def get_servo_state(self) -> Dict[str, Any]:
        """Returns current servo tracking state for telemetry."""
        return {
            "servo_pan": round(self.servo_pan, 1),
            "servo_tilt": round(self.servo_tilt, 1),
            "servo_status": self.servo_status,
            "servo_connected": self.servo_connected
        }

    def stop(self):
        self.running = False
        self.connected = False
        self.servo_connected = False
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
                        # Windows Media Foundation (CAP_MSMF) or default backend for clean UVC video without DSHOW buffer corruption
                        self.cap = cv2.VideoCapture(curr_src, cv2.CAP_MSMF)
                        if not self.cap.isOpened():
                            self.cap = cv2.VideoCapture(curr_src)
                        if not self.cap.isOpened() and curr_src != 0:
                            self.cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
                        if not self.cap.isOpened() and curr_src != 0:
                            self.cap = cv2.VideoCapture(0)
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
esp32_bridge = ESP32SerialBridge(
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

# Human / Face Suppression Cascades (prevents false positive detections on humans/people)
try:
    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    if face_cascade.empty():
        face_cascade = None
except Exception:
    face_cascade = None

VALID_DRONE_CLASSES = {
    "drone", "quadcopter", "fixed-wing", "uav", "multirotor",
    "shahed_136", "shahed_238", "mq9_reaper", "dji_mavic", "mohajer_6",
    "octocopter", "hexacopter", "fixed_wing", "aircraft", "airplane", "mavic"
}

HUMAN_DISALLOWED_CLASSES = {
    "person", "human", "pedestrian", "people", "man", "woman", "face", "body", "head",
    "bicycle", "car", "chair", "cell phone", "bottle", "cup", "dog", "cat",
    "tv", "laptop", "motor", "bus", "truck", "others", "awning-tricycle", "tricycle", "van"
}

# Global YOLO model holders (Triple-Model Ensemble)
yolo_model: Optional[YOLO] = None
secondary_yolo_model: Optional[YOLO] = None
military_yolo_model: Optional[YOLO] = None

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
    global yolo_model, secondary_yolo_model, military_yolo_model
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

    # Load Secondary Universal Drone Model (drone_yolo_v1.pt: quadcopter, fixed-wing)
    # Detects ducted FPV / Cinewhoop / Avata drones that best.pt lacks
    sec_path = Path(__file__).resolve().parent.parent / "smart_shield_ai" / "models" / "drone_yolo_v1.pt"
    if sec_path.is_file():
        try:
            secondary_yolo_model = YOLO(str(sec_path)).to(device)
            logger.info(f"Secondary Drone Model (drone_yolo_v1.pt) loaded on {device}. Classes: {secondary_yolo_model.names}")
        except Exception as e_sec:
            logger.warning(f"Could not load secondary model: {e_sec}")
            secondary_yolo_model = None
    else:
        secondary_yolo_model = None

    # Military model disabled: produces false positive dji_mavic/shahed detections on indoor wall/ceiling/furniture
    military_yolo_model = None

    # 3. Start Camera Capture Thread
    cam_stream.start()

    # 4. Start AI Dedicated GPU Worker Thread
    ai_worker.start()

    # 5. Start ESP32 Serial Bridge (Radar + Servo Tracking)
    if config.radar.enabled or config.radar.serial_port:
        esp32_bridge.start()

    # 6. Start Real-Time Fast Telemetry Broadcast Loop
    asyncio.create_task(fusion_orchestration_loop())
    logger.info("SMART-SHIELD v3.0 Real-Time AI Pipeline Started.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SMART-SHIELD services...")
    ai_worker.stop()
    cam_stream.stop()
    esp32_bridge.stop()
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
    high_threat: bool = False,
    primary_target: Optional[dict] = None
):
    """Draw tactical HUD with Center Target Alignment Box ('Invisible Square' visualizer)."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    # Optical Alignment Square: 120px wide x 100px tall
    bw, bh = 120, 100
    x1, y1 = cx - bw // 2, cy - bh // 2
    x2, y2 = cx + bw // 2, cy + bh // 2

    # Check if target is inside the square
    in_square = False
    tx, ty = None, None
    if primary_target and "center_u" in primary_target:
        tx = int(primary_target["center_u"])
        ty = int(primary_target.get("center_v", cy))
        if x1 <= tx <= x2 and y1 <= ty <= y2:
            in_square = True

    # Color scheme: Bright Green if locked inside square, Amber/Cyan if tracking
    color = (0, 255, 0) if in_square else (0, 220, 255)
    corner_len = 16
    thick = 2 if in_square else 1

    # Draw 4 Tactical Corner Brackets for the center square
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thick)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thick)
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thick)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thick)
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thick)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thick)
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thick)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thick)

    # Center Boresight Crosshair
    cv2.drawMarker(frame, (cx, cy), color, markerType=cv2.MARKER_CROSS, markerSize=14, thickness=1)

    # Status Label on Center Square
    status_txt = "[ TARGET LOCKED IN ZONE ]" if in_square else "[ OPTICAL TRACK ZONE ]"
    cv2.putText(frame, status_txt, (x1 - 10, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 1, cv2.LINE_AA)

    # If target is outside the square, draw direction guide towards square
    if primary_target and tx is not None and not in_square:
        cv2.line(frame, (tx, ty), (cx, cy), (0, 160, 255), 1, cv2.LINE_AA)
        cues = []
        if tx < x1: cues.append("PAN LEFT")
        elif tx > x2: cues.append("PAN RIGHT")
        if ty < y1: cues.append("TILT UP")
        elif ty > y2: cues.append("TILT DOWN")
        if cues:
            cue_txt = " | ".join(cues)
            cv2.putText(frame, f">> {cue_txt} >>", (x1 - 10, y2 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 180, 255), 1, cv2.LINE_AA)


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
        self.track_hit_counts: Dict[int, int] = {}

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
                radar_range, radar_speed, radar_connected, raw_radar_dict = esp32_bridge.get_latest()
                w = config.ai.camera_width
                h = config.ai.camera_height

                evaluated_targets: List[Dict[str, Any]] = []
                active_track_ids: List[int] = []

                # ================================================================
                # CASE A: LIVE CAMERA / VIDEO AVAILABLE -> RUN FULL GPU AI PIPELINE
                # ================================================================
                if has_frame and frame is not None:
                    annotated_frame = frame.copy()
                    h, w = frame.shape[:2]

                    # Run GPU YOLO Inference with ByteTrack tracking
                    if yolo_model is not None:
                        try:
                            results = yolo_model.track(
                                frame,
                                persist=True,
                                tracker="bytetrack.yaml",
                                device=self.device,
                                conf=config.ai.yolo_confidence,
                                iou=config.ai.yolo_iou,
                                imgsz=config.ai.yolo_imgsz,
                                verbose=False
                            )
                        except Exception:
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

                        # Clean Model Inference: Primary YOLO (best.pt)
                        has_boxes = (results[0].boxes is not None and len(results[0].boxes) > 0)
                        max_conf = float(results[0].boxes.conf.max()) if has_boxes else 0.0

                        # Clean Secondary Fallback (drone_yolo_v1.pt for ducted / FPV drones)
                        # Only runs if primary (best.pt) produced 0 detections, with safe conf=0.38 threshold
                        if not has_boxes and secondary_yolo_model is not None:
                            try:
                                sec_conf = max(0.38, config.ai.yolo_confidence)
                                sec_results = secondary_yolo_model.predict(
                                    frame,
                                    device=self.device,
                                    conf=sec_conf,
                                    iou=config.ai.yolo_iou,
                                    imgsz=config.ai.yolo_imgsz,
                                    verbose=False
                                )
                                if sec_results[0].boxes is not None and len(sec_results[0].boxes) > 0:
                                    results = sec_results
                                    has_boxes = True
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

                            # Detect human faces in frame to suppress false detections on humans/people
                            detected_faces = []
                            if face_cascade is not None and frame is not None:
                                try:
                                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                    faces = face_cascade.detectMultiScale(
                                        gray_frame,
                                        scaleFactor=1.2,
                                        minNeighbors=4,
                                        minSize=(30, 30)
                                    )
                                    if len(faces) > 0:
                                        detected_faces = faces
                                except Exception:
                                    pass

                            seen_candidate_tids = set()
                            for box, score, tid, cls_name in zip(boxes, confs, track_ids, class_names):
                                if float(score) < config.ai.yolo_confidence:
                                    continue
                                x1, y1, x2, y2 = map(int, box)
                                bw = x2 - x1
                                bh = y2 - y1

                                # 1. Strict Class Name Filter (Whitelist drones, Blacklist humans/objects)
                                cls_name_str = str(cls_name).strip().lower()
                                if cls_name_str in HUMAN_DISALLOWED_CLASSES:
                                    continue
                                if any(hw in cls_name_str for hw in ("person", "human", "pedestrian", "people", "man", "woman", "face", "body")):
                                    continue
                                is_drone_match = (
                                    cls_name_str in VALID_DRONE_CLASSES or
                                    any(kw in cls_name_str for kw in ("drone", "quadcopter", "uav", "copter", "wing", "shahed", "reaper", "mavic", "mohajer", "aircraft", "airplane"))
                                )
                                if not is_drone_match:
                                    continue

                                # 2. Geometric Shape & Sanity Size Filters (Reject full-room, furniture, and extreme linear/stripe artifacts)
                                if bw < 20 or bh < 20:
                                    continue
                                if bw > (0.60 * w) or bh > (0.60 * h):
                                    continue
                                if (bw * bh) > (0.30 * w * h):
                                    continue
                                aspect_ratio = float(bw) / max(1.0, float(bh))
                                if aspect_ratio < 0.35 or aspect_ratio > 3.0:
                                    continue

                                # 3. Human Face Spatial Overlap Suppression (only if box is predominantly a human face)
                                is_human_overlap = False
                                for (fx, fy, fw, fh) in detected_faces:
                                    head_x1 = int(fx)
                                    head_y1 = int(fy)
                                    head_x2 = int(fx + fw)
                                    head_y2 = int(fy + fh)

                                    ix1 = max(x1, head_x1)
                                    iy1 = max(y1, head_y1)
                                    ix2 = min(x2, head_x2)
                                    iy2 = min(y2, head_y2)

                                    if ix2 > ix1 and iy2 > iy1:
                                        inter_area = (ix2 - ix1) * (iy2 - iy1)
                                        box_area = max(1, bw * bh)
                                        if (inter_area / box_area) > 0.70:
                                            is_human_overlap = True
                                            break

                                if is_human_overlap:
                                    continue

                                # 4. Multi-Frame Temporal Confirmation (Anti-Overfitting Filter)
                                # Requires detection across at least 2 consecutive frames before confirming track.
                                # Completely eliminates single-frame transient room blips/glitches.
                                seen_candidate_tids.add(tid)
                                self.track_hit_counts[tid] = min(10, self.track_hit_counts.get(tid, 0) + 1)
                                if self.track_hit_counts[tid] < 2:
                                    continue

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
                                end_pt_2s = next((wp for wp in future_waypoints_3d if abs(wp.get("t_sec", 0) - 2.0) < 0.25), None)
                                if not end_pt_2s and len(future_waypoints_3d) >= 4:
                                    end_pt_2s = future_waypoints_3d[3]
                                if not end_pt_2s:
                                    end_pt_2s = {"x_m": round(x_m + vx_ms_val * 2.0, 1), "y_m": round(y_m + vy_ms_val * 2.0, 1), "z_m": round(z_m + vz_ms_val * 2.0, 1), "t_sec": 2.0}

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
                                    "predicted_endpoint_2s": {
                                        "x_m": end_pt_2s["x_m"],
                                        "y_m": end_pt_2s["y_m"],
                                        "z_m": end_pt_2s["z_m"],
                                        "t_sec": end_pt_2s.get("t_sec", 2.0)
                                    },
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

                    # Decay inactive candidate track counters to avoid memory leak and stale counts
                    for tid_k in list(self.track_hit_counts.keys()):
                        if tid_k not in seen_candidate_tids:
                            self.track_hit_counts[tid_k] -= 1
                            if self.track_hit_counts[tid_k] <= 0:
                                del self.track_hit_counts[tid_k]

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
                        end_pt_2s = next((wp for wp in future_waypoints_3d if abs(wp.get("t_sec", 0) - 2.0) < 0.25), None)
                        if not end_pt_2s and len(future_waypoints_3d) >= 4:
                            end_pt_2s = future_waypoints_3d[3]
                        if not end_pt_2s:
                            end_pt_2s = {"x_m": round(t["x_m"] + t["vx_ms"] * 2.0, 1), "y_m": round(t["y_m"] + t["vy_ms"] * 2.0, 1), "z_m": round(t["z_m"], 1), "t_sec": 2.0}

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
                            "predicted_endpoint_2s": {
                                "x_m": end_pt_2s["x_m"],
                                "y_m": end_pt_2s["y_m"],
                                "z_m": end_pt_2s["z_m"],
                                "t_sec": end_pt_2s.get("t_sec", 2.0)
                            },
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
                    high_threat=has_high_threat,
                    primary_target=primary_target
                )

                # Update latest frame cache for MJPEG streamer atomically
                with frame_lock:
                    latest_annotated_frame = annotated_frame.copy()

                # Active Target Lock & Visual Servoing Gimbal Tracking
                pan_deg, tilt_deg, lock_meta = gimbal_ctrl.update_tracking(
                    targets=evaluated_targets,
                    primary_target=primary_target,
                    frame_width=w,
                    frame_height=h
                )
                threat_for_servo = primary_target.get("threat_level", "LOW") if primary_target else "LOW"

                # Send servo tracking command to ESP32 via serial bridge
                if config.gimbal.servo_enabled and esp32_bridge.servo_connected:
                    is_active = (has_frame and (frame is not None) and (primary_target is not None) and lock_meta.get("is_locked", False))
                    if is_active:
                        esp32_bridge.send_servo_command(pan_deg, tilt_deg=tilt_deg, threat_level=threat_for_servo, force=False, tracking=True)
                    else:
                        # Instant Freeze Stop: When no drone is locked or camera offline, brake pan and hold tilt at current/neutral position
                        esp32_bridge.send_servo_command(90.0, tilt_deg=tilt_deg, threat_level="LOW", force=False, tracking=False)

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
                        "auto_track": gimbal_ctrl.auto_track_enabled,
                        **lock_meta,
                        **esp32_bridge.get_servo_state()
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
    servo_state = esp32_bridge.get_servo_state()
    return {
        "status": "ONLINE",
        "version": "3.0.0",
        "time": time.time(),
        "camera_connected": cam_stream.connected,
        "radar_connected": esp32_bridge.connected,
        "servo_connected": servo_state["servo_connected"],
        "servo_pan": servo_state["servo_pan"],
        "servo_status": servo_state["servo_status"],
        "active_targets": len(latest_targets),
        "primary_target": latest_primary_target["id"] if latest_primary_target else None
    }


@app.post("/api/ai/set_sensitivity")
async def api_set_ai_sensitivity(conf: float = 0.28):
    conf = max(0.05, min(0.95, conf))
    config.ai.yolo_confidence = conf
    return {"status": "SUCCESS", "yolo_confidence": conf}


@app.post("/api/gimbal/toggle_invert")
async def api_toggle_invert():
    new_state = gimbal_ctrl.toggle_invert()
    return {"status": "SUCCESS", "invert_pan": new_state}


@app.post("/api/gimbal/toggle_invert_tilt")
async def api_toggle_invert_tilt():
    new_state = gimbal_ctrl.toggle_invert_tilt()
    return {"status": "SUCCESS", "invert_tilt": new_state}


@app.post("/api/gimbal/toggle_mode")
async def api_toggle_gimbal_mode():
    new_mode = gimbal_ctrl.toggle_mode()
    return {"status": "SUCCESS", "mode": new_mode}


@app.post("/api/gimbal/lock_target")
async def api_lock_target(track_id: int):
    gimbal_ctrl.lock_target(track_id)
    return {"status": "SUCCESS", "locked_track_id": track_id}


@app.post("/api/gimbal/unlock_target")
async def api_unlock_target():
    gimbal_ctrl.unlock_target()
    return {"status": "SUCCESS", "locked_track_id": None}


@app.post("/api/gimbal/recenter")
async def api_recenter_gimbal():
    gimbal_ctrl.set_manual_angles(90.0, 90.0)
    if esp32_bridge.servo_connected:
        esp32_bridge.send_servo_command(90.0, tilt_deg=90.0, threat_level="LOW", force=True)
    return {"status": "SUCCESS", "pan": 90.0, "tilt": 90.0}


@app.post("/api/gimbal/manual")
async def api_manual_gimbal(payload: Dict[str, float]):
    pan = payload.get("pan", 90.0)
    tilt = payload.get("tilt", 90.0)
    gimbal_ctrl.set_manual_angles(pan, tilt)
    if esp32_bridge.servo_connected:
        esp32_bridge.send_servo_command(pan, tilt_deg=tilt, threat_level="MANUAL", force=True)
    return {"status": "SUCCESS", "pan": pan, "tilt": tilt}


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


@app.get("/api/airspace/situation_after_2s")
async def get_airspace_situation_after_2s():
    """Returns the forecasted 3D tactical airspace situation 2 seconds into the future."""
    global latest_situation_2s
    if not latest_situation_2s:
        return {
            "status": "STANDBY",
            "forecast_time_s": 2.0,
            "total_targets": 0,
            "any_breach": False,
            "targets": []
        }
    return {
        "status": "SUCCESS",
        "timestamp_now": time.time(),
        **latest_situation_2s
    }


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
    """Switches active video source between USB Webcams and uploaded video."""
    src = str(req.get("source", "1")).strip().lower()
    if src in ("1", "external", "usb_ext", "ext", "usb"):
        cam_stream.set_source(1, source_name="USB Camera (Index 1)")
        return {"status": "SUCCESS", "source_type": "USB_CAMERA", "source_name": "USB Camera (Index 1)"}
    elif src in ("0", "webcam", "internal", "int"):
        cam_stream.set_source(0, source_name="Webcam (Index 0)")
        return {"status": "SUCCESS", "source_type": "INTERNAL_WEBCAM", "source_name": "Webcam (Index 0)"}
    elif os.path.isfile(str(req.get("source"))):
        path_val = str(req.get("source"))
        cam_stream.set_source(path_val, source_name=f"Video: {os.path.basename(path_val)}")
        return {"status": "SUCCESS", "source_type": "VIDEO_FILE", "source_name": os.path.basename(path_val)}
    else:
        try:
            idx = int(src)
            cam_stream.set_source(idx, source_name=f"Camera (Index {idx})")
            return {"status": "SUCCESS", "source_type": f"CAMERA_{idx}", "source_name": f"Camera (Index {idx})"}
        except ValueError:
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
