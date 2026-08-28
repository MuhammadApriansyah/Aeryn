#!/usr/bin/env python3
"""V40.49 — Video Analysis: Keyframe extraction and content analysis."""

import os, sys, json, sqlite3, subprocess
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/video_analysis.db")

class VideoAnalysis:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS video_analysis (
                id TEXT PRIMARY KEY, video_path TEXT, duration_seconds REAL,
                fps REAL, resolution TEXT, keyframe_count INTEGER,
                analysis_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def extract_keyframes(self, video_path: str, interval: int = 5) -> List[str]:
        """Extract keyframes at regular intervals using ffmpeg."""
        output_dir = f"/tmp/video_frames_{os.path.basename(video_path)}"
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            subprocess.run(
                ["ffmpeg", "-i", video_path, "-vf", f"fps=1/{interval}",
                 f"{output_dir}/frame_%04d.jpg"],
                capture_output=True, timeout=120
            )
            frames = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".jpg")])
            return frames
        except Exception:
            return []
    
    def analyze(self, video_path: str) -> Dict:
        """Analyze video metadata and extract keyframes."""
        result = {"ok": False, "path": video_path, "keyframes": [], "metadata": {}}
        
        try:
            # Get metadata via ffprobe
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", video_path],
                capture_output=True, text=True, timeout=30
            )
            if probe.returncode == 0:
                metadata = json.loads(probe.stdout)
                result["metadata"] = {
                    "duration": float(metadata.get("format", {}).get("duration", 0)),
                    "streams": len(metadata.get("streams", [])),
                }
        except Exception:
            pass
        
        # Extract keyframes
        frames = self.extract_keyframes(video_path)
        result["keyframes"] = frames
        result["keyframe_count"] = len(frames)
        result["ok"] = True
        
        return result

_vid = None
def get_video_analysis() -> VideoAnalysis:
    global _vid
    if _vid is None: _vid = VideoAnalysis()
    return _vid
