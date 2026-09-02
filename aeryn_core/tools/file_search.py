"""File Search tool — search files by name pattern."""

import os
import fnmatch
from typing import List


class FileSearchTool:
    """Search for files by name pattern."""
    
    def execute(self, pattern: str, directory: str = ".") -> dict:
        """Search files matching glob pattern."""
        try:
            matches = []
            for root, dirs, files in os.walk(directory):
                # Skip hidden dirs and common non-project dirs
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.git')]
                
                for filename in fnmatch.filter(files, pattern):
                    full_path = os.path.join(root, filename)
                    matches.append(full_path)
            
            return {"matches": matches, "count": len(matches), "pattern": pattern, "directory": directory}
        except Exception as e:
            return {"error": str(e)}


file_search_tool = FileSearchTool()
