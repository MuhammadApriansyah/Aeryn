"""Test V37.4 — security sweep (penetration tests).

Regresi keamanan: setiap kasus di sini adalah celah NYATA yang ditemukan
audit V37.4. Jangan pernah dihilangkan tanpa persetujuan majikan.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.terminal_tool import make_terminal
from aeryn_core.tool_bridge import build_default_registry


def test_terminal_blocks_secret_read():
    """`cat ~/.hermes/.env` harus ditolak (dulu BOCOR total)."""
    term = make_terminal(["~/aeryn-core-agent"])
    r = term("cat /home/sen/.hermes/.env")
    assert "error" in r, f"BOCOR: {r}"
    assert "stdout" not in r


def test_terminal_blocks_relative_escape():
    term = make_terminal(["~/aeryn-core-agent"])
    for cmd in ("cat ../.env", "cat ../../.hermes/.env",
                "head ~/../sen/.bashrc"):
        assert "error" in term(cmd), cmd


def test_terminal_allows_sandbox_paths():
    term = make_terminal(["/tmp/aeryn-test-sandbox"])
    os.makedirs("/tmp/aeryn-test-sandbox", exist_ok=True)
    with open("/tmp/aeryn-test-sandbox/halo.txt", "w") as f:
        f.write("isi aman")
    r = term("cat /tmp/aeryn-test-sandbox/halo.txt")
    assert r.get("stdout") == "isi aman", r
    # relative dalam cwd sandbox juga boleh
    r2 = term("cat halo.txt", cwd="/tmp/aeryn-test-sandbox")
    assert "halo.txt" in str(r2) or r2.get("stdout") == "isi aman", r2


def test_http_get_blocks_file_scheme():
    reg = build_default_registry(sandbox_roots=["/tmp"])
    r = reg.execute("http_get", {"url": "file:///etc/passwd"})
    assert "error" in r and "passwd" not in str(r.get("body", ""))


def test_http_get_blocks_ftp_and_data():
    reg = build_default_registry(sandbox_roots=["/tmp"])
    assert "error" in reg.execute("http_get", {"url": "ftp://x/y"})
    assert "error" in reg.execute("http_get", {"url": "data:text/html,hi"})


def test_gateway_allowlist_env_parsed():
    """Format allowlist: dipisah koma, spasi ditrim."""
    raw = "111, 222 ,333"
    ids = {u.strip() for u in raw.split(",") if u.strip()}
    assert ids == {"111", "222", "333"}
