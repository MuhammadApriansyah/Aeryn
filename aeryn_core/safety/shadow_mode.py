"""ShadowMode — jalankan native tool & pembanding referensi bersamaan.

Ketika sebuah tool naik ke status `shadowing`, setiap panggilan:
1. Tool utama dieksekusi (hasilnya yang dipakai agen)
2. Fungsi pembanding (checker) dieksekusi diam-diam
3. Hasil dibandingkan → paritas dicatat di ParityLedger

N kali paritas beruntun = kandidat graduation `native` (keputusan mentor).
"""
import os
import time


class ParityLedger:
    """Catatan paritas per tool — persist sederhana via registry state.

    V37.2 — records kini OPSIONAL persist ke disk. Dulu in-memory murni:
    tiap restart PM2 menghapus streak, sehingga tool shadowing tidak pernah
    mencapai 5-paritas-beruntun dan macet selamanya di status shadowing.
    """

    def __init__(self, registry, path: str = None):
        self.registry = registry  # ToolGraduationRegistry
        self.path = path          # JSON persist (opsional)
        self.records = {}         # name -> list[bool]
        if path:
            try:
                import json as _json
                with open(path) as f:
                    raw = _json.load(f)
                self.records = {k: [bool(x) for x in v[-15:]]
                                for k, v in raw.items() if isinstance(v, list)}
            except Exception:
                self.records = {}  # korup/hilang → mulai segar

    def _persist(self):
        if not self.path:
            return
        try:
            import json as _json
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                _json.dump(self.records, f)
            os.replace(tmp, self.path)
        except OSError:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass

    def record(self, tool_name: str, parity_ok: bool):
        seq = self.records.setdefault(tool_name, [])
        seq.append(parity_ok)
        if len(seq) > 30:
            self.records[tool_name] = seq[-15:]
        self._persist()
        # N paritas beruntun terakhir
        need = 5
        recent = self.records[tool_name][-need:]
        return {"consecutive": sum(recent) == need and len(recent) == need,
                "ratio": sum(self.records[tool_name]) / max(1, len(self.records[tool_name]))}

    def summary(self):
        return {name: {"runs": len(seq), "parity_ratio": round(sum(seq) / max(1, len(seq)), 2),
                       "graduation_ready": len(seq) >= 5 and all(seq[-5:])}
                for name, seq in self.records.items()}


class ShadowRunner:
    def __init__(self, registry, ledger: ParityLedger, checkers: dict = None):
        self.registry = registry
        self.ledger = ledger
        self.checkers = checkers or {}  # name -> fn(args, primary_result) -> bool

    def register_checker(self, tool_name: str, checker_fn):
        """checker_fn(args, primary_result) -> bool (True = paritas OK)."""
        self.checkers[tool_name] = checker_fn

    def run_with_shadow(self, name: str, args: dict):
        """Eksekusi utama; kalau tool berstatus shadowing & ada checker → bandingkan."""
        t = self.registry.tools[name]
        result = t["handler"](**args)

        if t["status"] == "shadowing" and name in self.checkers:
            t0 = time.time()
            try:
                ok = bool(self.checkers[name](args, result))
                shadow_err = None
            except Exception as e:
                ok, shadow_err = False, str(e)[:120]
            verdict = self.ledger.record(name, ok)
            t["shadow"] = {"last_parity": ok, "shadow_err": shadow_err,
                           "overhead_ms": int((time.time() - t0) * 1000),
                           **verdict}
        return result
