"""
Smart Shield AI Engine
Central configuration
"""

from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "best.pt"

OUTPUT_DIR = BASE_DIR / "outputs"

RECORDING_DIR = OUTPUT_DIR / "recordings"

LOG_DIR = OUTPUT_DIR / "logs"


# ============================================================
# CAMERA
# ============================================================

CAMERA_SOURCE = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

CAMERA_FPS = 30


# ============================================================
# YOLO
# ============================================================

YOLO_CONFIDENCE = 0.35

YOLO_IOU = 0.50

YOLO_IMAGE_SIZE = 640


# ============================================================
# TRACKING
# ============================================================

TRACKER_CONFIG = "bytetrack.yaml"

MAX_TRACK_HISTORY = 30


# ============================================================
# SPEED
# ============================================================

METERS_PER_PIXEL = None

SPEED_SMOOTHING = 8


# ============================================================
# RADAR
# ============================================================

RADAR_ENABLED = False

RADAR_PORT = "COM5"

RADAR_BAUDRATE = 115200


# ============================================================
# SENSOR FUSION
# ============================================================

CAMERA_WEIGHT = 0.40

RADAR_WEIGHT = 0.60

MAX_SENSOR_AGE = 0.5


# ============================================================
# TRAJECTORY
# ============================================================

PREDICTION_HORIZON = 3.0

PREDICTION_STEP = 0.2


# ============================================================
# MONITORING / RISK
# ============================================================

LOW_CONFIDENCE_THRESHOLD = 0.35

MEDIUM_RISK_THRESHOLD = 40

HIGH_RISK_THRESHOLD = 70


# ============================================================
# DISPLAY
# ============================================================

SHOW_WINDOW = True

SAVE_VIDEO = False


# ============================================================
# CREATE DIRECTORIES
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RECORDING_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)