"""File Read tool — read file contents."""

import os


class FileReadTool:
    """Read file contents."""
    
    def execute(self, path: str) -> dict:
        """Read file and return content."""
        try:
            if not os.path.exists(path):
                return {"error": f"File not found: {path}"}
            
            if not os.path.isfile(path):
                return {"error": f"Not a file: {path}"}
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return {"content": content, "path": path, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}


file_read_tool = FileReadTool()
