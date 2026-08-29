#!/usr/bin/env python3
"""Project Preview — Show what will be generated before creating files."""
import os
from typing import Dict, List

class ProjectPreview:
    """Preview project structure before generation."""
    
    def generate_preview(self, plan: Dict) -> Dict:
        """Generate a preview of what will be created."""
        preview = {
            "project_name": plan.get("name", "my-app"),
            "structure": [],
            "files": {},
            "dependencies": [],
            "database": [],
            "api_endpoints": [],
        }
        
        # Database tables
        if "database" in plan:
            for model in plan["database"].get("models", []):
                preview["database"].append({
                    "table": model["name"],
                    "fields": [f["name"] for f in model.get("fields", [])],
                })
        
        # API endpoints
        if "api" in plan:
            for endpoint in plan["api"].get("endpoints", []):
                preview["api_endpoints"].append({
                    "method": endpoint["method"],
                    "path": endpoint["path"],
                    "description": endpoint["description"],
                })
        
        # File structure
        preview["structure"] = [
            "src/server.ts",
            "src/routes/",
            "src/database.ts",
            "database/",
            "migrations/",
            "tests/",
            "package.json",
            "tsconfig.json",
        ]
        
        # Dependencies
        preview["dependencies"] = plan.get("backend", {}).get("dependencies", [])
        
        return preview
    
    def display_preview(self, preview: Dict) -> str:
        """Format preview for display."""
        output = []
        output.append("\n" + "=" * 60)
        output.append("📋 PROJECT PREVIEW")
        output.append("=" * 60)
        
        output.append(f"\n📁 Project: {preview['project_name']}")
        
        if preview["database"]:
            output.append("\n🗄️  Database Tables:")
            for table in preview["database"]:
                output.append(f"   • {table['table']}")
                for field in table["fields"]:
                    output.append(f"     - {field}")
        
        if preview["api_endpoints"]:
            output.append("\n🌐 API Endpoints:")
            for endpoint in preview["api_endpoints"]:
                output.append(f"   {endpoint['method']:6s} {endpoint['path']:20s} {endpoint['description']}")
        
        if preview["dependencies"]:
            output.append("\n📦 Dependencies:")
            for dep in preview["dependencies"]:
                output.append(f"   • {dep}")
        
        output.append("\n📂 Files will be created:")
        for item in preview["structure"]:
            output.append(f"   • {item}")
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)

project_preview = ProjectPreview()
