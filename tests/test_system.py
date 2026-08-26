"""
SMART-SHIELD v3.0 Automated Test Suite
Verifies Threat Scoring Math, LD2450 Radar Parsing, EKF State Estimation, and RF Jamming Detection.
"""

import math
import struct
import unittest

# Import system modules
from backend.hardware.esp32_serial import LD2450RadarParser
from backend.fusion.threat_matrix import ThreatEvaluationEngine
from backend.fusion.ekf import TargetEKFFilter
from backend.cyber_defense.rf_monitor import CyberRFMonitor

class TestSmartShieldCore(unittest.TestCase):

    def test_threat_scoring_math(self):
        """Validates that a fast, close-proximity drone yields HIGH threat while a distant slow object yields LOW threat."""
        # Hostile close inbound drone
        high_threat = ThreatEvaluationEngine.calculate_threat_score(
            distance_m=45.0,
            speed_ms=25.0,
            azimuth_deg=10.0,
            heading_deg=10.0,
            optical_confidence=0.98,
            classification="Drone (Hostile)",
            behavior_factor=0.9
        )
        self.assertGreaterEqual(high_threat["threat_score"], 75.0)
        self.assertEqual(high_threat["threat_level"], "HIGH")

        # Distant slow peripheral drone
        low_threat = ThreatEvaluationEngine.calculate_threat_score(
            distance_m=190.0,
            speed_ms=5.0,
            azimuth_deg=45.0,
            heading_deg=-90.0,
            optical_confidence=0.70,
            classification="Bird",
            behavior_factor=0.1
        )
        self.assertLess(low_threat["threat_score"], 40.0)
        self.assertEqual(low_threat["threat_level"], "LOW")

    def test_ld2450_radar_frame_parsing(self):
        """Validates binary unpacking of LD2450 30-byte radar packet."""
        header = bytes([0xAA, 0xFF, 0x03, 0x00])
        tail = bytes([0x55, 0xCC])
        
        # Target 1: X=-500mm, Y=3000mm, Speed=-150cm/s, Resolution=80
        t1 = struct.pack("<hhhH", -500, 3000, -150, 80)
        # Target 2 & 3 empty
        t2 = struct.pack("<hhhH", 0, 0, 0, 0)
        t3 = struct.pack("<hhhH", 0, 0, 0, 0)
        
        packet = header + t1 + t2 + t3 + tail
        self.assertEqual(len(packet), 30)

        targets = LD2450RadarParser.parse_frame(packet)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]["x_m"], -0.5)
        self.assertEqual(targets[0]["y_m"], 3.0)
        self.assertEqual(targets[0]["speed_ms"], -1.5)

    def test_ekf_state_prediction_and_update(self):
        """Validates Extended Kalman Filter state propagation and radar update."""
        ekf = TargetEKFFilter(init_x=0.0, init_y=50.0, init_z=10.0, init_vx=0.0, init_vy=-10.0, init_vz=0.0)
        ekf.predict(dt=0.1)
        
        state = ekf.get_fused_state()
        self.assertAlmostEqual(state["y_m"], 49.0, delta=0.5)
        
        # Update with radar measurement at range 49.0m, azimuth 0 rad, vr -10.0 m/s
        ekf.update_radar(r_meas=49.0, theta_rad_meas=0.0, vr_meas=-10.0)
        updated_state = ekf.get_fused_state()
        self.assertGreater(updated_state["distance_m"], 0.0)

    def test_cyber_rf_jamming_and_frequency_hop(self):
        """Validates RF spectrum anomaly detection and automatic frequency hopping."""
        rf = CyberRFMonitor()
        nominal_scan = rf.get_spectrum_scan()
        self.assertEqual(nominal_scan["status"], "SECURE")

        # Inject Jamming
        rf.toggle_jamming_simulation()
        jammed_scan = rf.get_spectrum_scan()
        self.assertEqual(jammed_scan["status"], "ATTACK_DETECTED")
        self.assertEqual(jammed_scan["severity"], "CRITICAL")

        # Execute Countermeasure
        old_ch = rf.active_channel
        hop_res = rf.execute_frequency_hop()
        self.assertEqual(hop_res["status"], "SUCCESS")
        self.assertNotEqual(rf.active_channel, old_ch)

        # After frequency hop, C2 link should be secure
        cleared_scan = rf.get_spectrum_scan()
        self.assertEqual(cleared_scan["status"], "SECURE")

    def test_sqlite_persistence_and_replay(self):
        """Validates SQLite database initialization, telemetry insertion, and CSV report generation."""
        import os
        import asyncio
        from database.db_manager import DatabaseManager

        test_db_path = "database/test_smart_shield.db"
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

        async def run_db_test():
            db = DatabaseManager(sqlite_path=test_db_path)
            await db.initialize()
            self.assertTrue(db.use_sqlite)

            # Insert sample telemetry
            await db.save_telemetry({
                "target_id": "DRONE-99",
                "x_pos_m": -12.5,
                "y_pos_m": 48.0,
                "z_pos_m": 15.0,
                "distance_m": 49.6,
                "azimuth_deg": -14.6,
                "speed_ms": 22.0,
                "optical_confidence": 0.95,
                "radar_snr": 92.0,
                "threat_score": 88.5,
                "threat_level": "HIGH"
            })

            # Query replay
            history = db.get_historical_telemetry(limit=10)
            self.assertGreaterEqual(len(history), 1)
            self.assertEqual(history[0]["target_id"], "DRONE-99")
            self.assertEqual(history[0]["threat_level"], "HIGH")

            # Export CSV
            csv_text = db.export_csv_report()
            self.assertIn("DRONE-99", csv_text)
            self.assertIn("Timestamp,Target_ID", csv_text)

            await db.close()

        asyncio.run(run_db_test())
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

    def test_multitarget_swarm_prioritization(self):
        """Validates that a swarm of 6 drones is correctly evaluated and ranked by threat score."""
        targets = [
            {"id": "DRONE-01", "distance_m": 150.0, "speed_ms": 5.0, "azimuth_deg": 30.0, "heading_deg": 0.0, "optical_confidence": 0.8, "classification": "Drone", "behavior_factor": 0.2},
            {"id": "DRONE-02", "distance_m": 120.0, "speed_ms": 10.0, "azimuth_deg": -20.0, "heading_deg": 0.0, "optical_confidence": 0.85, "classification": "Quadcopter", "behavior_factor": 0.3},
            {"id": "DRONE-03", "distance_m": 35.0, "speed_ms": 26.0, "azimuth_deg": 0.0, "heading_deg": 0.0, "optical_confidence": 0.98, "classification": "Drone (Hostile)", "behavior_factor": 0.9},
            {"id": "DRONE-04", "distance_m": 180.0, "speed_ms": 4.0, "azimuth_deg": 45.0, "heading_deg": -90.0, "optical_confidence": 0.6, "classification": "Bird", "behavior_factor": 0.1},
            {"id": "DRONE-05", "distance_m": 60.0, "speed_ms": 18.0, "azimuth_deg": 10.0, "heading_deg": 10.0, "optical_confidence": 0.92, "classification": "Drone", "behavior_factor": 0.6},
            {"id": "DRONE-06", "distance_m": 90.0, "speed_ms": 12.0, "azimuth_deg": -15.0, "heading_deg": 0.0, "optical_confidence": 0.88, "classification": "Fixed-Wing", "behavior_factor": 0.4}
        ]

        scored_targets = []
        for t in targets:
            score_data = ThreatEvaluationEngine.calculate_threat_score(
                distance_m=t["distance_m"],
                speed_ms=t["speed_ms"],
                azimuth_deg=t["azimuth_deg"],
                heading_deg=t["heading_deg"],
                optical_confidence=t["optical_confidence"],
                classification=t["classification"],
                behavior_factor=t["behavior_factor"]
            )
            scored_targets.append({**t, **score_data})

        ranked = ThreatEvaluationEngine.prioritize_targets(scored_targets)
        self.assertEqual(len(ranked), 6)
        self.assertEqual(ranked[0]["id"], "DRONE-03")
        self.assertTrue(ranked[0]["is_highest_priority"])
        self.assertEqual(ranked[0]["threat_level"], "HIGH")
        self.assertGreater(ranked[0]["threat_score"], ranked[1]["threat_score"])

    def test_camera_stream_manager_synthetic_feed(self):
        """Validates that CameraStreamManager generates valid JPEG image bytes for the HUD."""
        from backend.vision.detector import CameraStreamManager
        cam = CameraStreamManager()
        detections = [
            {"id": "DRONE-01", "bbox": [100.0, 100.0, 160.0, 140.0], "center_u": 130.0, "center_v": 120.0, "width": 60.0, "height": 40.0, "confidence": 0.95, "class_name": "Drone"}
        ]
        jpeg_bytes = cam.get_annotated_frame_bytes(targets=[], detections=detections, primary_id="DRONE-01")
        self.assertIsInstance(jpeg_bytes, bytes)
        self.assertGreater(len(jpeg_bytes), 100)
        # JPEG SOI marker (0xFFD8)
        self.assertEqual(jpeg_bytes[:2], b'\xff\xd8')

    def test_optical_velocity_estimator(self):
        """Validates that OpticalVelocityEstimator calculates smooth pixel velocities and metric rates."""
        from backend.vision.velocity_estimator import OpticalVelocityEstimator
        estimator = OpticalVelocityEstimator()

        history = [
            [100.0, 100.0, 150.0, 130.0], # Frame 1 center: (125, 115)
            [110.0, 105.0, 162.0, 136.0]  # Frame 2 center: (136, 120.5) (expanding)
        ]
        timestamps = [0.0, 0.033]

        vel = estimator.estimate_velocity_from_history("TRK-01", history, timestamps, estimated_depth_m=60.0)
        self.assertIn("vel_u_px_s", vel)
        self.assertIn("speed_est_ms", vel)
        self.assertGreater(vel["vel_u_px_s"], 0.0)
        self.assertGreater(vel["speed_est_ms"], 0.0)

    def test_trajectory_predictor_and_cpa(self):
        """Validates forward trajectory prediction and Closest Point of Approach calculation."""
        from backend.fusion.trajectory_predictor import TrajectoryPredictor
        predictor = TrajectoryPredictor()

        # Inbound drone: x=20m, y=100m, moving inbound vy=-20m/s
        waypoints = predictor.predict_future_trajectory(x_m=20.0, y_m=100.0, z_m=15.0, vx_ms=0.0, vy_ms=-20.0, horizon_s=3.0)
        self.assertEqual(len(waypoints), 6) # 3.0s / 0.5s step
        self.assertLess(waypoints[-1]["y_m"], 100.0)

        # CPA test
        cpa = predictor.calculate_closest_point_of_approach(x_m=20.0, y_m=100.0, z_m=0.0, vx_ms=0.0, vy_ms=-20.0)
        self.assertTrue(cpa["is_inbound"])
        self.assertAlmostEqual(cpa["t_cpa_sec"], 5.0, delta=0.1) # 100m / 20m/s = 5s
        self.assertAlmostEqual(cpa["d_cpa_m"], 20.0, delta=0.5)

    def test_sensor_fusion_engine(self):
        """Validates SensorFusionEngine multi-sensor coordination and EKF state integration."""
        from backend.fusion.sensor_fusion import SensorFusionEngine, fuse_velocities_weighted
        fusion = SensorFusionEngine()

        sample_target = {
            "id": "DRONE-01",
            "x_m": 15.0,
            "y_m": 60.0,
            "z_m": 12.0,
            "distance_m": 61.8,
            "azimuth_deg": 14.0,
            "speed_ms": -18.0
        }
        fused = fusion.fuse_target(sample_target, dt=0.033)
        self.assertEqual(fused["id"], "DRONE-01")
        self.assertIn("cpa", fused)
        self.assertIn("vx_ms", fused)

        # Weighted velocity fusion tests (formula from Page 3)
        # Case 1: Normal agreement
        v_fused = fuse_velocities_weighted(v_camera=20.0, v_radar=18.0, w_camera=0.4, w_radar=0.6)
        self.assertAlmostEqual(v_fused, 18.8, delta=0.2)

        # Case 2: Outlier disagreement (>15m/s difference -> down-weights camera)
        v_outlier = fuse_velocities_weighted(v_camera=50.0, v_radar=10.0, disagreement_threshold=15.0)
        self.assertLess(v_outlier, 16.0) # Heavily pulled toward radar (10 m/s)

        # Case 3: Single sensor failure / missing radar
        v_cam_only = fuse_velocities_weighted(v_camera=22.0, v_radar=None)
        self.assertEqual(v_cam_only, 22.0)

    def test_camera_calibration_homography_and_pinhole(self):
        """Validates Homography planar transformation and Pinhole 3D projection."""
        from backend.vision.calibration import HomographyCalibrator, PinholeCalibrator

        # 1. Homography 4-point mapping
        img_pts = [(0.0, 0.0), (640.0, 0.0), (640.0, 460.0), (0.0, 460.0)]
        world_pts = [(-50.0, 100.0), (50.0, 100.0), (50.0, 10.0), (-50.0, 10.0)]
        homo = HomographyCalibrator(img_pts, world_pts)
        self.assertTrue(homo.is_calibrated)

        # Transform center pixel (320, 230)
        world_x, world_y = homo.pixel_to_world(320.0, 230.0)
        self.assertAlmostEqual(world_x, 0.0, delta=2.0)
        self.assertGreater(world_y, 10.0)
        self.assertLess(world_y, 100.0)

        # Reverse transformation
        pix_u, pix_v = homo.world_to_pixel(world_x, world_y)
        self.assertAlmostEqual(pix_u, 320.0, delta=5.0)
        self.assertAlmostEqual(pix_v, 230.0, delta=5.0)

        # 2. Pinhole 3D Projection
        pinhole = PinholeCalibrator(focal_length_px=400.0, principal_point=(320.0, 230.0))
        X, Y, Z = pinhole.pixel_to_3d_point(u=320.0, v=150.0, depth_m=50.0)
        self.assertAlmostEqual(X, 0.0, delta=0.1) # Center azimuth
        self.assertEqual(Y, 50.0)                 # Forward range
        self.assertGreater(Z, 0.0)                # Above horizon (positive altitude)

        # Reverse 3D to 2D
        u_proj, v_proj = pinhole.point_3d_to_pixel(X, Y, Z)
        self.assertAlmostEqual(u_proj, 320.0, delta=0.5)
        self.assertAlmostEqual(v_proj, 150.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
