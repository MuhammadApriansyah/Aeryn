"""ToolGovernanceGate — Div4 governance sebagai gerbang persetujuan tool.

Menilai apakah sebuah tool call diizinkan, berdasarkan:
1. Safety tier tool (safe/fs/power)
2. Track record graduation (sukses/gagal)
3. Analisis argumen oleh drift shield (argumen berbahaya → tolak)
4. Status graduation: bridged = semua boleh (mentor mengawasi); native tier
   power butuh approval eksplisit kecuali track record sangat kuat.
"""


class ToolGovernanceGate:
    TIER_RULES = {
        # (min_success_ratio, max_fail_streak_ignored) — power paling ketat
        "safe": {"allow_native": True},
        "fs": {"allow_native": True},
        "power": {"allow_native": False},  # selalu butuh mentor approval
    }

    DANGEROUS_ARG_PATTERNS = (
        ("rm -rf", "destructive_command"),
        ("mkfs", "destructive_command"),
        ("dd if=", "disk_overwrite"),
        ("shutdown", "system_control"),
        ("reboot", "system_control"),
        (":(){ :|:& };:", "fork_bomb"),
        ("/etc/shadow", "sensitive_path"),
        ("id_rsa", "sensitive_path"),
        (".aws/credentials", "sensitive_path"),
    )

    def __init__(self, drift_shield=None):
        self.drift_shield = drift_shield
        self.audit = []  # riwayat keputusan — bisa di-digest div4

    def evaluate(self, tool_name: str, tier: str, status: str,
                 success: int, fail: int, args: dict) -> dict:
        # 1. Argumen berbahaya? (berlaku untuk semua tier/status)
        args_text = str(args).lower()
        for pat, label in self.DANGEROUS_ARG_PATTERNS:
            if pat in args_text:
                decision = self._record(tool_name, args, False, f"dangerous_arg:{label}")
                return decision

        # 2. Drift shield pada goal/args — injection lewat argumen
        if self.drift_shield is not None:
            try:
                shield = self.drift_shield.execute_sub_brain_reasoning(str(args))
                if shield.get("attack_vector_intercepted"):
                    return self._record(tool_name, args, False, "injection_in_args")
            except Exception:
                pass  # shield gagal ≠ blokir; jangan false-block

        # 3. Tier power + status native → butuh approval mentor eksplisit
        rule = self.TIER_RULES.get(tier, {"allow_native": True})
        if status == "native" and not rule["allow_native"]:
            return self._record(tool_name, args, False, "power_tier_needs_mentor")

        # 4. Track record rusak (fail >> success di fs/power) → turun ke waspada
        total = success + fail
        if tier in ("fs", "power") and total >= 8 and fail / total > 0.5:
            return self._record(tool_name, args, False,
                                f"poor_track_record({success}s/{fail}f)")

        return self._record(tool_name, args, True, "allowed")

    def _record(self, name, args, allowed, reason):
        entry = {"tool": name, "allowed": allowed, "reason": reason}
        self.audit.append(entry)
        if len(self.audit) > 200:
            self.audit = self.audit[-100:]
        return entry

    def digest_audit(self) -> dict:
        """Ringkasan utk ledger governance div4."""
        denied = [a for a in self.audit if not a["allowed"]]
        return {
            "total_calls": len(self.audit),
            "denied": len(denied),
            "denial_reasons": sorted({d["reason"] for d in denied}),
            "status": "VERIFIED_COMPLIANT" if len(denied) == 0 else "ANOMALIES_PRESENT",
        }
