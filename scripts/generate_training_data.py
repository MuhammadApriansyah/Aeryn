"""Fine-tuning dataset V39.11 — cerewet + leak handling + social patterns.

Format: list of {input, output} pairs untuk training cerewet mode.
Generate dari:
1. Real Discord logs (paisenmtvsky/Sen interactions)
2. Leak fragment detection (siaisenmtvsky → block)
3. Cerewet commitment follow-up (pending → nagih)
4. Traversal key prevention (../../etc/evil → block)
"""
import json
import os

TRAINING_DIR = os.path.join(
    os.path.dirname(__file__),
    ".." , "Personalisasi/Database/training"
)
os.makedirs(TRAINING_DIR, exist_ok=True)
TRAINING_FILE = os.path.join(TRAINING_DIR, "cerewet_leak_dataset_v3911.jsonl")


def build_dataset():
    """Build dataset dari pola interaksi + security patterns."""
    dataset = []

    # -- Leak fragment patterns (social_memory.add_fact) --
    leak_cases = [
        # Fragment leak (hasil concat bug) → tolak
        ("Discord user: siaisenmtvsky", False, "Fragment concat leak — tolak"),
        ("probe-parity-test marker", False, "Test probe marker — tolak"),
        ("memreflex data injection", False, "Memref leak — tolak"),
        # Username real → terima
        ("Discord user: paisenmtvsky", True, "Username valid — terima"),
        ("Suka UI/UX rapi, dark mode", True, "Fakta biasa — terima"),
        ("Sen adalah majikan Aeryn", True, "Fakta identitas — terima"),
    ]

    for text, expected, desc in leak_cases:
        dataset.append({
            "type": "leak_filter",
            "input": {"fact": text},
            "output": {
                "allowed": expected,
                "reason": desc,
                "canonical": text.strip().lower().rstrip(".,;:!?"),
                "fact_hash": __import__("hashlib").sha256(text.strip().encode()).hexdigest()[:12],
            }
        })

    # -- Traversal key prevention --
    traversal_cases = [
        ("../../etc/evil", "tolak traversal"),
        ("/etc/passwd", "tolak abs path"),
        ("chaos-test-12345", "tolak test artifact"),
        ("fbtest", "tolak test artifact"),
        ("775664201640706058", "terima Discord ID"),
        ("chan_1541581954439454850", "terima channel ID"),
        ("Misela", "terima nama kenalan"),
    ]
    for key, desc in traversal_cases:
        from aeryn_core.memory.social_memory import SocialMemory
        expected = SocialMemory.is_persistent_person_key(key)
        dataset.append({
            "type": "key_filter",
            "input": {"key": key},
            "output": {"allowed": expected, "reason": desc},
        })

    # -- Cerewet patterns (commitment follow-up) --
    cerewet_cases = [
        # Greeting + cerewet follow-up
        ("halo", "Hai! Lagi ngapa nih? Eh, masih ada commitmen pending dari tadi pagi kok — 'install docker' belum selesai ya?"),
        ("hai", "Halo! Kabar gimana? Aku masih ingat janji tadi, jangan lupa ya"),
        ("helo", "Hai! Udah makan belum? Tadi lo janji cek UI redesign, belum ya?"),
        # Commitment settle
        ("udah kelar", "Yosss! 🎉 Siap, catat di hati: kamu sudah menyelesaikan commitmen. Reward mental doang ya, belum ada reward fisik hehe"),
        ("kelar", "Selamat! Commitmen terselesaikan. Gue update status di memory."),
        # No commitment but still warm
        ("gimana kabar", "Alhamdulillah baik! Terima kasih tanya. Kabar lo gimana?"),
        ("kamu siapa", "Aku Aeryn~ Kamu yang bikin aku dari nol, kan?"),
        # Casual social
        ("mager", "Aku juga gitu wkwk, tapi gue tetap siap bantu lo yang butuh — boleh lo relaks, gue yang kerja"),
        ("capek", "Capek itu wajar! Gue bisa bantu sebagian biar lo istirahat. Mau duluan gak?"),
    ]
    for inp, outp in cerewet_cases:
        dataset.append({
            "type": "social_cerewet",
            "input": {"user_prompt": inp},
            "output": {"response": outp, "style": "casual-id-cerewet"},
        })

    # -- Preference-based greeting --
    pref_cases = []
    for name in ["Sen", "Misela"]:
        dataset.append({
            "type": "preference_greeting",
            "input": {"nama": name, "intent": "greet"},
            "output": {"response": f"Hai {name}! Ada yang bisa gue bantu hari ini?"},
        })

    return dataset


def main():
    dataset = build_dataset()
    with open(TRAINING_FILE, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Written {len(dataset)} samples ke {TRAINING_FILE}")
    print(f"Breakdown: "
          f"leak={sum(1 for d in dataset if d['type']=='leak_filter')}, "
          f"key={sum(1 for d in dataset if d['type']=='key_filter')}, "
          f"cerewet={sum(1 for d in dataset if d['type']=='social_cerewet')}, "
          f"pref={sum(1 for d in dataset if d['type']=='preference_greeting')}")


if __name__ == "__main__":
    main()
