"""Test V31.3 — VerificationGate: klaim faktual vs bukti tool."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.verification_gate import annotate_answer, check_claims


def _trace(tools, digest="ok"):
    return [{"type": "tool", "name": t, "result_digest": digest}
            for t in tools]


def test_klaim_tulis_tanpa_bukti_terdeteksi():
    ans = "File config.toml sudah diubah sesuai permintaan."
    c = check_claims(ans, _trace(["fs_read"], "{'content': '...'}"))
    assert not c["covered"]
    assert any("perubahan" in u for u in c["unsupported"])


def test_klaim_tulis_dengan_bukti_terminal():
    ans = "File config.toml sudah diubah."
    c = check_claims(ans, _trace(["terminal"],
                                 "exit_code: 0, written successfully"))
    assert c["covered"]


def test_klaim_versi_dengan_fs_read():
    ans = "Versi paket adalah 0.1.0"
    c = check_claims(ans, _trace(["fs_read"],
                                 '{"content":"name = aeryn_native version = 0.1.0"}'))
    assert c["covered"]


def test_klaim_versi_tanpa_tool():
    ans = "Versi paket adalah 9.9.9"
    c = check_claims(ans, [])
    # tidak ada tool sama sekali → gate tidak menuduh (bukan konteks tool)
    # tapi kalau dipaksa konteks tool kosong dengan klaim → unsupported
    c2 = check_claims(ans, _trace(["web_search"], "berita"))
    assert not c2["covered"] or c2["claims_found"] == 0


def test_obrolan_biasa_tidak_ditandai():
    c = check_claims("Halo! Senang bisa membantu.", _trace([]))
    assert c["claims_found"] == 0 and c["covered"]


def test_annotate_menambah_caveat():
    ans = "File sudah diubah."
    check = {"claims_found": 1, "unsupported": ["klaim perubahan file"],
             "covered": False}
    out = annotate_answer(ans, check)
    assert "Verifikasi" in out and "klaim perubahan" in out
    # covered → jawaban apa adanya
    assert annotate_answer(ans, {"covered": True}) == ans
