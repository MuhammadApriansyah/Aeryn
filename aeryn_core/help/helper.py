#!/usr/bin/env python3
"""Help Helper — Contextual help for every step."""
from typing import Dict, List

class HelpHelper:
    """Provide contextual help for Aeryn features."""
    
    def __init__(self):
        self._help_texts = self._load_help()
    
    def _load_help(self) -> Dict:
        """Load help texts."""
        return {
            "project_type": {
                "title": "📁 Tipe Project",
                "help": [
                    "Web App — Website lengkap dengan frontend dan backend",
                    "API Only — Backend saja, untuk mobile app atau frontend lain",
                    "Bot — Discord bot atau Telegram bot",
                ],
            },
            "project_name": {
                "title": "📝 Nama Project",
                "help": [
                    "Gunakan huruf kecil dan dash (-)",
                    "Contoh: my-app, task-manager, blog-api",
                    "Jangan gunakan spasi atau karakter spesial",
                ],
            },
            "database": {
                "title": "🗄️ Database",
                "help": [
                    "SQLite — Mudah, tidak perlu install, cocok untuk belajar",
                    "PostgreSQL — Lebih kuat, cocok untuk production",
                    "Pilih SQLite jika kamu baru mulai",
                ],
            },
            "authentication": {
                "title": "🔐 Authentication",
                "help": [
                    "Login/Register — Sistem masuk dan daftar user",
                    "Berguna jika app kamu butuh data per user",
                    "Tidak perlu jika app kamu tidak punya user",
                ],
            },
            "commands": {
                "title": "⌨️ Perintah CLI",
                "help": [
                    "aeryn start  — Buat project baru (wizard)",
                    "aeryn dev    — Jalankan development server",
                    "aeryn test   — Jalankan test",
                    "aeryn build  — Build untuk production",
                    "aeryn deploy — Deploy ke server",
                ],
            },
            "errors": {
                "title": "❌ Error",
                "help": [
                    "Port already in use — Ganti port atau matikan app lain",
                    "Module not found — Jalankan: npm install",
                    "Permission denied — Coba: sudo aeryn ...",
                ],
            },
        }
    
    def get_help(self, key: str) -> Dict:
        """Get help text for a key."""
        return self._help_texts.get(key, {"title": "Help", "help": ["Tidak ada bantuan tersedia"]})
    
    def format_help(self, key: str) -> str:
        """Format help for display."""
        help_info = self.get_help(key)
        output = [f"\n{'=' * 50}", f"❓ {help_info['title']}", "=" * 50]
        for line in help_info["help"]:
            output.append(f"  💡 {line}")
        output.append("=" * 50)
        return "\n".join(output)
    
    def get_all_topics(self) -> List[str]:
        """Get all help topics."""
        return list(self._help_texts.keys())

help_helper = HelpHelper()
