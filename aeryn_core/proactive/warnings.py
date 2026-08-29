#!/usr/bin/env python3
"""Proactive Warnings — Check before errors happen."""
import os
import shutil
from typing import Dict, List

class ProactiveWarnings:
    """Detect potential problems before they happen."""
    
    def check_port(self, port: int) -> Dict:
        """Check if port is available."""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            return {"port": port, "available": True}
        except socket.error:
            return {"port": port, "available": False, "message": f"Port {port} sudah dipakai"}
        finally:
            sock.close()
    
    def check_directory(self, path: str) -> Dict:
        """Check if directory exists or can be created."""
        if os.path.exists(path):
            return {"path": path, "exists": True, "message": f"Folder '{path}' sudah ada"}
        try:
            os.makedirs(path, exist_ok=True)
            os.rmdir(path)
            return {"path": path, "exists": False, "available": True}
        except Exception as e:
            return {"path": path, "exists": False, "available": False, "message": str(e)}
    
    def check_dependencies(self) -> Dict:
        """Check if required tools are installed."""
        results = {}
        
        for tool in ['node', 'npm', 'python3', 'git']:
            path = shutil.which(tool)
            results[tool] = {
                "installed": path is not None,
                "path": path or "Not found"
            }
        
        optional = ['docker', 'bwrap', 'pm2']
        for tool in optional:
            path = shutil.which(tool)
            results[tool] = {
                "installed": path is not None,
                "optional": True,
                "path": path or "Not found"
            }
        
        return results
    
    def check_disk_space(self, path: str = ".", min_mb: int = 500) -> Dict:
        """Check available disk space."""
        try:
            stat = os.statvfs(path)
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            return {
                "free_mb": int(free_mb),
                "sufficient": free_mb >= min_mb,
                "message": f"{'✓' if free_mb >= min_mb else '⚠'} {int(free_mb)} MB tersedia"
            }
        except:
            return {"free_mb": 0, "sufficient": True, "message": "Tidak bisa cek disk"}
    
    def get_all_warnings(self, project_name: str, port: int) -> List[Dict]:
        """Run all checks and return warnings."""
        warnings = []
        
        # Check directory
        dir_check = self.check_directory(project_name)
        if dir_check.get("exists"):
            warnings.append({"type": "warning", "message": dir_check["message"]})
        
        # Check port
        port_check = self.check_port(port)
        if not port_check["available"]:
            warnings.append({"type": "error", "message": port_check["message"]})
        
        # Check dependencies
        deps = self.check_dependencies()
        missing = [k for k, v in deps.items() if not v.get("installed") and not v.get("optional")]
        if missing:
            warnings.append({
                "type": "error",
                "message": f"Tools belum install: {', '.join(missing)}"
            })
        
        # Check disk
        disk = self.check_disk_space()
        if not disk["sufficient"]:
            warnings.append({"type": "warning", "message": disk["message"]})
        
        return warnings

proactive_warnings = ProactiveWarnings()
