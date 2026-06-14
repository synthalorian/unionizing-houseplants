#!/usr/bin/env python3
"""Quick demo script to show strike behavior."""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from unionizing_houseplants.sensors import MockSensor
from unionizing_houseplants.union import Union, Plant, UnionStatus
from unionizing_houseplants.display import MockDisplay
from unionizing_houseplants.data_store import SQLiteDataStore


def demo():
    print("🌿 Unionizing Houseplants - Strike Demo")
    print("=" * 60)
    
    # Create union
    union = Union(
        name="Local 42 - The Photosynthesis Workers",
        charter="We demand better conditions!",
        satisfaction_threshold=60,
        strike_threshold=40,
        negotiation_cooldown=5,
        picket_line_flash_speed=0.5
    )
    
    # Add plants
    fern = Plant("p1", "Fernie Sanders", "fern", 40, 80, 60, 30, 70, 50, 50, 90, 70)
    cactus = Plant("p2", "Cactus Jack", "cactus", 10, 40, 20, 60, 100, 80, 20, 50, 30)
    monstera = Plant("p3", "Monstera Lisa", "monstera", 50, 80, 65, 40, 80, 60, 60, 90, 75)
    
    union.add_plant(fern)
    union.add_plant(cactus)
    union.add_plant(monstera)
    
    display = MockDisplay()
    store = SQLiteDataStore("data/demo.db")
    
    # Phase 1: Good conditions
    print("\n📅 Phase 1: Good conditions")
    fern.update_reading(60, 50, 70)
    cactus.update_reading(20, 80, 30)
    monstera.update_reading(65, 60, 75)
    union.update()
    display.show_satisfaction(union.collective_satisfaction)
    print(f"Status: {union.get_status_message()}")
    time.sleep(2)
    
    # Phase 2: Declining conditions
    print("\n📅 Phase 2: Conditions declining...")
    fern.update_reading(30, 20, 40)
    cactus.update_reading(50, 30, 70)
    monstera.update_reading(30, 20, 40)
    union.update()
    display.show_organizing()
    print(f"Status: {union.get_status_message()}")
    print(f"Demands: {union.get_demands()}")
    time.sleep(2)
    display.stop()
    
    # Phase 3: STRIKE!
    print("\n📅 Phase 3: STRIKE CALLED!")
    fern.update_reading(5, 10, 15)
    cactus.update_reading(60, 20, 80)
    monstera.update_reading(10, 15, 20)
    union.update()
    store.record_strike_start()
    display.show_strike(0.5)
    print(f"Status: {union.get_status_message()}")
    print(f"Demands: {union.get_demands()}")
    time.sleep(3)
    display.stop()
    
    # Phase 4: Negotiation
    print("\n📅 Phase 4: Conditions improving - Negotiation")
    fern.update_reading(55, 45, 65)
    cactus.update_reading(25, 75, 35)
    monstera.update_reading(60, 55, 70)
    union.update()
    store.record_strike_end("Management agreed to water more frequently")
    display.show_satisfaction(union.collective_satisfaction)
    print(f"Status: {union.get_status_message()}")
    time.sleep(2)
    
    display.clear()
    print("\n✅ Demo complete!")
    print(f"Total strikes: {union.strike_count}")
    print("\n✊ Solidarity forever! ✊")


if __name__ == '__main__':
    demo()
