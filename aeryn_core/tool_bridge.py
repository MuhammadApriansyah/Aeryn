"""ToolBridge — Registry tool dengan graduation tracking (bridged→shadowing→native).

Fase 1 hybrid: tools aman diimplement native Python langsung (tanpa dependensi
Hermes), tiap tool punya metadata graduation + safety tier utk div4 governance.
"""
import json
import os
import re
import urllib.request
from pathlib import Path


# ── Safety tiers (div4 governance membaca ini) ──────────────────────────
TIER_SAFE = "safe"          # read-only, eksternal: boleh graduate cepat
TIER_FS = "fs"              # akses filesystem terbatas
TIER_POWER = "power"        # exec/network tulis — butuh track record panjang


class ToolGraduationRegistry:
    def __init__(self, state_path: str = None):
        self.tools = {}
        self.state_path = state_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/tool_graduation.json")
        self._load_state()

    def _load_state(self):
        try:
            self.grad = json.loads(open(self.state_path).read())
        except (OSError, ValueError):
            self.grad = {}

    def _save_state(self):
        Path(self.state_path).parent.mkdir(parents=True, exist_ok=True)
        json.dump(self.grad, open(self.state_path, "w"), indent=1)

    def register(self, name, handler, schema, tier=TIER_SAFE):
        st = self.grad.get(name, {"status": "bridged", "success": 0, "fail": 0})
        self.tools[name] = {"handler": handler, "schema": schema, "tier": tier,
                            "status": st["status"], "success": st["success"], "fail": st["fail"]}
        return self

    def schemas(self):
        return [t["schema"] for t in self.tools.values()]

    def execute(self, name, args):
        t = self.tools.get(name)
        if not t:
            return {"error": f"unknown tool: {name}"}
        try:
            result = t["handler"](**args)
            t["success"] += 1
            ok = True
        except Exception as e:
            result = {"error": f"{type(e).__name__}: {e}"}
            t["fail"] += 1
            ok = False
        self._record(name, ok)
        return result

    def _record(self, name, ok):
        """Track record → auto-promote bridged→shadowing saat 5 sukses & <2 gagal."""
        t = self.tools[name]
        if ok and t["status"] == "bridged" and t["success"] >= 5 and t["fail"] <= 2:
            t["status"] = "shadowing"
        self.grad[name] = {"status": t["status"], "success": t["success"], "fail": t["fail"]}
        self._save_state()

    def promote(self, name, status):
        assert status in ("bridged", "shadowing", "native")
        self.tools[name]["status"] = status
        self.grad[name] = {k: self.tools[name][k] for k in ("status", "success", "fail")}
        self._save_state()


# ── Native tools fase 1 (aman, tanpa Hermes) ────────────────────────────

def _web_search(query: str, max_results: int = 5):
    """DuckDuckGo Lite — tanpa API key. Link dibungkus redirect uddg=."""
    url = "https://lite.duckduckgo.com/lite/?q=" + urllib.request.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (aeryn-core)"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    results = []
    for m in re.finditer(
            r'<a[^>]+href="([^"]*uddg%3D[^"]+|[^"]*uddg=[^"]+)"[^>]*>(.*?)</a>', html):
        raw = m.group(1).replace("&amp;", "&")
        qm = re.search(r"uddg(?:%3D|=)([^&]+)", raw)
        target = urllib.request.unquote(qm.group(1)) if qm else raw
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if target.startswith("http"):
            results.append({"title": text, "url": target})
        if len(results) >= max_results:
            break
    return {"results": results}


def _http_get(url: str, max_bytes: int = 200_000):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (aeryn-core)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return {"status": r.status, "content_type": r.headers.get("content-type", ""),
                "body": r.read(max_bytes).decode("utf-8", "replace")}


def make_fs_read(roots):
    """File reader sandboxed — hanya path di bawah roots yang diizinkan."""
    allowed = [Path(os.path.expanduser(r)).resolve() for r in roots]

    def fs_read(path: str, max_bytes: int = 50_000):
        p = Path(os.path.expanduser(path)).resolve()
        if not any(p == root or root in p.parents for root in allowed):
            raise PermissionError(f"path outside sandbox roots: {p}")
        return {"path": str(p), "size": p.stat().st_size,
                "content": p.read_text(errors="replace")[:max_bytes]}
    return fs_read


def build_default_registry(sandbox_roots=None):
    reg = ToolGraduationRegistry()
    reg.register("web_search", _web_search, {
        "type": "function", "function": {"name": "web_search",
        "description": "Cari informasi di web. Returns list {title,url}.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]}}}, TIER_SAFE)
    reg.register("http_get", _http_get, {
        "type": "function", "function": {"name": "http_get",
        "description": "GET sebuah URL, returns status+body text.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]}}}, TIER_SAFE)
    if sandbox_roots:
        reg.register("fs_read", make_fs_read(sandbox_roots), {
            "type": "function", "function": {"name": "fs_read",
            "description": "Baca file teks dalam sandbox folder yang diizinkan.",
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string"}}, "required": ["path"]}}}, TIER_FS)
    return reg
