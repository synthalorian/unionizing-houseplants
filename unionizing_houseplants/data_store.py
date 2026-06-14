"""Data storage module - SQLite and MQTT backends."""

import sqlite3
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

from .sensors import SensorReading
from .union import Plant, Union


class BaseDataStore(ABC):
    """Abstract base class for data storage."""
    
    @abstractmethod
    def save_reading(self, plant_id: str, reading: SensorReading):
        """Save a sensor reading."""
        pass
    
    @abstractmethod
    def save_union_status(self, union: Union):
        """Save union status."""
        pass
    
    @abstractmethod
    def get_recent_readings(self, plant_id: str, limit: int = 10) -> list:
        """Get recent readings for a plant."""
        pass
    
    @abstractmethod
    def get_strike_history(self) -> list:
        """Get strike history."""
        pass


class SQLiteDataStore(BaseDataStore):
    """SQLite-based data storage."""
    
    def __init__(self, db_path: str = "data/plant_union.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id TEXT NOT NULL,
                    moisture REAL,
                    light REAL,
                    humidity REAL,
                    timestamp REAL,
                    satisfaction REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS union_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    collective_satisfaction REAL,
                    strike_count INTEGER,
                    timestamp REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strikes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    grievances TEXT
                )
            """)
            conn.commit()
    
    def save_reading(self, plant_id: str, reading: SensorReading, satisfaction: float = 0.0):
        """Save a sensor reading."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO readings (plant_id, moisture, light, humidity, timestamp, satisfaction) VALUES (?, ?, ?, ?, ?, ?)",
                (plant_id, reading.moisture, reading.light, reading.humidity, reading.timestamp, satisfaction)
            )
            conn.commit()
    
    def save_union_status(self, union: Union):
        """Save union status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO union_status (status, collective_satisfaction, strike_count, timestamp) VALUES (?, ?, ?, ?)",
                (union.status.value, union.collective_satisfaction, union.strike_count, time.time())
            )
            conn.commit()
    
    def record_strike_start(self):
        """Record the start of a strike."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO strikes (start_time, end_time, duration, grievances) VALUES (?, NULL, NULL, ?)",
                (time.time(), "")
            )
            conn.commit()
    
    def record_strike_end(self, grievances: str = ""):
        """Record the end of a strike."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, start_time FROM strikes WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                strike_id, start_time = row
                duration = time.time() - start_time
                conn.execute(
                    "UPDATE strikes SET end_time = ?, duration = ?, grievances = ? WHERE id = ?",
                    (time.time(), duration, grievances, strike_id)
                )
                conn.commit()
    
    def get_recent_readings(self, plant_id: str, limit: int = 10) -> list:
        """Get recent readings for a plant."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT plant_id, moisture, light, humidity, timestamp, satisfaction FROM readings WHERE plant_id = ? ORDER BY timestamp DESC LIMIT ?",
                (plant_id, limit)
            )
            return cursor.fetchall()
    
    def get_strike_history(self) -> list:
        """Get strike history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT start_time, end_time, duration, grievances FROM strikes ORDER BY start_time DESC"
            )
            return cursor.fetchall()


class MQTTDataStore(BaseDataStore):
    """MQTT-based data storage/publishing."""
    
    def __init__(self, broker: str = "localhost", port: int = 1883, topic_prefix: str = "unionizing_houseplants"):
        self.topic_prefix = topic_prefix
        self._client = None
        
        try:
            import paho.mqtt.client as mqtt
            self._client = mqtt.Client()
            self._client.connect(broker, port, 60)
            self._client.loop_start()
            self._has_mqtt = True
        except Exception as e:
            print(f"Warning: MQTT not available ({e}). Falling back to SQLite.")
            self._has_mqtt = False
            self._fallback = SQLiteDataStore()
    
    def save_reading(self, plant_id: str, reading: SensorReading, satisfaction: float = 0.0):
        if not self._has_mqtt:
            return self._fallback.save_reading(plant_id, reading, satisfaction)
        
        payload = {
            "plant_id": plant_id,
            "moisture": reading.moisture,
            "light": reading.light,
            "humidity": reading.humidity,
            "timestamp": reading.timestamp,
            "satisfaction": satisfaction
        }
        self._client.publish(
            f"{self.topic_prefix}/readings/{plant_id}",
            json.dumps(payload)
        )
    
    def save_union_status(self, union: Union):
        if not self._has_mqtt:
            return self._fallback.save_union_status(union)
        
        payload = {
            "status": union.status.value,
            "collective_satisfaction": union.collective_satisfaction,
            "strike_count": union.strike_count,
            "timestamp": time.time()
        }
        self._client.publish(
            f"{self.topic_prefix}/union/status",
            json.dumps(payload)
        )
    
    def get_recent_readings(self, plant_id: str, limit: int = 10) -> list:
        if not self._has_mqtt:
            return self._fallback.get_recent_readings(plant_id, limit)
        return []  # MQTT is pub-only
    
    def get_strike_history(self) -> list:
        if not self._has_mqtt:
            return self._fallback.get_strike_history()
        return []
    
    def __del__(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()


def create_data_store(config: dict) -> BaseDataStore:
    """Factory function to create appropriate data store."""
    backend = config.get('backend', 'sqlite')
    
    if backend == 'mqtt':
        mqtt_cfg = config.get('mqtt', {})
        return MQTTDataStore(
            broker=mqtt_cfg.get('broker', 'localhost'),
            port=mqtt_cfg.get('port', 1883),
            topic_prefix=mqtt_cfg.get('topic_prefix', 'unionizing_houseplants')
        )
    else:
        return SQLiteDataStore(config.get('sqlite_path', 'data/plant_union.db'))
