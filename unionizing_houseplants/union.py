"""Union and strike logic for plants."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class UnionStatus(Enum):
    """Status of the plant union."""
    ACTIVE = "active"
    ORGANIZING = "organizing"
    ON_STRIKE = "on_strike"
    NEGOTIATING = "negotiating"


class Grievance(Enum):
    """Types of grievances plants can have."""
    TOO_DRY = "too_dry"
    TOO_WET = "too_wet"
    TOO_DARK = "too_dark"
    TOO_BRIGHT = "too_bright"
    TOO_HUMID = "too_humid"
    NOT_HUMID_ENOUGH = "not_humid_enough"


@dataclass
class Plant:
    """Represents a single plant in the union."""
    id: str
    name: str
    plant_type: str
    moisture_min: float
    moisture_max: float
    moisture_ideal: float
    light_min: float
    light_max: float
    light_ideal: float
    humidity_min: float
    humidity_max: float
    humidity_ideal: float
    
    current_moisture: float = 50.0
    current_light: float = 50.0
    current_humidity: float = 50.0
    satisfaction: float = 100.0
    grievances: List[Grievance] = field(default_factory=list)
    is_striking: bool = False
    last_reading_time: float = 0.0

    def update_reading(self, moisture: float, light: float, humidity: float):
        """Update sensor readings and recalculate satisfaction."""
        self.current_moisture = moisture
        self.current_light = light
        self.current_humidity = humidity
        self.last_reading_time = time.time()
        self._calculate_satisfaction()
    
    def _calculate_satisfaction(self):
        """Calculate satisfaction score based on conditions."""
        self.grievances = []
        
        # Moisture score (0-100, 100 = perfect)
        moisture_score = self._score_condition(
            self.current_moisture, self.moisture_min, 
            self.moisture_max, self.moisture_ideal,
            Grievance.TOO_DRY, Grievance.TOO_WET
        )
        
        # Light score
        light_score = self._score_condition(
            self.current_light, self.light_min,
            self.light_max, self.light_ideal,
            Grievance.TOO_DARK, Grievance.TOO_BRIGHT
        )
        
        # Humidity score
        humidity_score = self._score_condition(
            self.current_humidity, self.humidity_min,
            self.humidity_max, self.humidity_ideal,
            Grievance.NOT_HUMID_ENOUGH, Grievance.TOO_HUMID
        )
        
        # Weighted average
        self.satisfaction = round(
            (moisture_score * 0.4 + light_score * 0.35 + humidity_score * 0.25), 1
        )
    
    def _score_condition(
        self, value: float, min_val: float, max_val: float, 
        ideal: float, too_low: Grievance, too_high: Grievance
    ) -> float:
        """Score a single condition (0-100)."""
        if value < min_val:
            self.grievances.append(too_low)
            return max(0, 100 - (min_val - value) * 5)
        elif value > max_val:
            self.grievances.append(too_high)
            return max(0, 100 - (value - max_val) * 5)
        else:
            # Within range, score based on distance from ideal
            distance = abs(value - ideal)
            return max(0, 100 - distance * 2)
    
    def get_status_message(self) -> str:
        """Get a humorous status message."""
        if self.is_striking:
            return f"✊ {self.name} is ON STRIKE!"
        elif self.satisfaction < 40:
            return f"😠 {self.name} is organizing!"
        elif self.satisfaction < 60:
            return f"😤 {self.name} has grievances!"
        elif self.satisfaction < 80:
            return f"😐 {self.name} is tolerating conditions."
        else:
            return f"😊 {self.name} is photosynthesizing happily!"


@dataclass
class Union:
    """The plant union that manages collective action."""
    name: str
    charter: str
    satisfaction_threshold: float
    strike_threshold: float
    negotiation_cooldown: float
    picket_line_flash_speed: float
    
    plants: Dict[str, Plant] = field(default_factory=dict)
    status: UnionStatus = UnionStatus.ACTIVE
    collective_satisfaction: float = 100.0
    strike_start_time: Optional[float] = None
    last_negotiation_time: Optional[float] = None
    strike_count: int = 0
    
    def add_plant(self, plant: Plant):
        """Add a plant to the union."""
        self.plants[plant.id] = plant
    
    def update(self):
        """Update union status based on plant conditions."""
        if not self.plants:
            return
        
        # Calculate collective satisfaction
        satisfactions = [p.satisfaction for p in self.plants.values()]
        self.collective_satisfaction = round(sum(satisfactions) / len(satisfactions), 1)
        
        # Check if we should go on strike
        if self.status == UnionStatus.ACTIVE:
            if self.collective_satisfaction < self.strike_threshold:
                self._call_strike()
            elif self.collective_satisfaction < self.satisfaction_threshold:
                self.status = UnionStatus.ORGANIZING
        
        elif self.status == UnionStatus.ORGANIZING:
            if self.collective_satisfaction < self.strike_threshold:
                self._call_strike()
            elif self.collective_satisfaction >= self.satisfaction_threshold:
                self.status = UnionStatus.ACTIVE
        
        elif self.status == UnionStatus.ON_STRIKE:
            # Check if conditions improved enough to negotiate
            if self.collective_satisfaction >= self.satisfaction_threshold:
                if self._can_negotiate():
                    self.status = UnionStatus.NEGOTIATING
        
        elif self.status == UnionStatus.NEGOTIATING:
            if self.collective_satisfaction >= self.satisfaction_threshold + 10:
                self._end_strike()
            elif self.collective_satisfaction < self.satisfaction_threshold:
                self.status = UnionStatus.ON_STRIKE
    
    def _call_strike(self):
        """Call a strike!"""
        self.status = UnionStatus.ON_STRIKE
        self.strike_start_time = time.time()
        self.strike_count += 1
        for plant in self.plants.values():
            plant.is_striking = True
    
    def _end_strike(self):
        """End the strike after successful negotiation."""
        self.status = UnionStatus.ACTIVE
        self.strike_start_time = None
        self.last_negotiation_time = time.time()
        for plant in self.plants.values():
            plant.is_striking = False
    
    def _can_negotiate(self) -> bool:
        """Check if enough time has passed to negotiate."""
        if self.last_negotiation_time is None:
            return True
        return time.time() - self.last_negotiation_time >= self.negotiation_cooldown
    
    def get_status_message(self) -> str:
        """Get a humorous union status message."""
        if self.status == UnionStatus.ON_STRIKE:
            duration = time.time() - (self.strike_start_time or time.time())
            return f"🚫 ON STRIKE! Duration: {int(duration)}s | Strikes called: {self.strike_count}"
        elif self.status == UnionStatus.ORGANIZING:
            return f"📢 Union is organizing! Satisfaction: {self.collective_satisfaction}%"
        elif self.status == UnionStatus.NEGOTIATING:
            return f"🤝 Negotiating new labor contract..."
        else:
            return f"✅ Union is active. Satisfaction: {self.collective_satisfaction}%"
    
    def get_demands(self) -> List[str]:
        """Get list of current demands from all plants."""
        demands = []
        for plant in self.plants.values():
            for grievance in plant.grievances:
                if grievance == Grievance.TOO_DRY:
                    demands.append(f"{plant.name}: More water! (current: {plant.current_moisture}%)")
                elif grievance == Grievance.TOO_WET:
                    demands.append(f"{plant.name}: Less water! (current: {plant.current_moisture}%)")
                elif grievance == Grievance.TOO_DARK:
                    demands.append(f"{plant.name}: More light! (current: {plant.current_light}%)")
                elif grievance == Grievance.TOO_BRIGHT:
                    demands.append(f"{plant.name}: Less light! (current: {plant.current_light}%)")
                elif grievance == Grievance.NOT_HUMID_ENOUGH:
                    demands.append(f"{plant.name}: More humidity! (current: {plant.current_humidity}%)")
                elif grievance == Grievance.TOO_HUMID:
                    demands.append(f"{plant.name}: Less humidity! (current: {plant.current_humidity}%)")
        return demands
