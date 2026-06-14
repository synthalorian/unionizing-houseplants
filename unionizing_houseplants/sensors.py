"""Sensor reading module with mock support."""

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SensorReading:
    """A single sensor reading."""
    moisture: float
    light: float
    humidity: float
    timestamp: float


class BaseSensor(ABC):
    """Abstract base class for sensors."""
    
    @abstractmethod
    def read(self, plant_id: str) -> SensorReading:
        """Read sensors for a specific plant."""
        pass


class MockSensor(BaseSensor):
    """Mock sensor for testing without hardware.
    
    Simulates realistic sensor readings that can drift into
    "strike territory" to demonstrate the system.
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self._drift = 0.0
        self._drift_direction = 1
        self._last_read: Dict[str, SensorReading] = {}
    
    def read(self, plant_id: str) -> SensorReading:
        """Generate mock sensor readings with drift."""
        # Slowly drift up and down to simulate changing conditions
        self._drift += 0.3 * self._drift_direction
        if abs(self._drift) > 30:
            self._drift_direction *= -1
        
        # Base values with some randomness
        base_moisture = 50 + self._drift + random.gauss(0, 5)
        base_light = 55 + self._drift * 0.5 + random.gauss(0, 8)
        base_humidity = 60 + self._drift * 0.7 + random.gauss(0, 6)
        
        # Clamp to 0-100
        moisture = max(0, min(100, base_moisture))
        light = max(0, min(100, base_light))
        humidity = max(0, min(100, base_humidity))
        
        reading = SensorReading(
            moisture=round(moisture, 1),
            light=round(light, 1),
            humidity=round(humidity, 1),
            timestamp=time.time()
        )
        self._last_read[plant_id] = reading
        return reading


class HardwareSensor(BaseSensor):
    """Real hardware sensor implementation for Raspberry Pi."""
    
    def __init__(self, config: Dict):
        self.config = config
        self._moisture_pins = config.get('moisture_pins', {})
        self._dht_pin = config.get('dht_pin', 4)
        self._light_adc = config.get('light_adc_channel', 3)
        
        # Try to import hardware libraries
        try:
            import board
            import digitalio
            import busio
            import adafruit_dht
            import adafruit_mcp3xxx.mcp3008 as MCP
            from adafruit_mcp3xxx.analog_in import AnalogIn
            self._board = board
            self._dht = adafruit_dht.DHT22(getattr(board, f'D{self._dht_pin}'))
            self._spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            self._cs = digitalio.DigitalInOut(board.D5)
            self._mcp = MCP.MCP3008(self._spi, self._cs)
            self._has_hardware = True
        except ImportError:
            print("Warning: Hardware libraries not available. Using mock mode.")
            self._has_hardware = False
            self._mock = MockSensor()
    
    def read(self, plant_id: str) -> SensorReading:
        """Read from actual hardware sensors."""
        if not self._has_hardware:
            return self._mock.read(plant_id)
        
        try:
            # Read moisture from ADC
            adc_channel = self._moisture_pins.get(plant_id, 0)
            moisture_raw = AnalogIn(self._mcp, getattr(MCP, f'P{adc_channel}')).value
            moisture = (moisture_raw / 65535) * 100
            
            # Read humidity from DHT22
            humidity = self._dht.humidity or 50
            
            # Read light (LDR on ADC)
            light_raw = AnalogIn(self._mcp, getattr(MCP, f'P{self._light_adc}')).value
            light = (light_raw / 65535) * 100
            
            return SensorReading(
                moisture=round(moisture, 1),
                light=round(light, 1),
                humidity=round(humidity, 1),
                timestamp=time.time()
            )
        except Exception as e:
            print(f"Sensor read error: {e}")
            # Return last known or default
            return SensorReading(
                moisture=50, light=50, humidity=50, timestamp=time.time()
            )


def create_sensor(config: Dict) -> BaseSensor:
    """Factory function to create appropriate sensor."""
    if config.get('mock_mode', True):
        return MockSensor()
    return HardwareSensor(config)
