#!/usr/bin/env python3
"""Template Preview — Visual preview with thumbnails."""
import os

class TemplatePreview:
    def __init__(self):
        self._templates = {
            "react": {
                "name": "React + Fastify",
                "description": "Full-stack app dengan React dan Fastify backend",
                "color": "#61dafb",
                "icon": "⚛️",
                "screenshot": "    ┌─────────────────────┐\n    │  React App          │\n    │  ┌───────────────┐  │\n    │  │  Welcome      │  │\n    │  │  [Button]     │  │\n    │  └───────────────┘  │\n    └─────────────────────┘",
                "features": ["React 18", "TypeScript", "Vite", "Fastify", "SQLite"],
                "difficulty": "Pemula",
            },
            "vue": {
                "name": "Vue + Fastify",
                "description": "Full-stack app dengan Vue.js",
                "color": "#42b883",
                "icon": "🟢",
                "screenshot": "    ┌─────────────────────┐\n    │  Vue App            │\n    │  ┌───────────────┐  │\n    │  │  Welcome      │  │\n    │  │  [Button]     │  │\n    │  └───────────────┘  │\n    └─────────────────────┘",
                "features": ["Vue 3", "TypeScript", "Vite", "Fastify", "SQLite"],
                "difficulty": "Pemula",
            },
            "api": {
                "name": "API Only",
                "description": "Backend API saja, tanpa frontend",
                "color": "#68a063",
                "icon": "🔌",
                "screenshot": "    ┌─────────────────────┐\n    │  API Server         │\n    │  GET  /api/health   │\n    │  GET  /api/items    │\n    │  POST /api/items    │\n    └─────────────────────┘",
                "features": ["Fastify", "SQLite", "REST API", "JWT Auth"],
                "difficulty": "Pemula",
            },
            "bot": {
                "name": "Discord Bot",
                "description": "Bot untuk Discord",
                "color": "#5865f2",
                "icon": "🤖",
                "screenshot": "    ┌─────────────────────┐\n    │  Discord Bot        │\n    │  /ping -> Pong!     │\n    │  /help -> Help msg  │\n    └─────────────────────┘",
                "features": ["Discord.js", "Slash Commands", "Events"],
                "difficulty": "Menengah",
            },
        }
    
    def list_templates(self):
        return list(self._templates.keys())
    
    def get_template(self, template_id):
        return self._templates.get(template_id, {})
    
    def display_card(self, template_id):
        t = self._templates.get(template_id)
        if not t:
            return "Template not found"
        
        lines = [
            f"┌─────────────────────────────────────┐",
            f"│ {t['icon']} {t['name']:30s} │",
            f"├─────────────────────────────────────┤",
            f"│ {t['description']:36s}│",
            f"│                                     │",
            f"│ {t['screenshot']:37s}│",
            f"│                                     │",
            f"│ Features: {', '.join(t['features'][:3]):28s}│",
            f"│ Difficulty: {t['difficulty']:26s}│",
            f"└─────────────────────────────────────┘",
        ]
        return "\n".join(lines)

template_preview = TemplatePreview()
