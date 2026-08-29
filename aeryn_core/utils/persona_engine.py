"""PERSONA ENGINE - Aeryn-Core

Memuat & menggabungkan lapisan persona menjadi satu system prompt.
Lapisan (urutan = prioritas):
  1. aeryn_core.md         - identitas inti + gaya bicara + push-pull
  2. michaela_layer.md     - sisi arsitek/observasional (sisi manipulatif dibuang)
  3. aeryn_orchestrator.md - 5 divisi sub-agen mental + routing

Social memory (fakta tentang orang yang dikenal) diinject terpisah oleh daemon.
"""
import os

PERSONA_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Persona")

LAYERS = ["aeryn_core.md", "michaela_layer.md", "aeryn_orchestrator.md"]


def load_persona(persona_dir: str = None, layers: list = None) -> str:
    """Baca semua lapisan persona, gabung jadi satu string system prompt."""
    pdir = persona_dir or PERSONA_DIR
    names = layers or LAYERS
    parts = []
    for name in names:
        path = os.path.join(pdir, name)
        try:
            content = open(path, encoding="utf-8").read().strip()
        except OSError:
            continue
        # buang frontmatter markdown jika ada
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                content = content[end + 3:].strip()
        parts.append(content)
    if not parts:
        return "Kamu Aeryn, agen otonom yang hangat dan metodis."
    return "\n\n---\n\n".join(parts)


class PersonaEngine:
    """Cache persona di memori; reload bila file berubah."""

    def __init__(self, persona_dir: str = None):
        self.dir = persona_dir or PERSONA_DIR
        self._cache = ""
        self._mtime = 0.0

    def get(self) -> str:
        try:
            mtimes = []
            for name in LAYERS:
                p = os.path.join(self.dir, name)
                if os.path.exists(p):
                    mtimes.append(os.path.getmtime(p))
            newest = max(mtimes) if mtimes else 0.0
            if newest > self._mtime or not self._cache:
                self._cache = load_persona(self.dir)
                self._mtime = newest
            return self._cache
        except Exception:
            return self._cache or "Kamu Aeryn."
