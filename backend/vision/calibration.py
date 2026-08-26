"""
SMART-SHIELD v3.0 Camera-to-World Calibration Module
Implements Homography / Planar perspective mapping and Pinhole Intrinsic/Extrinsic 3D coordinate conversion.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Any

class HomographyCalibrator:
    """Computes and applies a 3x3 Homography perspective matrix from 4-point image-to-world correspondences."""
    def __init__(self, image_points: Optional[List[Tuple[float, float]]] = None, world_points: Optional[List[Tuple[float, float]]] = None):
        self.H = np.eye(3, dtype=float)
        self.H_inv = np.eye(3, dtype=float)
        self.is_calibrated = False

        if image_points and world_points and len(image_points) >= 4 and len(world_points) >= 4:
            self.compute_homography(image_points, world_points)

    def compute_homography(self, image_points: List[Tuple[float, float]], world_points: List[Tuple[float, float]]) -> bool:
        """
        Calculates homography matrix H mapping image points (u, v) to world points (X, Y).
        Uses OpenCV cv2.findHomography if available, or Direct Linear Transformation (DLT) fallback.
        """
        try:
            import cv2
            src_pts = np.array(image_points, dtype=np.float32).reshape(-1, 1, 2)
            dst_pts = np.array(world_points, dtype=np.float32).reshape(-1, 1, 2)
            H_mat, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H_mat is not None:
                self.H = H_mat
                self.H_inv = np.linalg.inv(self.H)
                self.is_calibrated = True
                return True
        except Exception:
            pass

        # Manual DLT (Direct Linear Transformation) Fallback
        if len(image_points) >= 4 and len(world_points) >= 4:
            A = []
            for (u, v), (X, Y) in zip(image_points[:4], world_points[:4]):
                A.append([-u, -v, -1, 0, 0, 0, u * X, v * X, X])
                A.append([0, 0, 0, -u, -v, -1, u * Y, v * Y, Y])
            A = np.array(A, dtype=float)
            _, _, Vh = np.linalg.svd(A)
            L = Vh[-1, :] / Vh[-1, -1]
            self.H = L.reshape(3, 3)
            self.H_inv = np.linalg.inv(self.H)
            self.is_calibrated = True
            return True

        return False

    def pixel_to_world(self, u: float, v: float) -> Tuple[float, float]:
        """Transforms 2D pixel coordinates (u, v) to real-world ground coordinates (X, Y)."""
        vec = np.array([u, v, 1.0], dtype=float)
        world_homo = self.H @ vec
        if abs(world_homo[2]) > 1e-6:
            X = world_homo[0] / world_homo[2]
            Y = world_homo[1] / world_homo[2]
            return round(float(X), 2), round(float(Y), 2)
        return 0.0, 0.0

    def world_to_pixel(self, X: float, Y: float) -> Tuple[float, float]:
        """Transforms real-world ground coordinates (X, Y) back to 2D image pixels (u, v)."""
        vec = np.array([X, Y, 1.0], dtype=float)
        img_homo = self.H_inv @ vec
        if abs(img_homo[2]) > 1e-6:
            u = img_homo[0] / img_homo[2]
            v = img_homo[1] / img_homo[2]
            return round(float(u), 1), round(float(v), 1)
        return 0.0, 0.0


class PinholeCalibrator:
    """Pinhole camera intrinsic calibration model with radar-assisted depth projection."""
    def __init__(self, focal_length_px: float = 400.0, principal_point: Tuple[float, float] = (320.0, 230.0)):
        self.fx = focal_length_px
        self.fy = focal_length_px
        self.cx, self.cy = principal_point

        # Intrinsic Camera Matrix K
        self.K = np.array([
            [self.fx, 0.0, self.cx],
            [0.0, self.fy, self.cy],
            [0.0, 0.0, 1.0]
        ], dtype=float)
        self.K_inv = np.linalg.inv(self.K)

    def pixel_to_3d_point(self, u: float, v: float, depth_m: float) -> Tuple[float, float, float]:
        """
        Converts 2D pixel coordinate (u, v) and radar-measured range / depth (m) to 3D Cartesian coordinates (X, Y, Z).
        X = (u - cx) * depth / fx
        Y = depth (forward range)
        Z = (cy - v) * depth / fy (altitude)
        """
        X = (u - self.cx) * depth_m / self.fx
        Y = depth_m
        Z = (self.cy - v) * depth_m / self.fy
        return round(float(X), 2), round(float(Y), 2), round(float(Z), 2)

    def point_3d_to_pixel(self, X: float, Y: float, Z: float) -> Tuple[float, float]:
        """Projects 3D Cartesian point (X, Y, Z) onto camera 2D image plane (u, v)."""
        depth = max(0.1, Y)
        u = (X * self.fx / depth) + self.cx
        v = self.cy - (Z * self.fy / depth)
        return round(float(u), 1), round(float(v), 1)
