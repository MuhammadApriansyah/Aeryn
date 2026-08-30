#!/usr/bin/env python3
"""Debug Mode — Verbose logging for troubleshooting."""
import os, sys, logging, time
from typing import Dict

class DebugMode:
    def __init__(self, enabled=False, log_file="aeryn_debug.log"):
        self.enabled = enabled
        self.log_file = log_file
        self._logs = []
    
    def enable(self):
        self.enabled = True
        logging.basicConfig(level=logging.DEBUG, filename=self.log_file, format='%(asctime)s [%(levelname)s] %(message)s')
    
    def disable(self):
        self.enabled = False
    
    def log(self, level, message):
        timestamp = time.strftime('%H:%M:%S')
        entry = f"[{timestamp}] {level}: {message}"
        self._logs.append(entry)
        if self.enabled:
            print(entry, file=sys.stderr)
    
    def info(self, msg): self.log("INFO", msg)
    def warn(self, msg): self.log("WARN", msg)
    def error(self, msg): self.log("ERROR", msg)
    def debug(self, msg): self.log("DEBUG", msg)
    
    def get_logs(self): return self._logs

debug_mode = DebugMode()
