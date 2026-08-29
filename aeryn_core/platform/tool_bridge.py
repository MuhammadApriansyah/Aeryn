"""ToolBridge — Registry tool dengan graduation tracking (bridged→shadowing→native).

Fase 1 hybrid: tools aman diimplement native Python langsung (tanpa dependensi
Hermes), tiap tool punya metadata graduation + safety tier utk div4 governance.
"""
import json
import os
import re
import urllib.parse
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
        """V37.3 — validasi bentuk entry: harus dict {status,success,fail}.

        Dulu langsung dipercaya; file yang tertimpa format asing (mis.
        list paritas) membuat status tool korup diam-diam."""
        try:
            raw = json.loads(open(self.state_path).read())
            self.grad = {
                name: st for name, st in raw.items()
                if isinstance(st, dict)
                and isinstance(st.get("status"), str)
                and isinstance(st.get("success"), int)
                and isinstance(st.get("fail"), int)
            }
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
    """V33 — Bing scrape (DuckDuckGo diblok dari proot ini: SSL EOF/abort).

    Bing return redirect link (bing.com/ck/a?...u=a1<base64>) — decode
    base64 di param u untuk dapat URL asli.
    V38.6 — cap query 400 char (query ekstrem = biaya + hasil sampah).
    """
    if not isinstance(query, str) or not query.strip():
        return {"results": [], "note": "query kosong"}
    if len(query) > 400:
        return {"error": f"query terlalu panjang ({len(query)} > 400)"}
    url = ("https://www.bing.com/search?q=" +
           urllib.parse.quote(query) + "&count=" + str(max_results + 2))
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    })
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    results = []
    seen = set()
    # setiap hasil: <h2 ...><a ... href="REDIRECT" ...>TITLE</a></h2>
    for m in re.finditer(
            r'<h2[^>]*><a[^>]+href="(https://www\.bing\.com/ck/a\?[^"]+)"[^>]*>(.*?)</a>',
            html, re.S):
        raw = m.group(1).replace("&amp;", "&")
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        # URL asli ada di param u=a1<base64>
        qm = re.search(r"[?&]u=a1([A-Za-z0-9+/=_-]+)", raw)
        target = ""
        if qm:
            b64 = qm.group(1)
            b64 += "=" * (-len(b64) % 4)  # padding
            try:
                import base64
                target = base64.b64decode(b64).decode("utf-8", "replace")
            except Exception:
                target = ""
        if target.startswith("http") and target not in seen:
            seen.add(target)
            results.append({"title": text, "url": target})
        if len(results) >= max_results:
            break
    return {"results": results}


def _http_get(url: str, max_bytes: int = 200_000):
    # V37.4-SEC — hanya http(s); blokir file://, ftp://, data:, dsb.
    # Dulu file:///etc/passwd kebaca via urlopen (SSRF lokal).
    if not url.lower().startswith(("http://", "https://")):
        return {"error": "hanya http/https yang diizinkan"}
    # V37.5-SEC — blokir SSRF ke jaringan internal (localhost/private IP)
    import re as _re
    host_m = _re.match(r"[a-z]+://([^/:?#]+)", url, _re.I)
    if host_m:
        host = host_m.group(1).lower()
        import ipaddress as _ip
        try:
            ip = _ip.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return {"error": "akses ke IP private/internal diblokir"}
        except ValueError:
            pass  # hostname biasa, bukan IP literal
        if host in ("localhost",) or host.endswith(".local"):
            return {"error": "akses ke localhost diblokir"}
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (aeryn-core)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return {"status": r.status, "content_type": r.headers.get("content-type", ""),
                "body": r.read(max_bytes).decode("utf-8", "replace")}


def _web_read(url: str):
    """V33-T — Baca halaman web → teks artikel bersih (trafilatura).

    Melengkapi web_search: search kasih link, web_read baca isinya.
    Read-only, tanpa eksekusi konten.
    V38.4-SEC — scheme guard + blokir SSRF internal (sama dengan http_get):
    dulu web_read ke http://127.0.0.1:3010/* lolos validasi (gagal ekstraksi
    saja) — prinsipnya, jangan sampai fetch internal sama sekali.
    """
    if not url.lower().startswith(("http://", "https://")):
        return {"error": "hanya http/https yang diizinkan", "url": url}
    import re as _re
    import ipaddress as _ip
    host_m = _re.match(r"[a-z]+://([^/:?#]+)", url, _re.I)
    if host_m:
        host = host_m.group(1).lower()
        try:
            ip = _ip.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return {"error": "akses ke IP private/internal diblokir",
                        "url": url}
        except ValueError:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass
        if host in ("localhost",) or host.endswith(".local"):
            return {"error": "akses ke localhost diblokir", "url": url}
    import trafilatura
    try:
        downloaded = trafilatura.fetch_url(url)
    except Exception as e:
        return {"error": f"fetch gagal: {type(e).__name__}: {e}"[:200], "url": url}
    if not downloaded:
        return {"error": "halaman tidak bisa diambil", "url": url}
    text = trafilatura.extract(downloaded) or ""
    if not text.strip():
        return {"error": "ekstraksi kosong (kemungkinan bukan halaman artikel)",
                "url": url}
    out = {"url": url, "text": text[:20000], "chars": len(text)}
    meta = trafilatura.extract_metadata(downloaded)
    if meta:
        out["title"] = (getattr(meta, "title", "") or "")[:200]
        author = getattr(meta, "author", "") or ""
        if author:
            out["author"] = author[:120]
    return out


def make_fs_read(roots):
    """File reader sandboxed — hanya path di bawah roots yang diizinkan.

    V37.5-SEC — plus SecurityKernel: file sensitif (.env, memori pribadi,
    state internal) dilindungi BAHKAN di dalam sandbox."""
    from aeryn_core.safety.safety_engine import check_path
    allowed = [Path(os.path.expanduser(r)).resolve() for r in roots]

    def fs_read(path: str, max_bytes: int = 50_000):
        ok, reason = check_path(path, "read", roots)
        if not ok:
            raise PermissionError(reason)
        p = Path(os.path.expanduser(path)).resolve()
        if not any(p == root or root in p.parents for root in allowed):
            raise PermissionError(f"path outside sandbox roots: {p}")
        return {"path": str(p), "size": p.stat().st_size,
                "content": p.read_text(errors="replace")[:max_bytes]}
    return fs_read


def make_fs_write(sandbox_roots):
    """V35 INFRA-3 — tulis file dalam sandbox (tier fs).

    Mode overwrite penuh; path di-expand dan divalidasi ke sandbox roots.
    Parent dir otomatis dibuat. Returns dict {path, bytes_written}.
    V37.5-SEC — SecurityKernel: secret files + source dirs write-protected.
    """
    from aeryn_core.safety.safety_engine import check_path
    allowed = [Path(os.path.expanduser(r)).resolve() for r in sandbox_roots]

    def fs_write(path: str, content: str):
        ok, reason = check_path(path, "write", sandbox_roots)
        if not ok:
            raise PermissionError(reason)
        p = Path(os.path.expanduser(path)).resolve()
        if not any(p == root or root in p.parents for root in allowed):
            raise PermissionError(f"path outside sandbox roots: {p}")
        p.parent.mkdir(parents=True, exist_ok=True)
        # V38.9-SEC — TOCTOU guard: path sudah lolos kernel, tapi bisa
        # jadi SYMLINK yang di-swap setelah check. O_NOFOLLOW = gagal
        # bila komponen akhir adalah symlink (bukan mengikuti target).
        parent_fd = os.open(str(p.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            fd = os.open(p.name,
                         os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW,
                         0o644, dir_fd=parent_fd)
            with os.fdopen(fd, "wb") as f:
                f.write(content.encode("utf-8"))
            return {"ok": True, "path": str(p),
                    "bytes_written": len(content.encode("utf-8"))}
        finally:
            os.close(parent_fd)
    return fs_write


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
    reg.register("web_read", _web_read, {
        "type": "function", "function": {"name": "web_read",
        "description": ("Baca halaman web dan ekstrak teks artikel utamanya "
                        "(bersih, tanpa HTML). Pakai setelah web_search untuk "
                        "membaca isi link yang relevan."),
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]}}}, TIER_SAFE)
    if sandbox_roots:
        reg.register("fs_read", make_fs_read(sandbox_roots), {
            "type": "function", "function": {"name": "fs_read",
            "description": "Baca file teks dalam sandbox folder yang diizinkan.",
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string"}}, "required": ["path"]}}}, TIER_FS)
        reg.register("fs_write", make_fs_write(sandbox_roots), {
            "type": "function", "function": {"name": "fs_write",
            "description": ("Tulis/buat file teks di dalam sandbox folder "
                            "yang diizinkan (overwrite penuh)."),
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}},
                "required": ["path", "content"]}}}, TIER_FS)
    return reg
