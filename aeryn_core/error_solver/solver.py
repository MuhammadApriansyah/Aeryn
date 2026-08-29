#!/usr/bin/env python3
"""Error Solver — Detect errors and provide friendly solutions."""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ErrorSolver:
    """Analyze errors and provide human-friendly solutions."""
    
    def __init__(self):
        self._patterns = self._load_patterns()
    
    def _load_patterns(self) -> List[Dict]:
        """Load error patterns and solutions."""
        return [
            {
                "pattern": r"Port \d+ (already in use|is in use)",
                "message": "Port sudah dipakai aplikasi lain.",
                "solutions": [
                    "Matikan aplikasi yang pakai port itu",
                    "Atau ganti port: aeryn dev --port 3011",
                ],
            },
            {
                "pattern": r"ModuleNotFoundError|ImportError",
                "message": "Library belum terinstall.",
                "solutions": [
                    "Jalankan: pip install -r requirements.txt",
                    "Atau: npm install",
                ],
            },
            {
                "pattern": r"Permission denied",
                "message": "Tidak punya izin akses file/folder.",
                "solutions": [
                    "Coba jalankan dengan sudo",
                    "Atau ubah permission: chmod 755 <folder>",
                ],
            },
            {
                "pattern": r"Connection refused",
                "message": "Tidak bisa koneksi ke server.",
                "solutions": [
                    "Pastikan server sudah jalan",
                    "Cek apakah port benar",
                ],
            },
            {
                "pattern": r"No such file or directory",
                "message": "File atau folder tidak ditemukan.",
                "solutions": [
                    "Cek apakah path sudah benar",
                    "Pastikan file sudah dibuat",
                ],
            },
            {
                "pattern": r"SyntaxError",
                "message": "Ada kesalahan tulis kode.",
                "solutions": [
                    "Cek baris yang error",
                    "Pastikan kurung/tanda baca lengkap",
                ],
            },
            {
                "pattern": r"Database locked",
                "message": "Database sedang dipakai proses lain.",
                "solutions": [
                    "Tutup aplikasi yang pakai database",
                    "Atau restart komputer",
                ],
            },
            {
                "pattern": r"OutOfMemoryError|memory",
                "message": "Memori tidak cukup.",
                "solutions": [
                    "Tutup aplikasi lain",
                    "A tambah RAM",
                ],
            },
            {
                "pattern": r"Docker",
                "message": "Docker belum install atau tidak jalan.",
                "solutions": [
                    "Install Docker dari https://docker.com",
                    "Atau pakai PM2: aeryn deploy --target pm2",
                ],
            },
        ]
    
    def analyze(self, error_message: str) -> Optional[Dict]:
        """Analyze error and return solution."""
        for pattern in self._patterns:
            if re.search(pattern["pattern"], error_message, re.IGNORECASE):
                return {
                    "error": error_message,
                    "message": pattern["message"],
                    "solutions": pattern["solutions"],
                }
        
        # Unknown error
        return {
            "error": error_message,
            "message": "Error tidak dikenali.",
            "solutions": [
                "Coba cari di Google",
                "Atau tanya di forum Aeryn",
            ],
        }
    
    def format(self, error_info: Dict) -> str:
        """Format error info for display."""
        output = []
        output.append("=" * 50)
        output.append("❌ Error Terdeteksi")
        output.append("=" * 50)
        output.append(f"\n📝 {error_info['message']}")
        output.append(f"\n🔍 Detail: {error_info['error']}")
        output.append("\n💡 Solusi:")
        for i, sol in enumerate(error_info["solutions"], 1):
            output.append(f"   {i}. {sol}")
        output.append("\n" + "=" * 50)
        return "\n".join(output)

error_solver = ErrorSolver()
