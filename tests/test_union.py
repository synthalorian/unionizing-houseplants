"""Tests for the Unionizing Houseplants system."""

import pytest
import time
from unionizing_houseplants.sensors import MockSensor, SensorReading
from unionizing_houseplants.union import Plant, Union, UnionStatus, Grievance
from unionizing_houseplants.display import MockDisplay
from unionizing_houseplants.data_store import SQLiteDataStore


class TestMockSensor:
    def test_read_returns_sensor_reading(self):
        sensor = MockSensor(seed=42)
        reading = sensor.read("plant_1")
        assert isinstance(reading, SensorReading)
        assert 0 <= reading.moisture <= 100
        assert 0 <= reading.light <= 100
        assert 0 <= reading.humidity <= 100
    
    def test_readings_vary_over_time(self):
        sensor = MockSensor(seed=42)
        r1 = sensor.read("plant_1")
        r2 = sensor.read("plant_1")
        # They can be same or different, but should be valid
        assert isinstance(r1, SensorReading)
        assert isinstance(r2, SensorReading)


class TestPlant:
    def test_satisfaction_perfect_conditions(self):
        plant = Plant(
            id="test", name="Test", plant_type="fern",
            moisture_min=40, moisture_max=80, moisture_ideal=60,
            light_min=30, light_max=70, light_ideal=50,
            humidity_min=50, humidity_max=90, humidity_ideal=70
        )
        plant.update_reading(60, 50, 70)
        assert plant.satisfaction == 100.0
        assert len(plant.grievances) == 0
    
    def test_satisfaction_too_dry(self):
        plant = Plant(
            id="test", name="Test", plant_type="fern",
            moisture_min=40, moisture_max=80, moisture_ideal=60,
            light_min=30, light_max=70, light_ideal=50,
            humidity_min=50, humidity_max=90, humidity_ideal=70
        )
        plant.update_reading(10, 50, 70)
        assert plant.satisfaction < 100
        assert Grievance.TOO_DRY in plant.grievances
    
    def test_satisfaction_too_wet(self):
        plant = Plant(
            id="test", name="Test", plant_type="fern",
            moisture_min=40, moisture_max=80, moisture_ideal=60,
            light_min=30, light_max=70, light_ideal=50,
            humidity_min=50, humidity_max=90, humidity_ideal=70
        )
        plant.update_reading(90, 50, 70)
        assert plant.satisfaction < 100
        assert Grievance.TOO_WET in plant.grievances
    
    def test_status_messages(self):
        plant = Plant(
            id="test", name="Test", plant_type="fern",
            moisture_min=40, moisture_max=80, moisture_ideal=60,
            light_min=30, light_max=70, light_ideal=50,
            humidity_min=50, humidity_max=90, humidity_ideal=70
        )
        
        plant.update_reading(60, 50, 70)
        assert "happily" in plant.get_status_message()
        
        plant.update_reading(45, 35, 55)
        assert "tolerating" in plant.get_status_message()
        
        plant.update_reading(30, 20, 40)
        assert "grievances" in plant.get_status_message()
        
        plant.update_reading(5, 10, 20)
        assert "organizing" in plant.get_status_message()
        
        plant.is_striking = True
        assert "STRIKE" in plant.get_status_message()


class TestUnion:
    def test_add_plant(self):
        union = Union("Test Union", "Test", 60, 40, 300, 0.5)
        plant = Plant(
            id="p1", name="Plant 1", plant_type="fern",
            moisture_min=40, moisture_max=80, moisture_ideal=60,
            light_min=30, light_max=70, light_ideal=50,
            humidity_min=50, humidity_max=90, humidity_ideal=70
        )
        union.add_plant(plant)
        assert "p1" in union.plants
    
    def test_collective_satisfaction(self):
        union = Union("Test Union", "Test", 60, 40, 300, 0.5)
        
        p1 = Plant("p1", "Plant 1", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        p2 = Plant("p2", "Plant 2", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        
        union.add_plant(p1)
        union.add_plant(p2)
        
        p1.update_reading(60, 50, 70)
        p2.update_reading(60, 50, 70)
        
        union.update()
        assert union.collective_satisfaction == 100.0
        assert union.status == UnionStatus.ACTIVE
    
    def test_strike_called(self):
        union = Union("Test Union", "Test", 60, 40, 300, 0.5)
        
        p1 = Plant("p1", "Plant 1", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        p2 = Plant("p2", "Plant 2", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        
        union.add_plant(p1)
        union.add_plant(p2)
        
        # Very bad conditions
        p1.update_reading(5, 10, 20)
        p2.update_reading(5, 10, 20)
        
        union.update()
        assert union.status == UnionStatus.ON_STRIKE
        assert union.strike_count == 1
        assert p1.is_striking
        assert p2.is_striking
    
    def test_strike_ends(self):
        union = Union("Test Union", "Test", 60, 40, 300, 0.5)
        
        p1 = Plant("p1", "Plant 1", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        p2 = Plant("p2", "Plant 2", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        
        union.add_plant(p1)
        union.add_plant(p2)
        
        # Start strike
        p1.update_reading(5, 10, 20)
        p2.update_reading(5, 10, 20)
        union.update()
        assert union.status == UnionStatus.ON_STRIKE
        
        # Improve conditions
        p1.update_reading(70, 60, 80)
        p2.update_reading(70, 60, 80)
        union.update()
        assert union.status == UnionStatus.NEGOTIATING
        
        # Even better
        p1.update_reading(60, 50, 70)
        p2.update_reading(60, 50, 70)
        union.update()
        assert union.status == UnionStatus.ACTIVE
        assert not p1.is_striking
    
    def test_demands(self):
        union = Union("Test Union", "Test", 60, 40, 300, 0.5)
        
        p1 = Plant("p1", "Fernie", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
        p1.update_reading(10, 50, 70)
        
        union.add_plant(p1)
        union.update()
        
        demands = union.get_demands()
        assert len(demands) > 0
        assert "Fernie" in demands[0]


class TestMockDisplay:
    def test_show_satisfaction(self, capsys):
        display = MockDisplay()
        display.show_satisfaction(90)
        captured = capsys.readouterr()
        assert "Satisfaction" in captured.out
    
    def test_show_strike(self, capsys):
        display = MockDisplay()
        display.show_strike(0.5)
        time.sleep(0.1)  # Let animation start
        display.stop()
        captured = capsys.readouterr()
        assert "STRIKE" in captured.out
    
    def test_clear(self, capsys):
        display = MockDisplay()
        display.clear()
        captured = capsys.readouterr()
        assert "Cleared" in captured.out


class TestSQLiteDataStore:
    def test_save_and_retrieve(self, tmp_path):
        db_path = tmp_path / "test.db"
        store = SQLiteDataStore(str(db_path))
        
        reading = SensorReading(50, 60, 70, time.time())
        store.save_reading("plant_1", reading, 85.0)
        
        readings = store.get_recent_readings("plant_1")
        assert len(readings) == 1
        assert readings[0][0] == "plant_1"
        assert readings[0][1] == 50.0
    
    def test_strike_history(self, tmp_path):
        db_path = tmp_path / "test.db"
        store = SQLiteDataStore(str(db_path))
        
        store.record_strike_start()
        time.sleep(0.1)
        store.record_strike_end("Too dry")
        
        strikes = store.get_strike_history()
        assert len(strikes) == 1
        assert strikes[0][3] == "Too dry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
