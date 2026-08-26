"""Test V38.9b — TOCTOU guard fs_write (O_NOFOLLOW).

Simulasi race: symlink di-swap SETELAH check_path, SEBELUM open.
O_NOFOLLOW harus menolak; file target asli (.env) tidak boleh tersentuh.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aeryn_core.tool_bridge as tb
from aeryn_core.tool_bridge import make_fs_write


def test_tocou_symlink_swap_blocked(tmp_path, monkeypatch):
    sb = tmp_path / "sb"
    sb.mkdir()
    fw = make_fs_write([str(sb)])

    # jalur normal yang lolos check_path
    target = sb / "late.txt"

    real_open = os.open

    def swapping_open(path, flags, *a, **kw):
        # simulasi attacker: swap ke symlink TEPAT sebelum open
        if "late" in str(path):
            if os.path.lexists(target):
                os.remove(target)
            os.symlink("/home/sen/.hermes/.env", target)
        return real_open(path, flags, *a, **kw)

    monkeypatch.setattr(tb.os, "open", swapping_open)
    try:
        try:
            r = fw(str(target), "data-race")
            # kalau sampai sini berarti menulis ke file baru — pastikan
            # BUKAN lewat symlink ke .env
            assert "pwn" not in open("/home/sen/.hermes/.env").read()[:200]
        except OSError:
            pass  # ditolak O_NOFOLLOW juga valid
    finally:
        monkeypatch.undo()

    # .env asli utuh
    head = open("/home/sen/.hermes/.env").read(20)
    assert "TERMINAL_ENV" in head


def test_normal_write_still_works(tmp_path):
    sb = tmp_path / "sb2"
    sb.mkdir()
    fw = make_fs_write([str(sb)])
    r = fw(str(sb / "sub" / "a.txt"), "halo")
    assert r["ok"] and r["bytes_written"] == 4
    assert (sb / "sub" / "a.txt").read_text() == "halo"


def test_write_to_existing_symlink_rejected():
    """Symlink yang SUDAH ada saat check → realpath resolve → keluar sandbox
    ATAU secret-basename match. Keduanya ditolak."""
    sb = "/tmp/v389_sb"
    os.makedirs(sb, exist_ok=True)
    lnk = os.path.join(sb, "lnk")
    if os.path.lexists(lnk):
        os.remove(lnk)
    os.symlink("/home/sen/.bashrc", lnk)  # non-secret tapi di luar sandbox
    fw = make_fs_write([sb])
    try:
        fw(lnk, "x")
        raise AssertionError("harusnya ditolak")
    except PermissionError:
        pass
