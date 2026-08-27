"""SOCIAL MEMORY - fakta tentang orang & channel yang dikenal Aeryn.

Struktur (JSON di Personalisasi/Database/social.json):
{
  "people": {
    "<discord_user_id|nama>": {
      "nama": "Sen",
      "relasi": "majikan/pembuat",
      "fakta": [{"text": "bangun webnovel platform", "hash": "abc123"}],
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
import hashlib
import json
import os
import re
import time

DB_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database")
DEFAULT_PATH = os.path.join(DB_DIR, "social.json")

MAX_FAKTA_PER_ORANG = 20


class SocialMemory:
    MAX_PEOPLE = 500  # V38.6 — cap kenalan (anti unbounded growth)

    # V39.10f — fragment-specific leak patterns (hasil string concat bug),
    # bukan substring sembarangan. Username real (paisenmtvsky) tetap valid.
    _LEAK_PATTERNS = [
        re.compile(r"siaisenmtvsky", re.I),  # concat fragment leak
        re.compile(r"probe-parity", re.I),   # test marker
        re.compile(r"memreflex", re.I),      # memref leak
        re.compile(r"inject_marker", re.I),  # SOP injection artefak
    ]

    def __init__(self, path: str = None):
        self.path = path or DEFAULT_PATH
        self._data = {"people": {}, "channels": {}}
        self._mtime = -1
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
                         "skilltest", "chaos-", "mathlive", "fbtest",
                         "dttest", "reminder_default", "mathlive1")

    @classmethod
    def is_persistent_person_key(cls, key: str) -> bool:
        """V38.5 + V39.10f — cegah entry transient/di traversal key masuk memory."""
        k = str(key).strip()  # V39.50: strip whitespace
        if not k or len(k) < 1:
            return False
        # Block traversal / path injection keys
        if "/" in k or ".." in k or "\\" in k or k.startswith("-"):
            return False
        if k.isdigit() and len(k) >= 15:
            return True          # Discord snowflake ID
        if k.startswith("chan_") and k[5:].isdigit() and len(k[5:]) >= 15:
            return True          # channel memory
        low = k.lower()
        if any(m in low for m in cls._TEST_KEY_MARKERS):
            return False
        # Allow known friendly names (Misela, etc) — bukan pure digit
        if k.isdigit() and len(k) < 15:
            return False  # "1", "123" = dummy
        return True

    @staticmethod
    def _fact_hash(text: str) -> str:
        return hashlib.sha256(text.strip().encode()).hexdigest()[:12]

    @classmethod
    def _norm_fact(cls, text: str) -> str:
        """Canonicalisasi fakta untuk dedup (lowercase, rstrip punctuation)."""
        return text.strip().lower().rstrip(".,;:!?")

    def touch_person(self, key: str, nama: str = "") -> dict | None:
        # V39.10f — cegah entry transient traversal key masuk permanen
        if not self.is_persistent_person_key(key):
            return None
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
        if "fakta" not in p or not isinstance(p["fakta"], list):
            p["fakta"] = []
        p["last_seen"] = time.time()
        self._save()
        return p

    def add_fact(self, key: str, fact: str, nama: str = "", author: str = "aeryn") -> bool:
        """Tambah fakta tentang orang. Return True jika fakta baru disimpan."""
        fact = fact.strip()[:200]
        if not fact:
            return False
        # V39.10f — block fragment leak exact (hasil concat bug), bukan substring
        for pat in self._LEAK_PATTERNS:
            if pat.search(fact):
                return False
        # V39.10f — cegah key tidak valid masuk
        p = self.touch_person(key, nama)
        if p is None:
            return False
        norm = self._norm_fact(fact)
        existing = {self._norm_fact(e.get("text", e) if isinstance(e, dict) else e)
                    for e in p.get("fakta", [])}
        if norm in existing:
            return False
        # Migrate fakta lama (string) ke dict format
        fakta = p.get("fakta", [])
        if fakta and isinstance(fakta[0], str):
            fakta = [{"text": t, "hash": self._fact_hash(t)} for t in fakta]
        # V39.44: Add author attribution
        fakta.append({"text": fact, "hash": self._fact_hash(fact), "author": author})
        p["fakta"] = fakta[-MAX_FAKTA_PER_ORANG:]
        self._save()
        return True

    def set_relation(self, key: str, relasi: str, nama: str = ""):
        p = self.touch_person(key, nama)
        if p is None:
            return False
        p["relasi"] = relasi[:80]
        self._save()
        return True

    def get_facts(self, key: str) -> list:
        """Return list of fact dicts with author attribution."""
        p = self.know_person(key)
        if not p:
            return []
        fakta = p.get("fakta", [])
        # Return full dicts (with author) if available
        result = []
        for f in fakta:
            if isinstance(f, dict):
                result.append(f)
            else:
                # Legacy string format — wrap in dict
                result.append({"text": f, "hash": "", "author": "unknown"})
        return result

    def set_preference(self, key: str, pref_key: str, value: str) -> bool:
        """V39.10f — set preference via API (dibutuhkan social_generator/cerewet)."""
        p = self.touch_person(key)
        if p is None:
            return False
        p.setdefault("preferensi", {})[pref_key] = value[:100]
        self._save()
        return True

    def get_preference(self, key: str, pref_key: str, default=None):
        """V39.11 — preference getter untuk social_generator / cerewet."""
        p = self.know_person(key)
        if not p:
            return default
        return p.get("preferensi", {}).get(pref_key, default)

    # ---- channels ------------------------------------------------------
    def know_channel(self, key: str) -> dict | None:
        return self._data["channels"].get(key)

    def touch_channel(self, key: str, nama: str = "", peran: str = ""):
        if "/" in key or ".." in key:
            return None
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
        if c is None:
            return False
        c["topik_terakhir"] = topic[:150]
        self._save()
        return True

    # ---- prompt blocks -------------------------------------------------
    def person_block(self, key: str, fallback_nama: str = "") -> str:
        p = self.know_person(key)
        if not p:
            # orang belum dikenal — catat pertemuan pertama
            self.touch_person(key, fallback_nama)
            return ("(Orang ini baru pertama kali kamu temui. Perhatikan dan "
                    "ingat detail penting tentang dia.)")
        lines = [
            f"(Kamu mengenal orang ini: {p.get('nama', key)}.)"
        ]
        if p.get("relasi"):
            lines.append(f"Relasi: {p['relasi']}.")
        if p["fakta"]:
            lines.append("Yang kamu ingat tentang dia:")
            for f in p["fakta"][-6:]:
                txt = f.get("text", f) if isinstance(f, dict) else f
                lines.append(f"- {txt}")
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

    def sanitize_database(self):
        """V39.10f — audit + bersihin database: hapus entry transient/invalid."""
        removed = []
        people = self._data["people"]
        for key in list(people.keys()):
            if not self.is_persistent_person_key(key):
                removed.append(key)
                del people[key]
            else:
                # sanitize fakta: hapus leak, migrate format
                facts = people[key].get("fakta", [])
                clean_facts = []
                for f in facts:
                    txt = f.get("text", f) if isinstance(f, dict) else f
                    # skip fakta dengan fragment leak
                    if any(pat.search(txt) for pat in self._LEAK_PATTERNS):
                        removed.append(f"fact@{key}: {txt[:40]}")
                        continue
                    if isinstance(f, dict):
                        clean_facts.append(f)
                    else:
                        clean_facts.append({"text": f, "hash": self._fact_hash(f)})
                people[key]["fakta"] = clean_facts[-MAX_FAKTA_PER_ORANG:]
        # sanitize channels
        channels = self._data["channels"]
        for key in list(channels.keys()):
            if "/" in key or ".." in key:
                removed.append(f"channel#{key}")
                del channels[key]
        if removed:
            self._save()
        return removed
