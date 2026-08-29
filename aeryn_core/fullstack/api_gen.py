#!/usr/bin/env python3
"""API Generator."""
from typing import Dict, List

class APIGenerator:
    def generate(self, plan: Dict) -> Dict:
        endpoints = plan.get("endpoints", [])
        routes = []
        
        for endpoint in endpoints:
            route = self._generate_route(endpoint)
            routes.append(route)
        
        return {
            "routes": routes,
            "openapi": self._generate_openapi(endpoints),
        }
    
    def _generate_route(self, endpoint: Dict) -> str:
        method = endpoint["method"].lower()
        path = endpoint["path"]
        desc = endpoint["description"]
        
        return f'''// {desc}
app.{method}('{path}', async (req, reply) => {{
  // TODO: Implement {desc}
  return {{ message: '{desc}' }};
}});
'''
    
    def _generate_openapi(self, endpoints: List[Dict]) -> Dict:
        paths = {}
        for ep in endpoints:
            path = ep["path"]
            if path not in paths:
                paths[path] = {}
            paths[path][ep["method"].lower()] = {
                "summary": ep["description"],
                "responses": {"200": {"description": "OK"}},
            }
        return {"openapi": "3.0.0", "paths": paths}
