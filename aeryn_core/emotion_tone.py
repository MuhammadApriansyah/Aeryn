"""V27.7 — EmotionTone: tensor emosi memengaruhi gaya jawaban Aeryn.

Tensor emosi (dari cognitive core, leaky integration teks nyata) dipetakan
ke arahan nada di system prompt. Deterministik, skala kecil, mudah dimatikan
(AERYN_EMOTION_TONE=0).

Mapping:
- frustrasi tinggi / valence negatif + arousal tinggi → sangat ringkas,
  langsung solusi
- valence positif → hangat, boleh sedikit ekspresif
- arousal rendah → struktur jelas, langkah bernomor
- default → baseline metodis hangat (tanpa arahan tambahan)
"""
import os


def tone_directive(snapshot: dict) -> str:
    """Snapshot tensor → arahan nada untuk system prompt. Kosong = baseline."""
    if not snapshot:
        return ""
    if os.getenv("AERYN_EMOTION_TONE", "1").lower() in ("0", "false"):
        return ""

    def get(*names, default=0.0):
        for n in names:
            for k, v in snapshot.items():
                if n in k.lower() and isinstance(v, (int, float)):
                    return max(-1.0, min(1.0, float(v)))
        return default

    valence = get("valence", "positiv", "pleasant")
    arousal = get("arousal", "activation", "energy")
    frustration = get("frustrasi", "frustration", "anger", "negative")

    directives = []
    if frustration > 0.4 or (valence < -0.3 and arousal > 0.4):
        directives.append(
            "NADA: pengguna tampak frustrasi — jawaban SANGAT ringkas, "
            "langsung solusi, tanpa pembukaan; akui kendala dengan tenang.")
    elif valence > 0.3:
        directives.append(
            "NADA: suasana positif — jawaban hangat dan boleh sedikit "
            "ekspresif, tetap presisi.")
    elif arousal < -0.3:
        directives.append(
            "NADA: gunakan struktur jelas (langkah bernomor), kalimat pendek.")
    if not directives:
        return ""
    return ("\n\n## Arahan nada (dari state emosi saat ini)\n"
            + " ".join(directives))
