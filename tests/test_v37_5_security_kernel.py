"""Test V37.5 — SecurityKernel: defense in depth.

Setiap test = vektor serangan nyata yang ditemukan audit berlapis.
Fail-closed: ragu → tolak.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.security_kernel import check_path, make_secure_terminal
from aeryn_core.tool_bridge import build_default_registry

SB = ["~/aeryn-core-agent"]


def test_secret_inside_sandbox_protected():
    """File sensitif DI DALAM sandbox pun harus ditolak."""
    ok, why = check_path("~/aeryn-core-agent/.env", "read", SB)
    assert not ok and "sensitif" in why


def test_memory_files_protected():
    for p in ("Personalisasi/Database/social.json",
              "Personalisasi/Database/core_memory.json",
              "Personalisasi/Database/parity_ledger.json"):
        ok, why = check_path(f"~/{'aeryn-core-agent/' if 'aeryn' in p else ''}{p}",
                             "read", SB)
        assert not ok, p


def test_source_write_protected():
    ok, why = check_path("~/aeryn-core-agent/aeryn_core/daemon.py",
                         "write", SB)
    assert not ok and "protected" in why
    # read ke source tetap boleh (transparansi)
    ok2, _ = check_path("~/aeryn-core-agent/aeryn_core/daemon.py",
                        "read", SB)
    assert ok2


def test_normal_file_still_allowed():
    ok, _ = check_path("~/aeryn-core-agent/catatan/harian.md",
                       "write", SB)
    assert ok
    ok2, _ = check_path("halo.txt", "write", SB)  # relative sederhana
    assert ok2


def test_traversal_blocked():
    ok, _ = check_path("~/aeryn-core-agent/../../.hermes/.env", "read", SB)
    assert not ok


def test_terminal_flag_with_path_value_blocked():
    """Bypass V37.4: flag dengan nilai path (--output=/x)."""
    term = make_secure_terminal(SB)
    r = term("git log --output=/tmp/evil.txt --oneline")
    assert "SecurityKernel" in str(r.get("error", "")), r


def test_terminal_short_flag_attached_path_blocked():
    term = make_secure_terminal(SB)
    r = term("find . -fprint/etc/pwned")
    assert "error" in r


def test_terminal_cat_env_in_sandbox_blocked():
    """.env ada DI DALAM sandbox → kernel harus menolak."""
    term = make_secure_terminal(SB)
    r = term("cat .env")
    assert "SecurityKernel" in str(r.get("error", "")), r


def test_http_ssrf_internal_blocked():
    reg = build_default_registry(sandbox_roots=["/tmp"])
    for url in ("http://127.0.0.1:3010/metrics", "http://localhost/x",
                "http://192.168.1.1/", "http://10.0.0.5/admin"):
        r = reg.execute("http_get", {"url": url})
        assert "error" in r, url
    # eksternal tetap lolos validasi scheme (tidak dieksekusi di test)


def test_external_url_passes_scheme_check():
    reg = build_default_registry(sandbox_roots=["/tmp"])
    r = reg.execute("http_get", {"url": "https://example.com/"})
    assert "error" not in r or "diizinkan" not in str(r.get("error"))
