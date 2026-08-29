#!/usr/bin/env python3
"""Progress Indicator — Visual feedback during generation."""
import time
import sys
from typing import List

class ProgressIndicator:
    """Show progress during project generation."""
    
    def __init__(self, total_steps: int = 5):
        self.total_steps = total_steps
        self.current_step = 0
    
    def start(self, message: str = "Memulai..."):
        """Show start message."""
        print(f"\n🚀 {message}")
        print("-" * 40)
    
    def step(self, message: str):
        """Show a step."""
        self.current_step += 1
        sys.stdout.write(f"  ✅ {message}")
        sys.stdout.flush()
        time.sleep(0.3)  # Simulate work
        print()
    
    def finish(self, message: str = "Selesai!"):
        """Show finish message."""
        print("-" * 40)
        print(f"🎉 {message}")
        print()

def progress_indicator(total_steps: int = 5):
    """Create a progress indicator."""
    return ProgressIndicator(total_steps)
