#!/usr/bin/env python3
"""Post-Generate Guide — Show next steps after project creation."""
import os
from typing import Dict

class PostGuide:
    """Show what to do after project is generated."""
    
    def generate_guide(self, project_info: Dict) -> str:
        """Generate post-project guide."""
        project_type = project_info.get("type", "fullstack")
        project_path = project_info.get("path", ".")
        project_name = project_info.get("name", "my-app")
        
        output = []
        output.append("\n" + "=" * 60)
        output.append("🎉 PROJECT BERHASIL DIBUAT!")
        output.append("=" * 60)
        output.append(f"\n📁 Lokasi: {project_path}")
        
        if project_type == "fullstack":
            output.extend(self._fullstack_guide(project_name))
        elif project_type == "api":
            output.extend(self._api_guide(project_name))
        elif project_type == "bot":
            output.extend(self._bot_guide(project_name))
        
        output.extend(self._common_tips())
        output.append("\n" + "=" * 60)
        
        return "\n".join(output)
    
    def _fullstack_guide(self, name):
        return [
            f"\n🚀 Langkah Selanjutnya:",
            f"",
            f"  1. Masuk ke folder project:",
            f"     cd {name}",
            f"",
            f"  2. Jalankan backend:",
            f"     cd api",
            f"     npm install",
            f"     npm run dev",
            f"",
            f"  3. Jalankan frontend (terminal baru):",
            f"     cd web",
            f"     npm install",
            f"     npm run dev",
            f"",
            f"  4. Buka browser:",
            f"     http://localhost:5173",
            f"",
            f"  5. Cek API:",
            f"     http://localhost:3010/health",
        ]
    
    def _api_guide(self, name):
        return [
            f"\n🚀 Langkah Selanjutnya:",
            f"",
            f"  1. Masuk ke folder project:",
            f"     cd {name}",
            f"",
            f"  2. Install dependencies:",
            f"     npm install",
            f"",
            f"  3. Jalankan server:",
            f"     npm run dev",
            f"",
            f"  4. Cek API:",
            f"     http://localhost:3010/health",
        ]
    
    def _bot_guide(self, name):
        return [
            f"\n🚀 Langkah Selanjutnya:",
            f"",
            f"  1. Masuk ke folder project:",
            f"     cd {name}",
            f"",
            f"  2. Install dependencies:",
            f"     npm install",
            f"",
            f"  3. Set bot token:",
            f"     echo 'DISCORD_TOKEN=your_token' > .env",
            f"",
            f"  4. Jalankan bot:",
            f"     npm run dev",
        ]
    
    def _common_tips(self):
        return [
            f"\n💡 Tips:",
            f"  • Cek README.md untuk dokumentasi lengkap",
            f"  • Jalankan 'aeryn test' untuk cek kode",
            f"  • Jalankan 'aeryn deploy' untuk deploy",
            f"  • Ketik 'aeryn help' untuk bantuan",
            f"",
            f"📚 Dokumentasi: https://github.com/MuhammadApriansyah/Aeryn",
        ]

postguide = PostGuide()
