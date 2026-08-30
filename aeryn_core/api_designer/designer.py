#!/usr/bin/env python3
"""Visual API Designer — Design APIs with JSON/YAML."""
import json
from typing import Dict, List

class APIDesigner:
    def __init__(self):
        self._endpoints = []
    
    def add_endpoint(self, method: str, path: str, description: str, 
                     request_body: Dict = None, response: Dict = None):
        endpoint = {
            "method": method.upper(),
            "path": path,
            "description": description,
            "request": request_body or {},
            "response": response or {"200": {"description": "OK"}},
        }
        self._endpoints.append(endpoint)
        return endpoint
    
    def remove_endpoint(self, path: str):
        self._endpoints = [e for e in self._endpoints if e["path"] != path]
    
    def export_openapi(self) -> Dict:
        paths = {}
        for ep in self._endpoints:
            if ep["path"] not in paths:
                paths[ep["path"]] = {}
            paths[ep["path"]][ep["method"].lower()] = {
                "summary": ep["description"],
                "responses": ep["response"],
            }
        
        return {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": paths,
        }
    
    def export_routes(self, framework: str = "fastify") -> str:
        lines = []
        for ep in self._endpoints:
            if framework == "fastify":
                lines.append(f"app.{ep['method'].lower()}('{ep['path']}', async (req, reply) => {{")
                lines.append(f"  // {ep['description']}")
                lines.append(f"  return {{ message: '{ep['description']}' }};")
                lines.append(f"}});")
            lines.append("")
        return "\n".join(lines)
    
    def list_endpoints(self) -> List[Dict]:
        return self._endpoints

api_designer = APIDesigner()

