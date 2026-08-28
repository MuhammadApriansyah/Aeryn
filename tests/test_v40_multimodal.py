"""Test V40 — Multimodal input processing (image, audio, video, PDF)."""

import os
import sys
import tempfile
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.multimodal import (
    MultimodalResult,
    process_image,
    process_audio,
    process_video,
    process_pdf,
    process_file,
    _ext,
    _safe_read,
    _run_cmd,
    MAX_IMAGE_BYTES,
    MAX_AUDIO_BYTES,
    MAX_VIDEO_BYTES,
    MAX_PDF_BYTES,
    IMAGE_EXTS,
    AUDIO_EXTS,
    VIDEO_EXTS,
    PDF_EXTS,
    MULTIMODAL_SCHEMAS,
)


# ── Helpers ───────────────────────────────────────────────────────

def _make_minimal_png(width=4, height=4):
    """Create a minimal valid PNG file."""
    import zlib
    import struct

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    for y in range(height):
        raw += b"\x00"  # filter byte
        for x in range(width):
            raw += b"\xff\x00\x00"  # red pixel
    idat = zlib.compress(raw)
    iend = b""

    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", iend)


def _make_minimal_pdf(pages=2):
    """Create a minimal valid PDF with N pages."""
    content = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << >> >>
endobj

4 0 obj
<< /Length 44 >>
stream
BT
/F1 24 Tf
100 700 Td
(Hello Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 

trailer
<< /Size 5 /Root 1 0 R >>
startxref
363
%%EOF
"""
    return content.encode("latin-1")


def _make_minimal_wav():
    """Create a minimal valid WAV file."""
    data = b"RIFF"
    data += struct.pack("<I", 36)  # file size - 8
    data += b"WAVE"
    data += b"fmt "
    data += struct.pack("<I", 16)  # chunk size
    data += struct.pack("<HHIIHH", 1, 1, 8000, 8000, 1, 8)  # PCM mono 8kHz 8-bit
    data += b"data"
    data += struct.pack("<I", 0)  # no samples
    return data


# ── MultimodalResult ─────────────────────────────────────────────

def test_result_to_dict():
    r = MultimodalResult(ok=True, modality="image", text="hello", metadata={"w": 100})
    d = r.to_dict()
    assert d["ok"] is True
    assert d["modality"] == "image"
    assert d["text"] == "hello"
    assert d["metadata"]["w"] == 100
    assert d["error"] == ""


def test_result_bool_true():
    r = MultimodalResult(ok=True, modality="pdf")
    assert bool(r) is True


def test_result_bool_false():
    r = MultimodalResult(ok=False, modality="pdf", error="fail")
    assert bool(r) is False


# ── _ext ─────────────────────────────────────────────────────────

def test_ext_png():
    assert _ext("photo.png") == ".png"


def test_ext_uppercase():
    assert _ext("DOC.PDF") == ".pdf"


def test_ext_no_ext():
    assert _ext("noext") == ""


# ── _safe_read ───────────────────────────────────────────────────

def test_safe_read_missing_file():
    data, err = _safe_read("/tmp/nonexistent_file_xyz_123.png", MAX_IMAGE_BYTES)
    assert data == b""
    assert "tidak ditemukan" in err


def test_safe_read_oversized(tmp_path):
    # Create a file larger than MAX_IMAGE_BYTES
    big = tmp_path / "big.png"
    big.write_bytes(b"\x00" * (MAX_IMAGE_BYTES + 1))
    data, err = _safe_read(str(big), MAX_IMAGE_BYTES)
    assert data == b""
    assert "terlalu besar" in err


def test_safe_read_blocks_traversal():
    data, err = _safe_read("/etc/passwd", MAX_IMAGE_BYTES)
    assert data == b""
    assert "traversal" in err or "sistem" in err


def test_safe_read_blocks_protected_dir():
    data, err = _safe_read("/home/sen/.hermes/auth.json", MAX_IMAGE_BYTES)
    assert data == b""
    # Should be blocked by protected dir or sensitive file
    assert err != ""


# ── _run_cmd ─────────────────────────────────────────────────────

def test_run_cmd_success():
    out, err, rc = _run_cmd(["echo", "hello"])
    assert rc == 0
    assert "hello" in out


def test_run_cmd_not_found():
    out, err, rc = _run_cmd(["nonexistent_command_xyz_abc"])
    assert rc == -1
    assert "not found" in err


# ── process_image ────────────────────────────────────────────────

def test_process_image_valid_png(tmp_path):
    png = tmp_path / "test.png"
    png.write_bytes(_make_minimal_png())
    r = process_image(str(png))
    assert r.ok is True
    assert r.modality == "image"
    assert r.metadata["format"] == "png"
    assert r.metadata["size_bytes"] > 0


def test_process_image_rejects_bad_ext(tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("not an image")
    r = process_image(str(txt))
    assert r.ok is False
    assert "tidak didukung" in r.error


def test_process_image_missing_file():
    r = process_image("/tmp/nonexistent_xyz.png")
    assert r.ok is False
    assert "tidak ditemukan" in r.error


def test_process_image_oversized(tmp_path):
    big = tmp_path / "big.png"
    big.write_bytes(b"\x00" * (MAX_IMAGE_BYTES + 1))
    r = process_image(str(big))
    assert r.ok is False
    assert "terlalu besar" in r.error


def test_process_image_metadata(tmp_path):
    png = tmp_path / "meta.png"
    png.write_bytes(_make_minimal_png(8, 6))
    r = process_image(str(png))
    assert r.ok is True
    # PIL may or may not be available; if present, check dimensions
    if "width" in r.metadata:
        assert r.metadata["width"] == 8
        assert r.metadata["height"] == 6


# ── process_audio ────────────────────────────────────────────────

def test_process_audio_valid_wav(tmp_path):
    wav = tmp_path / "test.wav"
    wav.write_bytes(_make_minimal_wav())
    r = process_audio(str(wav))
    assert r.ok is True
    assert r.modality == "audio"
    assert r.metadata["format"] == "wav"


def test_process_audio_rejects_bad_ext(tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("not audio")
    r = process_audio(str(txt))
    assert r.ok is False
    assert "tidak didukung" in r.error


def test_process_audio_missing_file():
    r = process_audio("/tmp/nonexistent_xyz.mp3")
    assert r.ok is False


# ── process_video ────────────────────────────────────────────────

def test_process_video_rejects_bad_ext(tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("not video")
    r = process_video(str(txt))
    assert r.ok is False
    assert "tidak didukung" in r.error


def test_process_video_missing_file():
    r = process_video("/tmp/nonexistent_xyz.mp4")
    assert r.ok is False


# ── process_pdf ──────────────────────────────────────────────────

def test_process_pdf_valid(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(_make_minimal_pdf())
    r = process_pdf(str(pdf))
    assert r.ok is True
    assert r.modality == "pdf"
    assert r.metadata["format"] == "pdf"
    assert r.metadata["size_bytes"] > 0


def test_process_pdf_rejects_bad_ext(tmp_path):
    txt = tmp_path / "test.txt"
    txt.write_text("not a pdf")
    r = process_pdf(str(txt))
    assert r.ok is False
    assert "tidak didukung" in r.error


def test_process_pdf_missing_file():
    r = process_pdf("/tmp/nonexistent_xyz.pdf")
    assert r.ok is False


def test_process_pdf_with_max_pages(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(_make_minimal_pdf())
    r = process_pdf(str(pdf), max_pages=1)
    assert r.ok is True


# ── process_file (dispatcher) ────────────────────────────────────

def test_dispatch_png(tmp_path):
    png = tmp_path / "dispatch.png"
    png.write_bytes(_make_minimal_png())
    r = process_file(str(png))
    assert r.ok is True
    assert r.modality == "image"


def test_dispatch_pdf(tmp_path):
    pdf = tmp_path / "dispatch.pdf"
    pdf.write_bytes(_make_minimal_pdf())
    r = process_file(str(pdf))
    assert r.ok is True
    assert r.modality == "pdf"


def test_dispatch_wav(tmp_path):
    wav = tmp_path / "dispatch.wav"
    wav.write_bytes(_make_minimal_wav())
    r = process_file(str(wav))
    assert r.ok is True
    assert r.modality == "audio"


def test_dispatch_unknown_ext(tmp_path):
    xyz = tmp_path / "file.xyz"
    xyz.write_text("unknown")
    r = process_file(str(xyz))
    assert r.ok is False
    assert "tidak dikenali" in r.error


# ── Schemas ──────────────────────────────────────────────────────

def test_schemas_count():
    assert len(MULTIMODAL_SCHEMAS) == 5


def test_schemas_have_required_fields():
    for schema in MULTIMODAL_SCHEMAS:
        assert schema["type"] == "function"
        func = schema["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"
        assert "properties" in func["parameters"]


def test_schemas_names():
    names = {s["function"]["name"] for s in MULTIMODAL_SCHEMAS}
    assert names == {"process_image", "process_audio", "process_video", "process_pdf", "process_file"}


# ── Extension sets ───────────────────────────────────────────────

def test_image_exts():
    assert ".png" in IMAGE_EXTS
    assert ".jpg" in IMAGE_EXTS
    assert ".webp" in IMAGE_EXTS


def test_audio_exts():
    assert ".mp3" in AUDIO_EXTS
    assert ".wav" in AUDIO_EXTS


def test_video_exts():
    assert ".mp4" in VIDEO_EXTS
    assert ".mkv" in VIDEO_EXTS


def test_pdf_exts():
    assert ".pdf" in PDF_EXTS


# ── Size limits ──────────────────────────────────────────────────

def test_size_limits_positive():
    assert MAX_IMAGE_BYTES > 0
    assert MAX_AUDIO_BYTES > 0
    assert MAX_VIDEO_BYTES > 0
    assert MAX_PDF_BYTES > 0


def test_size_limits_order():
    # Audio > image, video > audio
    assert MAX_AUDIO_BYTES >= MAX_IMAGE_BYTES
    assert MAX_VIDEO_BYTES >= MAX_AUDIO_BYTES


# ── Integration: result round-trip ───────────────────────────────

def test_result_round_trip(tmp_path):
    png = tmp_path / "round.png"
    png.write_bytes(_make_minimal_png())
    r = process_image(str(png))
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["ok"] is True
    assert d["modality"] == "image"
    assert isinstance(d["metadata"], dict)
    assert isinstance(d["text"], str)