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

