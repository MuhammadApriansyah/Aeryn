#!/usr/bin/env python3
"""Undo Manager — Revert last action."""
import os
import json
import time
import shutil
from typing import Dict, Optional

class UndoManager:
    def __init__(self):
        self._history_file = os.path.expanduser("~/.aerundo_history.json")
        self._max_history = 50
    
    def record(self, action: str, files_created: list, directories_created: list):
        history = self._load_history()
        entry = {
            "timestamp": time.time(),
            "action": action,
            "files": files_created,
            "dirs": directories_created,
        }
        history.append(entry)
        if len(history) > self._max_history:
            history = history[-self._max_history:]
        self._save_history(history)
    
    def can_undo(self) -> bool:
        history = self._load_history()
        return len(history) > 0
    
    def get_last_action(self) -> Optional[Dict]:
        history = self._load_history()
        return history[-1] if history else None
    
    def undo(self) -> Dict:
        if not self.can_undo():
            return {"error": "Nothing to undo"}
        
        history = self._load_history()
        last = history.pop()
        self._save_history(history)
        
        files_removed = 0
        dirs_removed = 0
        
        for filepath in last.get("files", []):
            if os.path.exists(filepath):
                os.remove(filepath)
                files_removed += 1
        
        for dirpath in last.get("dirs", []):
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath, ignore_errors=True)
                dirs_removed += 1
        
        return {
            "action": last["action"],
            "files_removed": files_removed,
            "dirs_removed": dirs_removed,
        }
    
    def _load_history(self):
        if os.path.exists(self._history_file):
            with open(self._history_file) as f:
                return json.load(f)
        return []
    
    def _save_history(self, history):
        with open(self._history_file, "w") as f:
            json.dump(history, f, indent=2)

undo_manager = UndoManager()
