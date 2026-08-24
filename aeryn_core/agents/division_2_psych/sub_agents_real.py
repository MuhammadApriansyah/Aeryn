import json
import re

_POSITIVE = {"senang", "bahagia", "suka", "cinta", "tenang", "syukur", "aman", "legа", "lega", "puas", "semangat", "mantap", "keren", "bagus", "thanks", "terima kasih", "alhamdulillah"}
_NEGATIVE = {"marah", "kesal", "benci", "sedih", "takut", "cemas", "stres", "stress", "capek", "lelah", "benci", "parah", "jelek", "buruk", "gagal", "salah", "benci", "frustrasi", "kecewa", "putus asa", "bingung"}
_URGENT = {"sekarang", "segera", "darurat", "urgent", "cepat", "asap", "deadline"}
_QUESTION = {"apa", "kenapa", "bagaimana", "gimana", "kapan", "dimana", "siapa", "berapa", "kok"}


class SubAgentLeakyIntegratorAccumulator:
    """Leaky integrator NYATA: menurunkan tensor emosi dari teks percakapan.

    Menggantikan mock_state hardcoded. Skor diturunkan dari leksikon afektif
    + sinyal struktural (panjang, tanda seru, pertanyaan), lalu di-decay
    eksponensial terhadap state sebelumnya (leaky integration sungguhan).
    """

    def __init__(self, decay: float = 0.7):
        self.decay = decay
        self._prev_state: dict[str, float] = {}

    def analyze_text(self, texts: list[str]) -> dict:
        pos = neg = urg = chars = excl = ques = 0
        n = max(1, len(texts))
        for t in texts:
            low = t.lower()
            words = set(re.findall(r"\w+", low))
            pos += len(words & _POSITIVE)
            neg += len(words & _NEGATIVE)
            urg += len(words & _URGENT)
            chars += len(t)
            excl += t.count("!")
            ques += sum(1 for w in words if w in _QUESTION)

        valence = (pos - neg) / (pos + neg + 1.0)          # -1..1
        arousal = min(1.0, (excl * 0.3 + urg * 0.4 + chars / (n * 400.0)))
        interrogative = min(1.0, ques / (n * 2.0))

        return {
            "valence": round(valence, 4),
            "arousal": round(arousal, 4),
            "interrogative": round(interrogative, 4),
        }

    def execute_sub_brain_reasoning(self, emotional_state_json: str, analyzed: dict | None = None, session_id: str = "default") -> dict:
        if analyzed is None:
            # Kompatibilitas mundur: input JSON lama
            try:
                state = json.loads(emotional_state_json) if emotional_state_json else {}
            except Exception:
                state = {}
            pragmatism = float(state.get("pragmatism", 1.0)) * 0.9
            return {"decayed_pragmatism": round(pragmatism, 4), "integrator_metrics": {"sub_agent_class": "LEAKY_INTEGRATOR"}}

        prev = self._prev_state.get(session_id, {"pragmatism": 0.8, "hostility": 0.1, "focus": 0.7, "compassion": 0.6})

        # Pemetaan afek → tensor 4-dimensi
        target_pragmatism = 0.5 + 0.5 * (analyzed["valence"] * 0.5 + (1 - analyzed["interrogative"]) * 0.5)
        target_hostility = max(0.0, min(1.0, (-analyzed["valence"]) * 0.6))
        target_focus = max(0.0, min(1.0, 0.4 + analyzed["arousal"] * 0.5 + analyzed["interrogative"] * 0.2))
        target_compassion = max(0.0, min(1.0, 0.55 + analyzed["valence"] * 0.35))

        # Leaky integration: menuju target, tidak melompat
        def leak(prev_v, target_v):
            return round(prev_v * self.decay + target_v * (1 - self.decay), 4)

        new_state = {
            "pragmatism": leak(prev["pragmatism"], target_pragmatism),
            "hostility": leak(prev["hostility"], target_hostility),
            "focus": leak(prev["focus"], target_focus),
            "compassion": leak(prev["compassion"], target_compassion),
        }
        self._prev_state[session_id] = new_state

        return {
            "decayed_pragmatism": new_state["pragmatism"],
            "emotional_tensor": new_state,
            "affect_analysis": analyzed,
            "integrator_metrics": {"sub_agent_class": "LEAKY_INTEGRATOR", "source": "text_derived"},
        }


class SubAgentMentalHealthCore:
    """Stabilitas kognitif dari pola percakapan nyata (bukan keyword 'alert' saja)."""

    def __init__(self):
        self._baseline_len: float | None = None

    def execute_sub_brain_reasoning(self, history_logs: list) -> dict:
        stability_score = 1.0
        if history_logs:
            lens = [len(str(l)) for l in history_logs[-10:]]
            avg_len = sum(lens) / len(lens)
            if self._baseline_len is not None:
                # Lonjakan panjang mendadak = potensi distorsi
                ratio = avg_len / max(1.0, self._baseline_len)
                if ratio > 4.0 or ratio < 0.15:
                    stability_score -= 0.2
            self._baseline_len = avg_len

            joined = " ".join(str(l).lower() for l in history_logs[-10:])
            distress_markers = sum(joined.count(k) for k in ("tolong", "tidak sanggup", "putus asa", "help me", "can't take"))
            stability_score -= min(0.4, distress_markers * 0.1)

        return {
            "cognitive_stability": max(0.0, round(stability_score, 2)),
            "mhc_metrics": {"sub_agent_class": "MENTAL_HEALTH_CORE", "source": "pattern_analysis"},
        }


class SubAgentPeaceKeeperEngine:
    """Beban tugas nyata dengan penalti deadline-berat."""

    HEAVY_WORDS = ("urgent", "darurat", "segera", "asap", "critical")

    def __init__(self, per_task_load: float = 0.12, heavy_multiplier: float = 1.8, ceiling: float = 0.95):
        self.per_task_load = per_task_load
        self.heavy_multiplier = heavy_multiplier
        self.ceiling = ceiling
        self._completed: int = 0

    def mark_completed(self, n: int = 1):
        self._completed += n

    def execute_sub_brain_reasoning(self, open_tasks: list) -> dict:
        tasks = [str(t) for t in (open_tasks or [])]
        heavy = sum(1 for t in tasks if any(w in t.lower() for w in self.HEAVY_WORDS))
        load = min(
            self.ceiling,
            len(tasks) * self.per_task_load + heavy * self.per_task_load * (self.heavy_multiplier - 1.0),
        )
        # Tugas selesai memberi sedikit ruang napas
        relief = min(0.2, self._completed * 0.02)
        stress_level = max(0.0, load - relief)
        return {
            "internal_stress_index": round(stress_level, 4),
            "task_count": len(tasks),
            "heavy_tasks": heavy,
            "peace_metrics": {"sub_agent_class": "PEACE_KEEPER"},
        }
