"""
SMART-SHIELD v3.0 Database & In-Memory Ring Buffer Manager
Handles async persistence of telemetry, targets, cyber events, and audit logs.
Provides an automatic in-memory fallback when external DB is not connected.
"""

import asyncio
import time
import logging
from collections import deque
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SmartShield.DBManager")

class TelemetryRingBuffer:
    """High-speed in-memory circular buffer for 30Hz telemetry data."""
    def __init__(self, max_len: int = 1000):
        self.buffer = deque(maxlen=max_len)
        self.targets_cache: Dict[str, Dict[str, Any]] = {}
        self.cyber_events: deque = deque(maxlen=200)
        self.audit_logs: deque = deque(maxlen=500)

    def record_telemetry(self, telemetry_data: Dict[str, Any]):
        timestamp = time.time()
        telemetry_data["timestamp"] = timestamp
        self.buffer.append(telemetry_data)

        # Update targets cache
        target_id = telemetry_data.get("target_id")
        if target_id:
            if target_id not in self.targets_cache:
                self.targets_cache[target_id] = {
                    "target_id": target_id,
                    "first_detected": timestamp,
                    "last_detected": timestamp,
                    "classification": telemetry_data.get("classification", "Unknown"),
                    "initial_distance_m": telemetry_data.get("distance_m", 0.0),
                    "max_threat_score": telemetry_data.get("threat_score", 0.0),
                    "status": "ACTIVE"
                }
            else:
                target = self.targets_cache[target_id]
                target["last_detected"] = timestamp
                if telemetry_data.get("threat_score", 0.0) > target["max_threat_score"]:
                    target["max_threat_score"] = telemetry_data["threat_score"]

    def log_cyber_event(self, event_data: Dict[str, Any]):
        event_data["timestamp"] = time.time()
        self.cyber_events.append(event_data)
        logger.warning(f"CYBER EVENT LOGGED: {event_data.get('event_type')} - {event_data.get('severity')}")

    def log_audit(self, subsystem: str, message: str, **kwargs):
        log_entry = {
            "timestamp": time.time(),
            "subsystem": subsystem,
            "message": message,
            **kwargs
        }
        self.audit_logs.append(log_entry)
        logger.info(f"[{subsystem}] {message}")

    def get_active_targets(self) -> List[Dict[str, Any]]:
        now = time.time()
        active = []
        for tid, data in list(self.targets_cache.items()):
            # Consider active if seen in last 3 seconds
            if now - data["last_detected"] < 3.0:
                active.append(data)
            else:
                data["status"] = "LOST"
        return active

    def get_recent_cyber_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(self.cyber_events)[-limit:]


import sqlite3
import os
import csv
import io
import json

class DatabaseManager:
    """Async & Local Persistent Database Manager supporting SQLite & PostgreSQL."""
    def __init__(self, dsn: Optional[str] = None, sqlite_path: str = "database/smart_shield.db"):
        self.dsn = dsn
        self.sqlite_path = sqlite_path
        self.ring_buffer = TelemetryRingBuffer()
        self.is_connected = False
        self.use_sqlite = True
        self._pool = None
        self._sqlite_conn = None

    async def initialize(self):
        """Initializes PostgreSQL connection pool if DSN provided, otherwise initializes local SQLite database."""
        if self.dsn:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
                self.is_connected = True
                self.use_sqlite = False
                logger.info("Connected to PostgreSQL/TimescaleDB cluster successfully.")
                return
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed ({e}). Defaulting to Local SQLite Persistent Mode.")
        
        # Initialize Local SQLite database
        try:
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            self._sqlite_conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self._init_sqlite_tables()
            self.use_sqlite = True
            logger.info(f"Local SQLite database initialized at {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite ({e}). Operating in in-memory mode only.")
            self.use_sqlite = False

    def _init_sqlite_tables(self):
        """Creates target_telemetry and cyber_rf_events SQLite tables if not present."""
        if not self._sqlite_conn:
            return
        cur = self._sqlite_conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                target_id TEXT PRIMARY KEY,
                first_detected REAL,
                last_detected REAL,
                classification TEXT,
                initial_distance_m REAL,
                max_threat_score REAL,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS target_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                target_id TEXT,
                x_pos_m REAL,
                y_pos_m REAL,
                z_pos_m REAL,
                distance_m REAL,
                azimuth_deg REAL,
                elevation_deg REAL,
                speed_ms REAL,
                heading_deg REAL,
                optical_confidence REAL,
                radar_snr REAL,
                threat_score REAL,
                threat_level TEXT
            );

            CREATE TABLE IF NOT EXISTS cyber_rf_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                frequency_mhz REAL,
                rssi_dbm REAL,
                noise_floor_delta_db REAL,
                severity TEXT,
                countermeasure_taken TEXT
            );
        """)
        self._sqlite_conn.commit()

    async def save_telemetry(self, telemetry_data: Dict[str, Any]):
        self.ring_buffer.record_telemetry(telemetry_data)
        
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    INSERT INTO target_telemetry (
                        timestamp, target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                        azimuth_deg, elevation_deg, speed_ms, heading_deg,
                        optical_confidence, radar_snr, threat_score, threat_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    telemetry_data["target_id"], telemetry_data["x_pos_m"], telemetry_data["y_pos_m"],
                    telemetry_data.get("z_pos_m", 0.0), telemetry_data["distance_m"], telemetry_data["azimuth_deg"],
                    telemetry_data.get("elevation_deg", 0.0), telemetry_data["speed_ms"], telemetry_data.get("heading_deg", 0.0),
                    telemetry_data["optical_confidence"], telemetry_data["radar_snr"], telemetry_data["threat_score"],
                    telemetry_data["threat_level"]
                ))
                self._sqlite_conn.commit()
            except Exception as e:
                logger.error(f"SQLite telemetry persist failed: {e}")

        elif self.is_connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO target_telemetry (
                            target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                            azimuth_deg, elevation_deg, speed_ms, heading_deg,
                            optical_confidence, radar_snr, threat_score, threat_level
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, 
                    telemetry_data["target_id"], telemetry_data["x_pos_m"], telemetry_data["y_pos_m"],
                    telemetry_data.get("z_pos_m", 0.0), telemetry_data["distance_m"], telemetry_data["azimuth_deg"],
                    telemetry_data.get("elevation_deg", 0.0), telemetry_data["speed_ms"], telemetry_data.get("heading_deg", 0.0),
                    telemetry_data["optical_confidence"], telemetry_data["radar_snr"], telemetry_data["threat_score"],
                    telemetry_data["threat_level"])
            except Exception as e:
                logger.error(f"PostgreSQL telemetry persist failed: {e}")

    async def save_cyber_event(self, event_data: Dict[str, Any]):
        self.ring_buffer.log_cyber_event(event_data)
        
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    INSERT INTO cyber_rf_events (
                        timestamp, event_type, frequency_mhz, rssi_dbm, noise_floor_delta_db,
                        severity, countermeasure_taken
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    event_data["event_type"], event_data.get("frequency_mhz", 2412.0),
                    event_data.get("rssi_dbm", -85.0), event_data.get("delta_db", 0.0),
                    event_data.get("severity", "WARNING"), event_data.get("message", "N/A")
                ))
                self._sqlite_conn.commit()
            except Exception as e:
                logger.error(f"SQLite cyber event persist failed: {e}")

    def get_historical_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent recorded trajectory points for mission playback."""
        if self.use_sqlite and self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                cur.execute("""
                    SELECT timestamp, target_id, x_pos_m, y_pos_m, z_pos_m, distance_m,
                           azimuth_deg, speed_ms, threat_score, threat_level
                    FROM target_telemetry
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cur.fetchall()
                results = []
                for r in reversed(rows):
                    results.append({
                        "timestamp": r[0], "target_id": r[1], "x_m": r[2], "y_m": r[3],
                        "z_m": r[4], "distance_m": r[5], "azimuth_deg": r[6], "speed_ms": r[7],
                        "threat_score": r[8], "threat_level": r[9]
                    })
                return results
            except Exception as e:
                logger.error(f"Failed to query SQLite history: {e}")
        
        # Fallback to ring buffer
        return list(self.ring_buffer.buffer)[-limit:]

    def export_csv_report(self) -> str:
        """Exports recent telemetry & threat scoring as a CSV string."""
        history = self.get_historical_telemetry(limit=500)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Target_ID", "X_m", "Y_m", "Z_m", "Distance_m", "Azimuth_deg", "Speed_ms", "Threat_Score", "Threat_Level"])
        for h in history:
            writer.writerow([
                h.get("timestamp"), h.get("target_id"), h.get("x_m") or h.get("x_pos_m"),
                h.get("y_m") or h.get("y_pos_m"), h.get("z_m") or h.get("z_pos_m", 0.0),
                h.get("distance_m"), h.get("azimuth_deg"), h.get("speed_ms"),
                h.get("threat_score"), h.get("threat_level")
            ])
        return output.getvalue()

    async def close(self):
        if self._sqlite_conn:
            self._sqlite_conn.close()
            logger.info("SQLite database connection closed.")
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL database connection pool closed.")

