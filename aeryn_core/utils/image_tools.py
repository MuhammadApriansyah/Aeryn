"""V39.3 — Image understanding via Nous inference (vision-capable model).

Tool `image_understand`: kirim URL/path gambar + pertanyaan ke model
vision. Endpoint sama dengan chat (inference-api.nousresearch.com) dengan
content image_url — model vision di sisi Nous yang memproses.

Guard:
- scheme http(s)/path dalam sandbox saja
- ukuran file lokal maks 8MB
- marker sensitif pada pertanyaan tetap diblokir
"""
import base64
import json
import os
import urllib.error
import urllib.request

INFERENCE_BASE = "https://inference-api.nousresearch.com/v1"
VISION_MODEL = "stealth/ox-alpha"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def _load_key() -> str:
    # sumber sama dengan model_client: env → auth.json agent_key
    key = os.environ.get("NOUS_API_KEY", "")
    if key:
        return key
    try:
        auth = json.load(open(os.path.expanduser("~/.hermes/auth.json")))
        return auth["providers"]["nous"].get("agent_key", "")
    except Exception:
        return ""


def _to_data_url(path: str) -> str:
    from aeryn_core.safety.safety_engine import check_path
    ok, reason = check_path(path, "read",
                            ["~/aeryn-core-agent", "~/webnovel-platform",
                             "~/Downloads"])
    if not ok:
        raise PermissionError(reason)
    raw = open(os.path.expanduser(path), "rb").read()
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError(f"gambar terlalu besar ({len(raw)//1024//1024}MB)")
    b64 = base64.b64encode(raw).decode()
    ext = os.path.splitext(path)[1].lstrip(".").lower() or "png"
    return f"data:image/{ext};base64,{b64}"


def image_understand(image_source: str, question: str = "Jelaskan gambar ini.") -> dict:
    """image_source: URL http(s) ATAU path file dalam sandbox."""
    question = str(question or "").strip() or "Jelaskan gambar ini."
    low = question.lower()
    for marker in ("password", "api_key", "token", "secret", ".env"):
        if marker in low:
            return {"ok": False,
                    "error": f"pertanyaan menyinggung '{marker}' — tidak "
                             f"diizinkan"}

    if image_source.startswith(("http://", "https://")):
        img_field = {"type": "image_url",
                     "image_url": {"url": image_source}}
    elif image_source.startswith("/") or image_source.startswith("~"):
        try:
            img_field = {"type": "image_url",
                         "image_url": {"url": _to_data_url(image_source)}}
        except (PermissionError, ValueError, OSError) as e:
            return {"ok": False, "error": str(e)[:200]}
    else:
        return {"ok": False,
                "error": "image_source harus URL http(s) atau path file"}

    key = _load_key()
    if not key:
        return {"ok": False, "error": "NOUS_API_KEY tidak tersedia"}

    payload = json.dumps({
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question[:500]},
            img_field]}],
        "max_tokens": 600}).encode()
    req = urllib.request.Request(
        INFERENCE_BASE + "/chat/completions", data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "aeryn-core/39 (+security-kernel)"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            out = json.loads(r.read())
        text = str(out["choices"][0]["message"].get("content") or "")
        return {"ok": True, "answer": text[:4000]}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read()[:120]}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:150]}


IMAGE_SCHEMA = {
    "type": "function", "function": {"name": "image_understand",
    "description": ("Pahami/gambarkan sebuah GAMBAR dari URL http(s) atau "
                    "path file dalam sandbox. Kirim juga pertanyaan spesifik "
                    "tentang gambarnya."),
    "parameters": {"type": "object", "properties": {
        "image_source": {"type": "string", "description": "URL atau path "
                         "gambar"},
        "question": {"type": "string", "description": "pertanyaan tentang "
                     "gambar"}},
        "required": ["image_source"]}},
}
