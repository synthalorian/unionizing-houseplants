"""LED picket line display module."""

import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Optional
from enum import Enum


class PicketColor(Enum):
    """Colors for the picket line."""
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    OFF = (0, 0, 0)


class BaseDisplay(ABC):
    """Abstract base class for LED displays."""
    
    @abstractmethod
    def show_satisfaction(self, satisfaction: float):
        """Display satisfaction level."""
        pass
    
    @abstractmethod
    def show_strike(self, flash_speed: float = 0.5):
        """Display strike picket line."""
        pass
    
    @abstractmethod
    def show_organizing(self):
        """Display organizing mode."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear the display."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop any running animations."""
        pass


class MockDisplay(BaseDisplay):
    """Mock LED display for testing without hardware.
    
    Prints what the LEDs would show to stdout.
    """
    
    def __init__(self, led_count: int = 8):
        self.led_count = led_count
        self._current_colors = [PicketColor.OFF] * led_count
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_animation = False
    
    def show_satisfaction(self, satisfaction: float):
        """Show satisfaction as a color gradient."""
        self._stop_animation = True
        if satisfaction >= 80:
            color = PicketColor.GREEN
        elif satisfaction >= 60:
            color = PicketColor.YELLOW
        else:
            color = PicketColor.RED
        
        self._current_colors = [color] * self.led_count
        self._print_display(f"Satisfaction: {satisfaction}%")
    
    def show_strike(self, flash_speed: float = 0.5):
        """Show flashing picket line."""
        self._stop_animation = True
        time.sleep(0.1)
        self._stop_animation = False
        
        def animate():
            toggle = False
            while not self._stop_animation:
                if toggle:
                    self._current_colors = [PicketColor.RED] * self.led_count
                else:
                    self._current_colors = [PicketColor.YELLOW] * self.led_count
                toggle = not toggle
                self._print_display("🪧 ON STRIKE! 🪧")
                time.sleep(flash_speed)
        
        self._animation_thread = threading.Thread(target=animate, daemon=True)
        self._animation_thread.start()
    
    def show_organizing(self):
        """Show organizing mode (chasing yellow)."""
        self._stop_animation = True
        time.sleep(0.1)
        self._stop_animation = False
        
        def animate():
            pos = 0
            while not self._stop_animation:
                colors = [PicketColor.OFF] * self.led_count
                colors[pos] = PicketColor.YELLOW
                self._current_colors = colors
                pos = (pos + 1) % self.led_count
                self._print_display("📢 ORGANIZING 📢")
                time.sleep(0.3)
        
        self._animation_thread = threading.Thread(target=animate, daemon=True)
        self._animation_thread.start()
    
    def clear(self):
        """Clear the display."""
        self._stop_animation = True
        self._current_colors = [PicketColor.OFF] * self.led_count
        self._print_display("Cleared")
    
    def stop(self):
        """Stop animations."""
        self._stop_animation = True
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)
    
    def _print_display(self, status: str):
        """Print the current LED state."""
        color_strs = []
        for c in self._current_colors:
            if c == PicketColor.RED:
                color_strs.append("🔴")
            elif c == PicketColor.YELLOW:
                color_strs.append("🟡")
            elif c == PicketColor.GREEN:
                color_strs.append("🟢")
            else:
                color_strs.append("⚫")
        print(f"[LED] {' '.join(color_strs)} | {status}")


class NeoPixelDisplay(BaseDisplay):
    """Real NeoPixel LED display for Raspberry Pi."""
    
    def __init__(self, pin: int = 18, count: int = 8, brightness: float = 0.5):
        self.count = count
        self._brightness = brightness
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_animation = False
        
        try:
            import board
            import neopixel
            self._pixels = neopixel.NeoPixel(
                getattr(board, f'D{pin}'), count, 
                brightness=brightness, auto_write=False
            )
            self._has_hardware = True
        except ImportError:
            print("Warning: NeoPixel libraries not available. Using mock display.")
            self._has_hardware = False
            self._mock = MockDisplay(count)
    
    def show_satisfaction(self, satisfaction: float):
        if not self._has_hardware:
            return self._mock.show_satisfaction(satisfaction)
        
        self._stop_animation = True
        if satisfaction >= 80:
            color = PicketColor.GREEN.value
        elif satisfaction >= 60:
            color = PicketColor.YELLOW.value
        else:
            color = PicketColor.RED.value
        
        self._pixels.fill(color)
        self._pixels.show()
    
    def show_strike(self, flash_speed: float = 0.5):
        if not self._has_hardware:
            return self._mock.show_strike(flash_speed)
        
        self._stop_animation = True
        time.sleep(0.1)
        self._stop_animation = False
        
        def animate():
            toggle = False
            while not self._stop_animation:
                if toggle:
                    self._pixels.fill(PicketColor.RED.value)
                else:
                    self._pixels.fill(PicketColor.YELLOW.value)
                self._pixels.show()
                toggle = not toggle
                time.sleep(flash_speed)
        
        self._animation_thread = threading.Thread(target=animate, daemon=True)
        self._animation_thread.start()
    
    def show_organizing(self):
        if not self._has_hardware:
            return self._mock.show_organizing()
        
        self._stop_animation = True
        time.sleep(0.1)
        self._stop_animation = False
        
        def animate():
            pos = 0
            while not self._stop_animation:
                self._pixels.fill(PicketColor.OFF.value)
                self._pixels[pos] = PicketColor.YELLOW.value
                self._pixels.show()
                pos = (pos + 1) % self.count
                time.sleep(0.3)
        
        self._animation_thread = threading.Thread(target=animate, daemon=True)
        self._animation_thread.start()
    
    def clear(self):
        if not self._has_hardware:
            return self._mock.clear()
        
        self._stop_animation = True
        self._pixels.fill(PicketColor.OFF.value)
        self._pixels.show()
    
    def stop(self):
        if not self._has_hardware:
            return self._mock.stop()
        
        self._stop_animation = True
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)
        self.clear()


def create_display(config: Dict) -> BaseDisplay:
    """Factory function to create appropriate display."""
    if config.get('mock_mode', True):
        return MockDisplay(config.get('neopixel', {}).get('count', 8))
    
    neopixel_cfg = config.get('neopixel', {})
    return NeoPixelDisplay(
        pin=neopixel_cfg.get('pin', 18),
        count=neopixel_cfg.get('count', 8),
        brightness=neopixel_cfg.get('brightness', 0.5)
    )
