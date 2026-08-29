"""Test V36 — Credential health check chain provider (scripts/credential_health.py).

Semua unit test memakai mock urllib — TIDAK memanggil API nyata.
"""
import io
import json
import os
import sys
import urllib.error
import urllib.request
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.archive.credential_health as ch


# ---------------------------------------------------------------- helpers

def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://x/chat/completions", code,
                                  "err", {}, io.BytesIO(b"{}"))


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ok_resp(content='{"choices":[{"message":{"content":"pong"}}]}'):
    return _FakeResp(content.encode())


@pytest.fixture()
def no_sleep(monkeypatch):
    monkeypatch.setattr(ch.time, "sleep", lambda *_: None)


# ------------------------------------------------- klasifikasi HTTPError

@pytest.mark.parametrize("code,expected", [
    (401, "AUTH_FAIL"), (403, "AUTH_FAIL"),
    (429, "RATE_LIMITED"),
    (500, "SERVER_ERROR"), (502, "SERVER_ERROR"), (503, "SERVER_ERROR"),
    (400, "CLIENT_ERROR"), (404, "CLIENT_ERROR"),
])
def test_classify_http_error(code, expected):
    assert ch.classify_http_error(code) == expected


def test_probe_ok(monkeypatch):
    calls = {}

    def fake_urlopen(req, timeout=None):
        calls["ua"] = req.headers.get("User-agent") or req.headers.get("User-Agent")
        calls["timeout"] = timeout
        return _ok_resp()

    monkeypatch.setattr(ch.urllib.request, "urlopen", fake_urlopen)
    status, lat = ch.probe_endpoint("https://x/v1", "m-1", "k", timeout_s=20)
    assert status == "OK"
    assert isinstance(lat, int)
    # WAJIB custom UA — Cloudflare blok python-urllib
    assert calls["ua"] and "python-urllib" not in calls["ua"]
    assert "aeryn-core" in calls["ua"]
    assert calls["timeout"] <= 20


def test_probe_auth_fail_from_401(monkeypatch):
    monkeypatch.setattr(ch.urllib.request, "urlopen",
                        lambda req, timeout=None: (_ for _ in ()).throw(_http_error(401)))
    status, _ = ch.probe_endpoint("https://x/v1", "m", "badkey")
    assert status == "AUTH_FAIL"


def test_probe_rate_limited_from_429(monkeypatch):
    monkeypatch.setattr(ch.urllib.request, "urlopen",
                        lambda req, timeout=None: (_ for _ in ()).throw(_http_error(429)))
    status, _ = ch.probe_endpoint("https://x/v1", "m", "k")
    assert status == "RATE_LIMITED"


def test_probe_server_error_from_503(monkeypatch):
    monkeypatch.setattr(ch.urllib.request, "urlopen",
                        lambda req, timeout=None: (_ for _ in ()).throw(_http_error(503)))
    status, _ = ch.probe_endpoint("https://x/v1", "m", "k")
    assert status == "SERVER_ERROR"


def test_probe_timeout_classified(monkeypatch):
    def raise_timeout(req, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr(ch.urllib.request, "urlopen", raise_timeout)
    status, _ = ch.probe_endpoint("https://x/v1", "m", "k")
    assert status == "TIMEOUT"


def test_probe_unreachable_on_urlerror(monkeypatch):
    def raise_conn(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ch.urllib.request, "urlopen", raise_conn)
    status, _ = ch.probe_endpoint("https://x/v1", "m", "k")
    assert status == "UNREACHABLE"


# ------------------------------------------------------------ ringkasan

def test_build_summary_format():
    results = {
        "NOUS/stealth/ox-alpha": {"status": "OK", "latency_ms": 812,
                                  "checked_at": "t"},
        "GROQ/openai/gpt-oss-20b": {"status": "RATE_LIMITED", "latency_ms": 90,
                                    "checked_at": "t"},
        "NVIDIA/meta/llama-3.1-8b-instruct": {"status": "NO_KEY",
                                              "latency_ms": None, "checked_at": "t"},
    }
    s = ch.build_summary(results)
    assert s == ("NOUS ox-alpha OK 812ms | "
                 "GROQ gpt-oss-20b RATE_LIMITED 90ms | "
                 "NVIDIA llama-3.1-8b-instruct NO_KEY")


def test_summary_no_latency_segment_when_none():
    r = {"NOUS/x": {"status": "NO_KEY", "latency_ms": None, "checked_at": "t"}}
    assert ch.build_summary(r) == "NOUS x NO_KEY"


# -------------------------------------------------------------- NO_KEY

def test_no_key_skips_network(no_sleep):
    cands = [{"provider": "NVIDIA", "base_url": "", "model": "-", "api_key": ""}]
    urlopen = mock.Mock(side_effect=AssertionError("jangan network utk NO_KEY"))
    with mock.patch.object(ch.urllib.request, "urlopen", urlopen):
        results, summary = ch.run_health_check(cands)
    urlopen.assert_not_called()
    assert results["NVIDIA/-"]["status"] == "NO_KEY"
    assert summary == "NVIDIA - NO_KEY"


# --------------------------------------- loop tahan hang / budget waktu

def test_timeout_does_not_drop_loop(no_sleep):
    """Provider pertama hang → loop lanjut ke kandidat berikutnya."""
    state = {"n": 0}

    def fake_urlopen(req, timeout=None):
        state["n"] += 1
        if state["n"] == 1:
            raise TimeoutError("hang")
        return _ok_resp()

    cands = [
        {"provider": "SLOW", "base_url": "https://slow/v1", "model": "m",
         "api_key": "k"},
        {"provider": "FAST", "base_url": "https://fast/v1", "model": "m",
         "api_key": "k"},
    ]
    with mock.patch.object(ch.urllib.request, "urlopen", fake_urlopen):
        results, _ = ch.run_health_check(cands)
    assert state["n"] == 2
    assert results["SLOW/m"]["status"] == "TIMEOUT"
    assert results["FAST/m"]["status"] == "OK"


def test_total_budget_marks_rest_skipped(no_sleep, monkeypatch):
    monkeypatch.setattr(ch, "TOTAL_BUDGET_S", -1)  # deadline sudah lewat
    cands = [{"provider": "P", "base_url": "https://p/v1", "model": "m",
              "api_key": "k"}]
    urlopen = mock.Mock(side_effect=AssertionError("budget habis → jangan network"))
    with mock.patch.object(ch.urllib.request, "urlopen", urlopen):
        results, _ = ch.run_health_check(cands)
    assert results["P/m"]["status"] == "SKIPPED_BUDGET"


def test_inter_provider_sleep_applied(no_sleep):
    sleeps = []
    monkey = pytest.MonkeyPatch()
    monkey.setattr(ch.time, "sleep", lambda s: sleeps.append(s))
    try:
        cands = [
            {"provider": "A", "base_url": "https://a/v1", "model": "m", "api_key": "k"},
            {"provider": "B", "base_url": "https://b/v1", "model": "m", "api_key": "k"},
        ]
        with mock.patch.object(ch.urllib.request, "urlopen",
                               lambda req, timeout=None: _ok_resp()):
            ch.run_health_check(cands)
    finally:
        monkey.undo()
    assert sleeps == [ch.INTER_PROVIDER_SLEEP_S]


# ------------------------------------------------------ exit code & save

def test_exit_code_rules():
    ok = {"a": {"status": "OK"}, "b": {"status": "RATE_LIMITED"},
          "c": {"status": "NO_KEY"}}
    assert ch.exit_code(ok) == 0
    fail = dict(ok, d={"status": "AUTH_FAIL"})
    assert ch.exit_code(fail) == 1


def test_save_results(tmp_path, monkeypatch):
    monkeypatch.setattr(ch, "REPO", tmp_path)
    path = ch.save_results({"NOUS/x": {"status": "OK", "latency_ms": 5,
                                       "checked_at": "t"}})
    data = json.loads(path.read_text())
    assert data["results"]["NOUS/x"]["status"] == "OK"
    assert path == tmp_path / "Personalisasi" / "health" / "latest.json"


def test_dedupe_candidates(monkeypatch):
    """Kandidat duplikat (url,model) didedup; provider kanonik tanpa key → NO_KEY row."""
    fake_raw = [("https://api.groq.com/openai/v1/", "openai/gpt-oss-20b", "gk"),
                ("https://api.groq.com/openai/v1", "openai/gpt-oss-20b", "gk"),
                ("https://integrate.api.nvidia.com/v1", "meta/llama-3.1-8b-instruct",
                 "nk")]
    mc = mock.Mock()
    mc._endpoint_candidates.return_value = fake_raw
    monkeypatch.setattr(ch, "ModelClient", lambda *a, **kw: mc)
    for v in ("NOUS_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(v, "")  # kosong → NO_KEY rows
    monkeypatch.delenv("NOUS_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cands = ch.build_candidates()
    keyed = [(c["base_url"], c["model"]) for c in cands if c["base_url"]]
    assert len(keyed) == len(set(keyed))     # kandidat ber-key unik
    by_prov = {}
    for c in cands:
        by_prov.setdefault(c["provider"], []).append(c)
    assert len(by_prov["GROQ"]) == 1          # dedup + trailing slash dirapikan
    assert by_prov["GROQ"][0]["provider"] == "GROQ"
    assert {c["status"] if False else c["api_key"] for c in by_prov["NVIDIA"]} == {"nk"}
    assert all(c["api_key"] == "" for c in by_prov.get("NOUS", []))
    assert all(c["api_key"] == "" for c in by_prov.get("GEMINI", []))
