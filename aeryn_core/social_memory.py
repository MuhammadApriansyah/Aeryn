"""SOCIAL MEMORY - fakta tentang orang & channel yang dikenal Aeryn.

Struktur (JSON di Personalisasi/Database/social.json):
{
  "people": {
    "<discord_user_id|nama>": {
      "nama": "Sen",
      "relasi": "majikan/pembuat",
      "fakta": ["bangun webnovel platform", "suka UI rapi"],
      "preferensi": {"bahasa": "id-casual", "panjang": "singkat"},
      "last_seen": ts
    }
  },
  "channels": {
    "<channel_id>": {
      "nama": "general",
      "peran": "ruang utama ngobrol",
      "topik_terakhir": "...",
      "last_seen": ts
    }
  }
}

Aeryn bisa menambah fakta via tool `remember` (lihat daemon).
"""
import json
import os
import time

DB_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database")
DEFAULT_PATH = os.path.join(DB_DIR, "social.json")

MAX_FAKTA_PER_ORANG = 20


class SocialMemory:
    MAX_PEOPLE = 500  # V38.6 — cap kenalan (anti unbounded growth)

    def __init__(self, path: str = None):
        self.path = path or DEFAULT_PATH
        self._data = {"people": {}, "channels": {}}
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.loads(f.read())
            self._data = {
                "people": d.get("people", {}),
                "channels": d.get("channels", {}),
            }
        except (OSError, ValueError):
            pass

    def _reload_if_changed(self):
        """Reload dari disk bila file berubah (diedit proses lain / manual)."""
        try:
            m = os.path.getmtime(self.path)
        except OSError:
            return
        if m != getattr(self, "_mtime", -1):
            self._mtime = m
            self._load()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=1)

    # ---- people ------------------------------------------------------
    def know_person(self, key: str) -> dict | None:
        self._reload_if_changed()
        return self._data["people"].get(key)

    # V38.5 — hanya ID Discord nyata (digit panjang) yang layak jadi
    # "kenalan" permanen. Session test/smoke/sub-agent mencemari social
    # memory (ditemukan audit: 49 entri sampah dari 55).
    _TEST_KEY_MARKERS = ("smoke", "test", "parity", "wrtest", "soptest",
                         "sub_", "subagent", "v36", "digestcheck", "rltest",
                         "sectest", "sigtest", "gradcheck", "handscheck",
                         "fscheck", "e2e-", "modelcheck", "limitcheck",
                         "reflexcheck", "captest", "v29", "vgate",
                         "skilltest")

    @classmethod
    def is_persistent_person_key(cls, key: str) -> bool:
        k = str(key)
        if k.isdigit() and len(k) >= 15:
            return True          # Discord snowflake ID
        if k.startswith("chan_"):
            return True          # channel memory
        low = k.lower()
        return not any(m in low for m in cls._TEST_KEY_MARKERS)

    def touch_person(self, key: str, nama: str = "") -> dict:
        # V38.6 — cap jumlah people (anti unbounded growth)
        people = self._data["people"]
        if key not in people and len(people) >= self.MAX_PEOPLE:
            # buang yang paling lama tidak terlihat
            oldest = min(people, key=lambda k: people[k].get("last_seen", 0))
            del people[oldest]
        p = people.setdefault(
            key, {"nama": nama or key, "relasi": "", "fakta": [],
                  "preferensi": {}, "last_seen": 0})
        if nama and not p.get("nama"):
            p["nama"] = nama
        p["last_seen"] = time.time()
        self._save()
        return p

    def add_fact(self, key: str, fact: str, nama: str = "") -> bool:
        """Tambah fakta tentang orang. Return True jika fakta baru disimpan."""
        fact = fact.strip()[:200]
        if not fact:
            return False
        p = self.touch_person(key, nama)
        if fact in p["fakta"]:
            return False
        p["fakta"].append(fact)
        # jaga ringan: simpan maksimal N fakta terbaru
        p["fakta"] = p["fakta"][-MAX_FAKTA_PER_ORANG:]
        self._save()
        return True

    def set_relation(self, key: str, relasi: str, nama: str = ""):
        p = self.touch_person(key, nama)
        p["relasi"] = relasi[:80]
        self._save()

    # ---- channels ------------------------------------------------------
    def know_channel(self, key: str) -> dict | None:
        return self._data["channels"].get(key)

    def touch_channel(self, key: str, nama: str = "", peran: str = ""):
        c = self._data["channels"].setdefault(
            key, {"nama": nama or key, "peran": peran,
                  "topik_terakhir": "", "last_seen": 0})
        if nama:
            c["nama"] = nama
        if peran and not c.get("peran"):
            c["peran"] = peran
        c["last_seen"] = time.time()
        self._save()
        return c

    def set_channel_topic(self, key: str, topic: str):
        c = self.touch_channel(key)
        c["topik_terakhir"] = topic[:150]
        self._save()

    # ---- prompt blocks -------------------------------------------------
    def person_block(self, key: str, fallback_nama: str = "") -> str:
        p = self.know_person(key)
        if not p:
            # orang belum dikenal — catat pertemuan pertama
            self.touch_person(key, fallback_nama)
            return ("(Orang ini baru pertama kali kamu temui. Perhatikan dan "
                    "ingat detail penting tentang dia.)")
        lines = [f"(Kamu mengenal orang ini: {p.get('nama', key)}."]
        if p.get("relasi"):
            lines.append(f"Relasi: {p['relasi']}.")
        if p["fakta"]:
            lines.append("Yang kamu ingat tentang dia:")
            for f in p["fakta"][-6:]:
                lines.append(f"- {f}")
        lines.append("Gunakan ingatan ini secara alami, jangan dibacakan.)")
        return "\n".join(lines)

    def channel_block(self, key: str, fallback_nama: str = "") -> str:
        c = self.know_channel(key)
        if not c:
            self.touch_channel(key, fallback_nama)
            return ""
        parts = [f"(Ruang ini: {c.get('nama', key)}"]
        if c.get("peran"):
            parts.append(f"— {c['peran']}")
        if c.get("topik_terakhir"):
            parts.append(f". Topik terakhir di sini: {c['topik_terakhir']}")
        parts.append(".)")
        return "".join(parts)
