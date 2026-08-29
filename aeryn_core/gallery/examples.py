#!/usr/bin/env python3
"""Example Gallery — Cloneable example projects."""
from typing import Dict, List

class ExampleGallery:
    """Show example projects that can be cloned."""
    
    def __init__(self):
        self._examples = self._load_examples()
    
    def _load_examples(self) -> List[Dict]:
        return [
            {
                "id": "todo-app",
                "name": "Todo App",
                "description": "Aplikasi todo sederhana dengan auth",
                "difficulty": "Pemula",
                "tech": ["React", "Fastify", "SQLite"],
                "features": ["Login/Register", "CRUD Todo", "Filter by status"],
            },
            {
                "id": "blog-api",
                "name": "Blog API",
                "description": "API untuk blog dengan posts dan comments",
                "difficulty": "Pemula",
                "tech": ["Fastify", "SQLite"],
                "features": ["CRUD Posts", "Comments", "Pagination"],
            },
            {
                "id": "chat-bot",
                "name": "Discord Bot",
                "description": "Bot Discord dengan commands dan events",
                "difficulty": "Menengah",
                "tech": ["Node.js", "Discord.js"],
                "features": ["Slash Commands", "Events", "Database"],
            },
        ]
    
    def list_examples(self) -> List[Dict]:
        return self._examples
    
    def get_example(self, example_id: str) -> Dict:
        for ex in self._examples:
            if ex["id"] == example_id:
                return ex
        return {}
    
    def display_gallery(self) -> str:
        output = []
        output.append("\n" + "=" * 60)
        output.append("🎨 CONTOH PROJECT")
        output.append("=" * 60)
        
        for ex in self._examples:
            output.append(f"\n  📦 {ex['name']} [{ex['difficulty']}]")
            output.append(f"     {ex['description']}")
            output.append(f"     Tech: {', '.join(ex['tech'])}")
            output.append(f"     Features: {', '.join(ex['features'])}")
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)

example_gallery = ExampleGallery()
