"""File Write tool — write file contents."""

import os


class FileWriteTool:
    """Write content to a file."""
    
    def execute(self, path: str, content: str) -> dict:
        """Write content to file (creates or overwrites)."""
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"status": "ok", "path": path, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}


file_write_tool = FileWriteTool()
