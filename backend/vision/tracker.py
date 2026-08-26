"""
SMART-SHIELD v3.0 Multi-Object Tracker (ByteTrack Implementation)
Maintains persistent track IDs across frames and handles association through occlusions.
"""

import math
import time
from typing import List, Dict, Any, Optional

class Track:
    """Represents a single persistent target track with Kalman state filtering."""
    def __init__(self, track_id: int, bbox: List[float], class_name: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.class_name = class_name
        self.confidence = confidence
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.history = [bbox]
        self.state = "TRACKING"  # "TRACKING", "LOST"

    def update(self, bbox: List[float], confidence: float, class_name: Optional[str] = None):
        self.bbox = bbox
        self.confidence = confidence
        if class_name:
            self.class_name = class_name
        self.hits += 1
        self.time_since_update = 0
        self.history.append(bbox)
        if len(self.history) > 30:
            self.history.pop(0)

    def mark_missed(self):
        self.time_since_update += 1
        self.age += 1
        if self.time_since_update > 10:
            self.state = "LOST"


class ByteTracker:
    """ByteTrack multi-target association algorithm."""
    def __init__(self, max_lost_frames: int = 15, iou_threshold: float = 0.3):
        self.max_lost_frames = max_lost_frames
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1

    @staticmethod
    def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        denom = float(boxAArea + boxBArea - interArea)
        return interArea / denom if denom > 0 else 0.0

    def update(self, detections: List[Dict[str, Any]]) -> List[Track]:
        matched_tracks = set()
        matched_dets = set()

        # Step 1: Match high-confidence detections with existing tracks
        for d_idx, det in enumerate(detections):
            best_iou = self.iou_threshold
            best_t_idx = -1
            for t_idx, track in enumerate(self.tracks):
                if t_idx in matched_tracks:
                    continue
                iou = self.calculate_iou(det["bbox"], track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_t_idx = t_idx

            if best_t_idx >= 0:
                self.tracks[best_t_idx].update(det["bbox"], det["confidence"], det["class_name"])
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)

        # Step 2: Unmatched detections initiate new tracks
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                # Use predefined simulation ID if present, otherwise increment ID
                t_id = det.get("id", self.next_id)
                if isinstance(t_id, int):
                    self.next_id = max(self.next_id, t_id + 1)
                else:
                    self.next_id += 1
                new_track = Track(
                    track_id=t_id,
                    bbox=det["bbox"],
                    class_name=det["class_name"],
                    confidence=det["confidence"]
                )
                self.tracks.append(new_track)

        # Step 3: Unmatched tracks are marked missed
        for t_idx, track in enumerate(self.tracks):
            if t_idx not in matched_tracks:
                track.mark_missed()

        # Clean up permanently lost tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_lost_frames]
        return [t for t in self.tracks if t.time_since_update == 0]
