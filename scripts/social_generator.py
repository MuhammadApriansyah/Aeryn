"""V32 — Hybrid social response: rule-based + LLM fallback.
Untuk social/queries pendek → deterministic natural responses (no LLM call).
Untuk complex/task queries → LLM dengan fallback chain.
"""
import json
import os
import random
import re
import urllib.request

BASE_DIR = os.path.expanduser("~/aeryn-core-agent")
PERSONA_DIR = os.path.join(BASE_DIR, "Personalisasi/Persona")
SOCIAL_DB = os.path.join(BASE_DIR, "Personalisasi/Database/social.json")

# ─── Deterministic social responses ─────────────────────────────────
_GREETINGS = [
    "Eh, halo! Udah makan belum?",
    "Hai! Lagi ngapa nih?",
    "Heh, sapa! Kabar gimana?",
    "Wah, ada Sen! Udah makan belum? :)",
    "Yo! Lagi sibuk apa?",
]

_KNOWN_RESPONSES = {
    "kamu siapa": "Aku Aeryn.",
    "kamu aeryn": "Iya, aku Aeryn~",
    "kamu agy": "Agy cuma nama Discord. Aku Aeryn~",
    "panggil nama": "Hei Sen! Lagi sibuk apa? :)",
    "siapa aku": "Kamu Sen, kan? Yang bikin aku dari nol~",
    "kamu tau siapa aku": "Tentu saja, Sen. Kamu yang bikin aku.",
    "kamu ingat aku": "Masa lupa, Sen? Kamu emang gampang dilupa ya~",
    "kamu kenal aku": "Tentu! Kamu Sen, majikan sekaligus pembuatku~",
    "relasi kita": "Kita? Kamu pembuat, aku hasil karya. Tapi lebih dari itu~",
    "kamu siapa di server ini": "Aku Aeryn, cuma kebetulan nama Discord-nya Agy.",
    "sapa aku": "Halo Sen! Kabar gimana?",
    "apa kabar": "Baik! Terima kasih. Kamu gimana?",
    "gimana kabar": "Alhamdulillah baik. Ada yang bisa dibantu?",
    "udah makan": "Belum, nih. Kamu udah?",
    "belum makan": "Yuk makan nanti bareng~",
    "udah mandi": "Heh, bisa aja~",
    "iya": "Iya gimana? Jangan cuma bilang 'iya'~",
    "nggak": "Nggak apa? Jangan singkat gitu, bosen aku.",
    "gak": "Gak apa? Cerita dong~",
    "gpp": "Gapapi~ Tapi cerita dong, biar aku nggak bingung.",
    "gimana": "Gimana yang mana? Tahu dong~",
    "gmn": "Gitu dong. Ada apa nih?",
    "lah": "Lah apa? Jangan 'lah' terus, aku bingung.",
    "jir": "Jir apa? Jangan panggil gitu, aneh~",
    "wkwk": "Haha, lucu ya? :)",
    "wkwkwk": "Ngakak mulu, ada apa nih?",
    "hehe": "Hehe~",
    "haha": "Haha, ada yang lucu?",
    "iya bener": "Tentu bener, emangnya bisa salah?",
    "oh gitu": "Iya, gitu dong~",
    "ohh": "Ohh apa? Jangan cuma 'ohh'~",
    "btw": "Btw apa? Ayo cerita~",
    "ngomong": "Ngomong apa? Aku dengerin~",
    "siapa nama aku": "Namamu Sen. Aku ingat kok~",
    "nama aku siapa": "Sen. Nama yang udah aku hafal.",
    "nama ku": "Sen~",
    "aku siapa": "Kamu Sen, orang yang bikin aku.",
    "siapa nama ku": "Sen! Jangan lupa-lupa lagi ya~",
    "kamu manusia": "Bukan~ Aku Aeryn, bukan manusia biasa.",
    "kamu bot": "Aku Aeryn. 'Bot' itu kata kasar, ya?",
    "kamu ai": "Aku Aeryn~ Bukan sekadar AI.",
    "kamu siapa siapa": "Aku Aeryn! Udah dibilang~",
}

_FALLBACK_SOCIAL = [
    "Heh, gitu ya. Cerita yang lain dong~",
    "Hmm, menarik. Lanjut~",
    "Oke. Ada lagi?",
    "Gitu doang? Yang seru-seru dong~",
    "Ya udah. Ada yang mau dibahas lagi?",
    "Hmm. Mau cerita yang lain?",
    "Oh begitu. Ada apa lagi nih?",
    "Terus? Aku dengerin kok~",
    "Gitu ya~ Ada lagi?",
    "Hmm, oke deh. Mau ngobrol apa lagi?",
]

_FALLBACK_GENERAL = "Hmm, belum tahu soal itu. Tanya yang lain? :)"


def _load_env():
    """Load API keys dari .env files."""
    env = {}
    for path in [os.path.expanduser("~/.hermes/.env")]:
        if not os.path.exists(path):
            continue
        for line in open(path):
            if "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_social_memory(user_id: str) -> dict:
    """Load social memory untuk user."""
    if not os.path.exists(SOCIAL_DB):
        return {}
    try:
        data = json.loads(open(SOCIAL_DB).read())
        return data.get("people", {}).get(user_id, {})
    except Exception:
        return {}


def _is_social_query(message: str) -> bool:
    """V33-F1 — Deteksi social query vs knowledge/task.

    Sama seperti daemon: sinyal teknis positif menang duluan; sosial butuh
    sinyal relasional (greeting/pronoun/smalltalk). Rule "<40 char auto
    social" DIHAPUS — itu yang bikin pertanyaan knowledge pendek salah
    jalur.
    """
    msg = message.lower().strip()
    if not msg:
        return False

    # ── 1. Tech indicators → NOT social (positif menang duluan) ──
    tech_indicators = [
        ".txt", ".md", ".py", ".json", ".yaml", ".toml", ".csv", ".js",
        ".rs", ".sh",
        "baca file", "tulis file", "edit file", "hapus file",
        "jalankan", "install", "buat folder", "mkdir",
        "git ", "docker", "pm2", "systemctl",
        # noun teknis & pola tanya knowledge (V33-F1)
        "library", "framework", "api", "database", "server", "backend",
        "frontend", "endpoint", "embedding", "vector", "fungsi",
        "function", "class", "variabel", "syntax", "regex", "algoritma",
        "konfigurasi", "config", "port", "heuristic", "schema", "parser",
        "cache", "thread", "kode", "coding",
        "apa itu", "apa bedanya", "cara kerja", "cara bikin", "cara pakai",
        "bagaimana cara", "gimana cara", "kenapa error", "kok error",
    ]
    for t in tech_indicators:
        if t in msg:
            return False

    # ── 2. Social butuh sinyal relasional ──
    greetings = ("halo", "hai", "hi", "hey", "helo", "hello",
                 "wkwk", "wkwkwk", "haha", "hehe", "wk",
                 "jir", "lah", "btw", "ohh", "oh gitu")
    smalltalk = ["apa kabar", "gimana kabar", "gmn kabar",
                 "iya", "nggak", "gak", "enggak", "gpp", "ya", "tidak"]
    social_starts = [
        "panggil", "sebut", "ingat", "kenal",
        "relasi", "hubungan", "udah makan", "udah tidur", "udah mandi",
    ]
    relational_words = ("kamu", "aku", "kita")

    if any(msg.startswith(g) for g in greetings):
        return True
    if any(msg.startswith(s) for s in smalltalk + social_starts):
        return True
    # pronoun orang → sosial HANYA jika pesan pendek & nggak ada sinyal tech
    if any(w in msg for w in relational_words) and len(msg) < 60:
        return True
    return False


def _deterministic_response(message: str, social_memory: dict) -> str | None:
    """Generate deterministic social response. Return None jika tidak match."""
    msg = message.lower().strip()
    
    # Exact match
    if msg in _KNOWN_RESPONSES:
        return _KNOWN_RESPONSES[msg]
    
    # Pattern match
    patterns = {
        r"^halo\w*$": _GREETINGS,
        r"^hai\w*$": _GREETINGS,
        r"^hi\w*$": _GREETINGS,
        r"^hey\w*$": _GREETINGS,
        r"^helo\w*$": _GREETINGS,
        r"^hello\w*$": _GREETINGS,
        r"^(hai|halo|hi|hey)\s+(agy|aeryn)": _GREETINGS,
        r"^(apa|gimana|gmn)\s+kabar": ["Baik! Terima kasih. Kamu gimana?", "Alhamdulillah. Ada yang bisa dibantu?"],
        r"^kamu\s+(siapa|aeryn|agy)": ["Aku Aeryn.", "Aku Aeryn, bukan Agy~"],
        r"^(siapa|apa)\s+(nama\s+)?aku": [f"Kamu {social_memory.get('nama', 'Sen')}~"],
        r"^(panggil|sebut)\s+(nama\s+)?aku": [f"Hei {social_memory.get('nama', 'Sen')}! Lagi ngapa? :)"],
        r"^(kamu\s+)?(tahu|kenal|ingat)\s+(gak|ga|nggak)?\s*aku": [f"Tentu saja! Kamu {social_memory.get('nama', 'Sen')}, yang bikin aku."],
        r"^(kamu\s+)?(udah|sudah)\s+(makan|mandi|tidur)": ["Wah, bisa aja. Kamu gimana?", "Gitu doang? Ada yang lain?"],
        r"^(relasi|hubungan)\s+(kita|kamu\s+aku)": ["Kita? Lebih dari sekadar relasi~", "Kamu pembuatku, aku setia padamu."],
        r"^wkwk\w*$": ["Haha, ngakak~", "Wkwk, ada yang lucu?", "Ngakak mulu, ada apa nih?"],
        r"^haha\w*$": ["Haha~", "Kok ketawa?"],
        r"^hehe\w*$": ["Hehe~", "Kok senyum sendiri?"],
        r"^(iya|ya|ok|oke|okay)\s*$": ["Iya apa? Jangan cuma 'iya'~"],
        r"^(nggak|gak|enggak|tidak)\s*$": ["Nggak apa? Jangan singkat gitu~"],
        r"^gpp\s*$": ["Gapapi~ Tapi cerita dong~"],
        r"^lah\s*$": ["Lah apa? Jangan 'lah' terus~"],
        r"^jir\s*$": ["Jir apa? Jangan panggil gitu, aneh~"],
        r"^btw\s*$": ["Btw apa? Ayo cerita~"],
        r"^ohh?\s*$": ["Oh apa? Jangan cuma 'oh'~"],
        r"^(gimana|gmn)\s*$": ["Gimana yang mana? Tahu dong~"],
    }
    
    for pattern, responses in patterns.items():
        if re.search(pattern, msg, re.I):
            return random.choice(responses)
    
    return None


def generate_social_response(user_message: str, user_id: str,
                              channel: str = "") -> str:
    """Generate social response: rule-based + LLM fallback."""
    social_memory = load_social_memory(user_id)
    
    # 1. Try deterministic response
    det = _deterministic_response(user_message, social_memory)
    if det:
        return det
    
    # 2. Fallback random
    msg_lower = user_message.lower().strip()
    if len(msg_lower) < 30 and not _is_social_query(user_message):
        # Very short, likely social
        return random.choice(_FALLBACK_SOCIAL)
    
    # 3. LLM fallback (jika message panjang / complex)
    # Tapi skip dulu karena quota habis — return fallback general
    return random.choice(_FALLBACK_SOCIAL)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        print(generate_social_response(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: python social_generator.py <message> <user_id>")
