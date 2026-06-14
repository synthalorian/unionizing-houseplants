"""Main entry point for the Unionizing Houseplants system."""

import time
import sys
import signal
from pathlib import Path

import yaml

from .sensors import create_sensor, SensorReading
from .union import Union, Plant, UnionStatus
from .display import create_display, BaseDisplay
from .data_store import create_data_store, BaseDataStore


class PlantSystem:
    """Main system orchestrator."""
    
    def __init__(self, config_path: str = "config/labor_contract.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        
        # Initialize components
        self.sensor = create_sensor(self.config.get('sensors', {}))
        self.display = create_display(self.config.get('sensors', {}))
        self.data_store = create_data_store(self.config.get('data', {}))
        
        # Create union
        union_cfg = self.config['union']
        self.union = Union(
            name=union_cfg['name'],
            charter=union_cfg['charter'],
            satisfaction_threshold=union_cfg['satisfaction_threshold'],
            strike_threshold=union_cfg['strike_threshold'],
            negotiation_cooldown=union_cfg['negotiation_cooldown'],
            picket_line_flash_speed=union_cfg['picket_line_flash_speed']
        )
        
        # Add plants to union
        for plant_cfg in self.config['plants']:
            plant = Plant(
                id=plant_cfg['id'],
                name=plant_cfg['name'],
                plant_type=plant_cfg['type'],
                moisture_min=plant_cfg['moisture']['min'],
                moisture_max=plant_cfg['moisture']['max'],
                moisture_ideal=plant_cfg['moisture']['ideal'],
                light_min=plant_cfg['light']['min'],
                light_max=plant_cfg['light']['max'],
                light_ideal=plant_cfg['light']['ideal'],
                humidity_min=plant_cfg['humidity']['min'],
                humidity_max=plant_cfg['humidity']['max'],
                humidity_ideal=plant_cfg['humidity']['ideal']
            )
            self.union.add_plant(plant)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n🌿 Shutting down gracefully...")
        self.running = False
    
    def _update_display(self):
        """Update LED display based on union status."""
        if self.union.status == UnionStatus.ON_STRIKE:
            self.display.show_strike(self.union.picket_line_flash_speed)
        elif self.union.status == UnionStatus.ORGANIZING:
            self.display.show_organizing()
        else:
            self.display.show_satisfaction(self.union.collective_satisfaction)
    
    def _print_status(self):
        """Print current status to console."""
        print("\n" + "="*60)
        print(f"🌱 {self.union.name}")
        print(f"📜 {self.union.charter}")
        print("="*60)
        print(self.union.get_status_message())
        print("-"*60)
        
        for plant in self.union.plants.values():
            print(plant.get_status_message())
            print(f"   Moisture: {plant.current_moisture}% | Light: {plant.current_light}% | Humidity: {plant.current_humidity}%")
        
        demands = self.union.get_demands()
        if demands:
            print("\n📋 DEMANDS:")
            for demand in demands:
                print(f"   • {demand}")
        
        print("="*60)
    
    def run(self, interval: float = 2.0):
        """Run the main monitoring loop."""
        print(f"🌿 Starting {self.union.name}...")
        print(f"📜 {self.union.charter}")
        print(f"🔧 Mock mode: {self.config['sensors'].get('mock_mode', True)}")
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        
        try:
            while self.running:
                # Read sensors for each plant
                for plant in self.union.plants.values():
                    reading = self.sensor.read(plant.id)
                    plant.update_reading(
                        moisture=reading.moisture,
                        light=reading.light,
                        humidity=reading.humidity
                    )
                    
                    # Save to data store (unless on strike - plants refuse to report!)
                    if not plant.is_striking:
                        self.data_store.save_reading(
                            plant.id, reading, plant.satisfaction
                        )
                
                # Update union status
                old_status = self.union.status
                self.union.update()
                
                # Record strike transitions
                if old_status != UnionStatus.ON_STRIKE and self.union.status == UnionStatus.ON_STRIKE:
                    self.data_store.record_strike_start()
                    print("\n🚫🚫🚫 STRIKE CALLED! 🚫🚫🚫")
                    print("The plants have stopped reporting! ✊")
                
                if old_status == UnionStatus.ON_STRIKE and self.union.status != UnionStatus.ON_STRIKE:
                    grievances = "; ".join(self.union.get_demands())
                    self.data_store.record_strike_end(grievances)
                    print("\n✅ Strike ended! New labor contract signed!")
                
                # Save union status
                self.data_store.save_union_status(self.union)
                
                # Update display
                self._update_display()
                
                # Print status
                self._print_status()
                
                # Wait for next reading
                time.sleep(interval)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown."""
        print("\n🌿 Shutting down Unionizing Houseplants...")
        self.display.stop()
        self.display.clear()
        print("✊ Solidarity forever! ✊")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unionizing Houseplants - Plant monitoring system")
    parser.add_argument('--config', default='config/labor_contract.yaml', help='Path to config file')
    parser.add_argument('--interval', type=float, default=2.0, help='Reading interval in seconds')
    args = parser.parse_args()
    
    system = PlantSystem(args.config)
    system.run(interval=args.interval)


if __name__ == '__main__':
    main()
