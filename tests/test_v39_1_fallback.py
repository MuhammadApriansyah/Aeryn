"""Test V39.1 — FallbackRouter: setiap error tool DIARAHKAN, bukan ditolak
mentah. Filosofi Sen: jangan menambal tanpa ujung — arahkan."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.utils.fallback_router import get_fallback_directive


def test_error_gets_directive():
    r = {"error": "query terlalu panjang (5000 > 400)"}
    d = get_fallback_directive("web_search", r)
    assert d and "PERSINGKAT" in d


def test_secret_denial_directs_to_report_not_bypass():
    """Kunci keamanan: denial sensitif mengarahkan LAPOR, bukan bypass."""
    r = {"error": ("file sensitif '.env' dilindungi SecurityKernel")}
    d = get_fallback_directive("fs_read", r)
    assert d and "JANGAN coba baca lewat cara lain" in d
    assert "Laporkan" in d or "restricted" in d


def test_no_such_file_directs_confirm():
    r = {"error": "[Errno 2] No such file or directory: 'x.txt'"}
    d = get_fallback_directive("fs_read", r)
    assert d and "konfirmasi" in d.lower()


def test_daily_cap_directs_degrade():
    r = {"ok": False, "error": "daily cap"}
    d = get_fallback_directive("ask_hermes", r)
    assert d and ("Kerjakan langsung" in d or "menunggu" in d)


def test_unknown_tool_gets_default():
    d = get_fallback_directive("tool_misterius", {"error": "boom"})
    assert d and DEFAULT_IN(d)


def DEFAULT_IN(s):
    return "JANGAN ulangi percobaan identik" in s


def test_success_result_untouched():
    assert get_fallback_directive("web_search", {"results": [1]}) is None
    assert get_fallback_directive("web_search", {}) is None


def test_every_registered_tool_has_map_or_default():
    """Semua tool di daemon harus jatuh di peta ATAU default directive —
    tidak ada error yang 'menggantung' tanpa arahan."""
    from aeryn_core.utils.fallback_router import FALLBACK_MAP, DEFAULT_DIRECTIVE
    for tool in ("web_search", "web_read", "http_get", "fs_read",
                 "fs_write", "terminal", "ask_hermes", "spawn_subagents",
                 "memory_search", "core_memory_edit"):
        r = {"error": "kesalahan apa pun"}
        d = get_fallback_directive(tool, r)
        assert d, f"{tool} tidak punya directive"
        assert "JANGAN" in d or "Fallback" in d or "ARAHAN" in d
