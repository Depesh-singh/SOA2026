"""
VayuNetra — GPU-Accelerated Live Camera Servo Tracker
=====================================================
- Instant Brake (90.0): Stops completely when drone is centered or lost.
- Strict 180° Travel Bounds: Never spins continuous/round-and-round.
- Dual Mode: Supports Continuous (360°) and Standard Positional (180°) servos.
- NVIDIA GPU CUDA FP16 Acceleration.
- External USB Camera Default (Index 1).

Keyboard Controls:
    m       : Toggle Mode (Continuous 360° vs Positional 180°)
    i       : Invert Direction (if movement is opposite)
    c       : Switch Camera (USB <-> Laptop)
    r       : Reset Servo to Center
    + / -   : Increase / Decrease Detection Confidence
    q / ESC : Quit (brakes motor)

Usage:
    python servo_tracker/test_live_camera.py
"""

import sys
import os
import time
import threading
import argparse
import cv2
import numpy as np
import torch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_controller import ServoTracker

try:
    from ultralytics import YOLO
except ImportError:
    print("ERROR: ultralytics is not installed.")
    sys.exit(1)


class ThreadedCamera:
    """Threaded camera reader for real-time zero-latency frame grabbing."""

    def __init__(self, src=1, width=640, height=480):
        self.src = src
        self.width = width
        self.height = height
        self.cap = None
        self.ret = False
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self._init_capture()

    def _init_capture(self):
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.src)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def start(self):
        if self.cap is None or not self.cap.isOpened():
            return False
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        for _ in range(50):
            if self.frame is not None:
                return True
            time.sleep(0.02)
        return self.frame is not None

    def _update(self):
        while self.running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.frame = frame
                        self.ret = ret
                else:
                    time.sleep(0.005)
            else:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def release(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()


def switch_camera(current_src, width=640, height=480):
    next_src = 0 if current_src == 1 else 1
    print(f"\n[Camera] Switching to Camera {next_src}...")
    new_cam = ThreadedCamera(src=next_src, width=width, height=height)
    if new_cam.start():
        print(f"[Camera] Active: Camera {next_src}")
        return new_cam, next_src
    else:
        new_cam.release()
        fallback_cam = ThreadedCamera(src=current_src, width=width, height=height)
        fallback_cam.start()
        return fallback_cam, current_src


def find_default_model():
    candidates = [
        os.path.join(ROOT_DIR, "smart_shield_ai", "models", "drone_yolo_v1.pt"),
        os.path.join(ROOT_DIR, "smart_shield_ai", "models", "best.pt"),
        os.path.join(ROOT_DIR, "smart_shield_ai", "models", "best_military_detector.pt"),
        os.path.join(ROOT_DIR, "yolov8n.pt"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "yolov8n.pt"


def main():
    parser = argparse.ArgumentParser(description="Precision Live Drone Tracker")
    parser.add_argument("--cam", type=int, default=1, help="Camera index (default: 1 for USB)")
    parser.add_argument("--port", type=str, default="COM5", help="ESP32 COM port")
    parser.add_argument("--conf", type=float, default=0.22, help="YOLO confidence threshold")
    parser.add_argument("--mode", type=str, default="continuous", choices=["continuous", "positional"], help="Servo type")
    parser.add_argument("--imgsz", type=int, default=480, help="Inference resolution")
    args = parser.parse_args()

    # ── GPU Setup ──
    if torch.cuda.is_available():
        device = "cuda:0"
        use_half = True
        print(f"[GPU] CUDA Accelerated: {torch.cuda.get_device_name(0)} (FP16)")
    else:
        device = "cpu"
        use_half = False
        print("[WARNING] Running on CPU")

    model_path = find_default_model()
    print(f"[Model] Loading: {model_path}")
    model = YOLO(model_path)

    if device.startswith("cuda"):
        dummy = np.zeros((args.imgsz, args.imgsz, 3), dtype=np.uint8)
        model.predict(dummy, device=device, half=use_half, verbose=False)

    # ── Servo Tracker (Default Continuous with Brake Control) ──
    print(f"[Servo] Initializing Tracker on {args.port} (Mode: {args.mode.upper()})...")
    tracker = ServoTracker(
        port=args.port,
        baudrate=115200,
        mode=args.mode,
        deadband_px=50,       # Wide center zone: Drone centered = STOP MOTOR
        invert=False,
    )
    tracker.start()

    # ── Open Camera ──
    current_cam_idx = args.cam
    print(f"[Camera] Opening Camera {current_cam_idx}...")
    cam = ThreadedCamera(src=current_cam_idx, width=640, height=480)
    if not cam.start():
        fallback_idx = 0 if current_cam_idx == 1 else 1
        print(f"[Camera] Trying Camera {fallback_idx}...")
        cam.release()
        current_cam_idx = fallback_idx
        cam = ThreadedCamera(src=current_cam_idx, width=640, height=480)
        if not cam.start():
            print("[ERROR] No camera found.")
            tracker.stop()
            return

    conf_thresh = args.conf
    fps_history = []

    print("\n" + "=" * 65)
    print("  VAYUNETRA CONTROLLED 180° TRACKER ACTIVE")
    print("=" * 65)
    print("  Safety Features:")
    print("    • Drone in Center Green Zone  → MOTOR BRAKES TO STOP")
    print("    • No Drone Detected           → MOTOR BRAKES TO STOP")
    print("    • Drone on Left               → Turns Left (until centered)")
    print("    • Drone on Right              → Turns Right (until centered)")
    print("    • 180° Software Lock          → NEVER spins 360°/720°")
    print("\n  Keys:")
    print("    [M] Toggle Mode (Continuous 360 vs Positional 180)")
    print("    [I] Invert Left/Right | [R] Reset Center | [Q] Quit")
    print("=" * 65 + "\n")

    cv2.namedWindow("VayuNetra — 180° Precision Tracker", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("VayuNetra — 180° Precision Tracker", 960, 720)

    try:
        while True:
            t0 = time.time()
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            h, w = frame.shape[:2]
            cx_frame = w // 2

            # ── Fast YOLO Inference ──
            results = model.predict(
                source=frame,
                device=device,
                half=use_half,
                imgsz=args.imgsz,
                conf=conf_thresh,
                verbose=False
            )
            boxes = results[0].boxes if len(results) > 0 else None

            best_box = None
            highest_conf = -1.0
            if boxes is not None and len(boxes) > 0:
                for b in boxes:
                    c = float(b.conf[0].item())
                    if c > highest_conf:
                        highest_conf = c
                        best_box = b

            # ── Update Tracker ──
            if best_box is not None:
                xyxy = best_box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                target_cx = (x1 + x2) / 2.0
                target_cy = (y1 + y2) / 2.0
                cls_id = int(best_box.cls[0].item())
                cls_name = model.names.get(cls_id, "drone")

                tracker.update_target(target_center_x=target_cx, frame_width=w)

                # Draw Bounding Box & Target Center
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (int(target_cx), int(target_cy)), 6, (0, 0, 255), -1)
                cv2.line(frame, (int(target_cx), int(target_cy)), (cx_frame, int(target_cy)), (0, 255, 255), 2)

                label = f"{cls_name.upper()} {highest_conf:.2f}"
                cv2.putText(frame, label, (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                tracker.clear_target()

            state = tracker.get_state()

            # ── Center Green Still Zone ──
            db = tracker.deadband_px
            overlay = frame.copy()
            cv2.rectangle(overlay, (cx_frame - db, 0), (cx_frame + db, h), (0, 120, 0), -1)
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)

            cv2.line(frame, (cx_frame, 0), (cx_frame, h), (0, 255, 0), 1)
            cv2.line(frame, (cx_frame - db, 0), (cx_frame - db, h), (0, 220, 0), 1)
            cv2.line(frame, (cx_frame + db, 0), (cx_frame + db, h), (0, 220, 0), 1)
            cv2.putText(frame, "CENTER BRAKE ZONE", (cx_frame - db + 5, h - 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 0), 1)

            # ── Top HUD ──
            hud = frame.copy()
            cv2.rectangle(hud, (10, 10), (w - 10, 95), (15, 15, 15), -1)
            cv2.addWeighted(hud, 0.80, frame, 0.20, 0, frame)
            cv2.rectangle(frame, (10, 10), (w - 10, 95), (0, 200, 255), 1)

            # Row 1
            det_text = "LOCKED" if state["target_detected"] else "SEARCHING"
            det_color = (0, 255, 0) if state["target_detected"] else (0, 165, 255)
            cv2.putText(frame, f"STATUS: {det_text}", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, det_color, 2)

            dir_text = state["direction"]
            dir_color = (0, 255, 0) if "STILL" in dir_text or "STOPPED" in dir_text else (0, 255, 255)
            cv2.putText(frame, f"MOTOR: {dir_text}", (190, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, dir_color, 2)

            cur_cam_label = "USB (1)" if current_cam_idx == 1 else "LAPTOP (0)"
            cv2.putText(frame, f"[{cur_cam_label}]", (w - 150, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Row 2
            mode_label = state["mode"].upper()
            cv2.putText(frame, f"MODE: {mode_label}", (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            head_val = state["heading_deg"]
            cv2.putText(frame, f"SPAN: {head_val:+.0f} DEG [-90 to +90]", (220, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            # FPS
            dt = time.time() - t0
            fps = 1.0 / max(1e-4, dt)
            fps_history.append(fps)
            if len(fps_history) > 30:
                fps_history.pop(0)
            avg_fps = sum(fps_history) / len(fps_history)
            cv2.putText(frame, f"GPU: {avg_fps:.1f} FPS", (w - 170, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

            # Bottom help line
            inv_str = "INV" if state["invert"] else "NORM"
            cv2.putText(frame, f"[M] Mode: {mode_label} | [I] Dir: {inv_str} | [R] Reset | [C] Cam | [Q] Quit",
                        (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

            cv2.imshow("VayuNetra — 180° Precision Tracker", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('m'):
                new_mode = "positional" if tracker.mode == "continuous" else "continuous"
                tracker.set_mode(new_mode)
                print(f"[Servo] Switched Mode to: {new_mode.upper()}")
            elif key == ord('i'):
                tracker.set_invert(not tracker.invert)
                print(f"[Servo] Invert Direction: {tracker.invert}")
            elif key == ord('c'):
                cam.release()
                cam, current_cam_idx = switch_camera(current_cam_idx, width=640, height=480)
            elif key == ord('r'):
                tracker.reset_center()
                print("[Servo] Reset to Origin Center")
            elif key == ord('+') or key == ord('='):
                conf_thresh = min(0.90, conf_thresh + 0.05)
            elif key == ord('-') or key == ord('_'):
                conf_thresh = max(0.10, conf_thresh - 0.05)

    finally:
        print("\nStopping camera and braking motor...")
        cam.release()
        cv2.destroyAllWindows()
        tracker.stop()
        print("Done.\n")


if __name__ == "__main__":
    main()
