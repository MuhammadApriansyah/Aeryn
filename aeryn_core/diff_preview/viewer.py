#!/usr/bin/env python3
"""Diff Preview — Lihat perubahan sebelum apply."""
from typing import Dict, List

class DiffPreview:
    def generate_diff(self, old_files: Dict, new_files: Dict) -> List[Dict]:
        diffs = []
        
        # Check new files
        for filepath, content in new_files.items():
            if filepath not in old_files:
                diffs.append({"type": "new", "file": filepath, "content": content})
            elif old_files[filepath] != content:
                diffs.append({"type": "modified", "file": filepath, "content": content})
        
        # Check deleted files
        for filepath in old_files:
            if filepath not in new_files:
                diffs.append({"type": "deleted", "file": filepath})
        
        return diffs
    
    def display_diff(self, diffs: List[Dict]) -> str:
        if not diffs:
            return "Tidak ada perubahan."
        
        output = ["\n📋 CHANGES:", "=" * 40]
        
        for diff in diffs:
            if diff["type"] == "new":
                output.append(f"  + NEW: {diff['file']}")
            elif diff["type"] == "modified":
                output.append(f"  ~ MOD: {diff['file']}")
            elif diff["type"] == "deleted":
                output.append(f"  - DEL: {diff['file']}")
        
        output.append("=" * 40)
        return "\n".join(output)

diff_preview = DiffPreview()
