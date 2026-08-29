#!/usr/bin/env python3
"""Credential health check berkala untuk chain provider Aeryn-Core.

Untuk SETIAP kandidat unik di rantai ModelClient._endpoint_candidates():
kirim chat completion mini (max_tokens=5, prompt 'ping', timeout 20s)
dengan UA kustom (Cloudflare memblok python-urllib). Klasifikasi hasil:

  OK | AUTH_FAIL | RATE_LIMITED | SERVER_ERROR | TIMEOUT | UNREACHABLE |
  CLIENT_ERROR | NO_KEY | SKIPPED_BUDGET

Output:
  - dict {provider/model: {status, latency_ms, checked_at}}
  - one-line summary siap masuk nightly digest, mis.:
      "NOUS ox-alpha OK 812ms | GROQ gpt-oss-20b RATE_LIMITED | NVIDIA NO_KEY"
  - JSON tersimpan ke Personalisasi/health/latest.json

CLI: --json (print JSON penuh), --quiet (hanya exit-code; 0 semua OK/
rate-limited wajar, 1 ada AUTH_FAIL).
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from aeryn_core.utils.model_client import ModelClient  # noqa: E402

USER_AGENT = "aeryn-core/27 (+https://github.com/sen/aeryn-core)"
PROBE_TIMEOUT_S = 20          # per-request — satu provider hang tidak boleh menggantung keseluruhan
TOTAL_BUDGET_S = 240          # budget ketat seluruh run; sisanya ditandai SKIPPED_BUDGET
INTER_PROVIDER_SLEEP_S = 1    # rate-limit friendly antar-provider

# Provider kanonik + env var key-nya (utk deteksi NO_KEY saat tak muncul di chain)
CANONICAL_PROVIDERS = {
    "NOUS": "NOUS_API_KEY",
    "GEMINI": "GEMINI_API_KEY",
    "GROQ": "GROQ_API_KEY",
    "NVIDIA": "NVIDIA_API_KEY",
}


def _provider_for_url(base_url: str) -> str:
    host = base_url.split("//")[-1].split("/")[0]
    if "nousresearch" in host:
        return "NOUS"
    if "googleapis" in host:
        return "GEMINI"
    if "groq.com" in host:
        return "GROQ"
    if "nvidia.com" in host:
        return "NVIDIA"
    if "openrouter" in host:
        return "OPENROUTER"
    return host.upper()


def build_candidates():
    """Kandidat unik dari chain ModelClient + baris NO_KEY untuk provider
    kanonik yang hilang (key env-nya kosong).

    Return list of dict {provider, base_url, model, api_key} — urutan chain dipertahankan.
    """
    mc = ModelClient()
    raw = mc._endpoint_candidates()  # sudah menjalankan _load_hermes_env (env+auth.json)
    cands, seen = [], set()
    for url, model, api_key in raw:
        url = url.rstrip("/")
        k = (url, model)
        if k in seen:
            continue
        seen.add(k)
        cands.append({"provider": _provider_for_url(url), "base_url": url,
                      "model": model, "api_key": api_key})
    # NO_KEY untuk provider kanonik yang tidak masuk chain karena tanpa key
    present = {c["provider"] for c in cands}
    for prov, env_name in CANONICAL_PROVIDERS.items():
        if prov not in present and not os.getenv(env_name):
            cands.append({"provider": prov, "base_url": "", "model": "-",
                          "api_key": ""})
    return cands


def classify_http_error(code: int) -> str:
    """Klasifikasi status dari HTTP status code."""
    if code in (401, 403):
        return "AUTH_FAIL"
    if code == 429:
        return "RATE_LIMITED"
    if code >= 500:
        return "SERVER_ERROR"
    return "CLIENT_ERROR"


def probe_endpoint(base_url: str, model: str, api_key: str,
                   timeout_s: float = PROBE_TIMEOUT_S):
    """Satu chat completion mini. Return (status, latency_ms).

    Tidak pernah raise — semua exception jadi status klasifikasi.
    """
    payload = {"model": model,
               "messages": [{"role": "user", "content": "ping"}],
               "max_tokens": 5}
    if "gpt-oss" in model:
        payload["reasoning_effort"] = "low"  # reasoning default makan token → content kosong
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            # Cloudflare memblok UA Python-urllib (error 1010) — WAJIB custom UA
            "User-Agent": USER_AGENT,
        },
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            json.loads(resp.read())
        return ("OK", int((time.monotonic() - t0) * 1000))
    except urllib.error.HTTPError as e:
        return (classify_http_error(e.code), int((time.monotonic() - t0) * 1000))
    except TimeoutError:
        # socket.timeout & urlopen timeout masuk sini
        return ("TIMEOUT", int((time.monotonic() - t0) * 1000))
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), TimeoutError):
            return ("TIMEOUT", int((time.monotonic() - t0) * 1000))
        return ("UNREACHABLE", int((time.monotonic() - t0) * 1000))
    except OSError:
        # DNS gagal / koneksi refused / socket.timeout lama
        return ("UNREACHABLE", int((time.monotonic() - t0) * 1000))
    except Exception:
        return ("CLIENT_ERROR", int((time.monotonic() - t0) * 1000))


def run_health_check(candidates=None):
    """Probes seluruh kandidat dengan budget waktu ketat.

    Return ({f"{provider}/{model}": {status, latency_ms, checked_at}}, summary_line).
    """
    results = {}
    deadline = time.monotonic() + TOTAL_BUDGET_S
    for i, cand in enumerate(candidates if candidates is not None else build_candidates()):
        name = f"{cand['provider']}/{cand['model']}"
        checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not cand["api_key"]:
            results[name] = {"status": "NO_KEY", "latency_ms": None,
                             "checked_at": checked_at}
            continue
        if i > 0 and time.monotonic() < deadline:
            time.sleep(INTER_PROVIDER_SLEEP_S)  # jeda antar-provider
        if time.monotonic() >= deadline:
            results[name] = {"status": "SKIPPED_BUDGET", "latency_ms": None,
                             "checked_at": checked_at}
            continue
        remaining = min(PROBE_TIMEOUT_S, max(1.0, deadline - time.monotonic()))
        status, lat = probe_endpoint(cand["base_url"], cand["model"],
                                     cand["api_key"], timeout_s=remaining)
        results[name] = {"status": status, "latency_ms": lat,
                         "checked_at": checked_at}
    return results, build_summary(results)


def _short_model(model: str) -> str:
    return model.rsplit("/", 1)[-1] if "/" in model else model


def build_summary(results: dict) -> str:
    """One-line digest: 'NOUS ox-alpha OK 812ms | GROQ gpt-oss-20b RATE_LIMITED'."""
    parts = []
    for name, r in results.items():
        prov, _, model = name.partition("/")
        seg = f"{prov} {_short_model(model)} {r['status']}"
        if r.get("latency_ms") is not None:
            seg += f" {r['latency_ms']}ms"
        parts.append(seg)
    return " | ".join(parts)


def save_results(results: dict) -> Path:
    out_dir = REPO / "Personalisasi" / "health"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "latest.json"
    path.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "results": results}, indent=2, ensure_ascii=False) + "\n")
    return path


def exit_code(results: dict) -> int:
    """0 = semua OK/rate-limited wajar; 1 = ada AUTH_FAIL."""
    return 1 if any(r["status"] == "AUTH_FAIL" for r in results.values()) else 0


def main():
    ap = argparse.ArgumentParser(
        description="Credential health check chain provider Aeryn-Core")
    ap.add_argument("--json", action="store_true", help="print JSON penuh")
    ap.add_argument("--quiet", action="store_true", help="hanya exit-code")
    args = ap.parse_args()

    results, summary = run_health_check()
    save_results(results)

    if args.quiet:
        sys.exit(exit_code(results))
    if args.json:
        print(json.dumps({"summary": summary, "results": results},
                         indent=2, ensure_ascii=False))
    else:
        print(summary)
        print(f"[saved] Personalisasi/health/latest.json", file=sys.stderr)
    sys.exit(exit_code(results))


if __name__ == "__main__":
    main()
