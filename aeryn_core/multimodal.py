"""V40 — Multimodal input processing (image, audio, video, PDF).

Provides unified ingestion for non-text modalities:
- Image: OCR (tesseract), captioning placeholder, metadata extraction
- Audio: transcription placeholder, duration/format detection
- Video: frame extraction placeholder, duration/format detection
- PDF: text extraction (pymupdf), page count, metadata

All processors return a standard MultimodalResult with:
  - ok: bool
  - modality: str ("image" | "audio" | "video" | "pdf")
  - text: extracted/derived text (transcription, OCR, caption, PDF text)
  - metadata: dict (dimensions, duration, pages, format, size_bytes)
  - error: str (when ok is False)

Security:
- Path access gated by safety_engine.check_path
- File size caps per modality
- Sensitive-file basenames blocked
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from aeryn_core.safety_engine import check_path

# ── Constants ─────────────────────────────────────────────────────

MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_AUDIO_BYTES = 50 * 1024 * 1024   # 50 MB
MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_PDF_BYTES = 25 * 1024 * 1024     # 25 MB

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
PDF_EXTS = {".pdf"}

SANDBOX_ROOTS = ["~/aeryn-core-agent", "~/Downloads", "~/webnovel-platform"]


# ── Result type ───────────────────────────────────────────────────

@dataclass
class MultimodalResult:
    ok: bool
    modality: str
    text: str = ""
    metadata: dict = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "modality": self.modality,
            "text": self.text,
            "metadata": self.metadata,
            "error": self.error,
        }

    def __bool__(self) -> bool:
        return self.ok


# ── Helpers ───────────────────────────────────────────────────────

def _safe_read(path: str, max_bytes: int) -> tuple:
    """Validate path + size, return (bytes, error_msg)."""
    ok, reason = check_path(path, "read", SANDBOX_ROOTS)
    if not ok:
        return b"", reason
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return b"", f"file tidak ditemukan: {path}"
    size = os.path.getsize(expanded)
    if size > max_bytes:
        return b"", f"file terlalu besar ({size // 1024 // 1024}MB, max {max_bytes // 1024 // 1024}MB)"
    with open(expanded, "rb") as f:
        return f.read(), ""


def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _run_cmd(cmd: list, timeout: int = 30) -> tuple:
    """Run subprocess, return (stdout_str, stderr_str, returncode)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except FileNotFoundError:
        return "", f"command not found: {cmd[0]}", -1
    except subprocess.TimeoutExpired:
        return "", "timeout", -2


# ── Image processing ──────────────────────────────────────────────

def _image_metadata(data: bytes, path: str) -> dict:
    """Extract basic image metadata without external deps."""
    meta = {"size_bytes": len(data), "format": _ext(path).lstrip(".")}
    # Try PIL if available
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        meta["width"], meta["height"] = img.size
        meta["mode"] = img.mode
        meta["format"] = img.format or meta["format"]
    except ImportError:
        pass
    except Exception:
        pass
    return meta


def _ocr_image(data: bytes, path: str) -> str:
    """OCR via tesseract CLI. Returns empty string if unavailable."""
    # Write to temp file for tesseract
    ext = _ext(path) or ".png"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        stdout, stderr, rc = _run_cmd(
            ["tesseract", tmp_path, "stdout", "--psm", "3"], timeout=60
        )
        if rc == 0:
            return stdout.strip()
        return ""
    finally:
        os.unlink(tmp_path)


def _caption_image(data: bytes, path: str) -> str:
    """Image captioning placeholder — calls vision model if API key present.

    Replace this function with a real implementation (e.g. LLaVA, BLIP-2,
    or a cloud vision API) when a captioning backend is configured.
    """
    # Placeholder: return empty; real implementation would call a model
    return ""


def process_image(path: str, question: str = "Jelaskan gambar ini.") -> MultimodalResult:
    """Process an image file: OCR + metadata + optional caption.

    Args:
        path: Local file path within sandbox.
        question: Question for vision model (used by caption placeholder).
    """
    data, err = _safe_read(path, MAX_IMAGE_BYTES)
    if err:
        return MultimodalResult(ok=False, modality="image", error=err)

    if _ext(path) not in IMAGE_EXTS:
        return MultimodalResult(
            ok=False, modality="image",
            error=f"format tidak didukung: {_ext(path)}"
        )

    meta = _image_metadata(data, path)
    text_parts = []

    # OCR
    ocr_text = _ocr_image(data, path)
    if ocr_text:
        text_parts.append(f"[OCR]\n{ocr_text}")

    # Caption placeholder
    caption = _caption_image(data, path)
    if caption:
        text_parts.append(f"[Caption]\n{caption}")

    text = "\n\n".join(text_parts)
    if not text:
        text = "[Image processed — no extractable text]"

    return MultimodalResult(ok=True, modality="image", text=text, metadata=meta)


# ── Audio processing ──────────────────────────────────────────────

def _audio_metadata(path: str) -> dict:
    """Extract audio metadata via ffprobe if available."""
    meta = {"size_bytes": os.path.getsize(os.path.expanduser(path)), "format": _ext(path).lstrip(".")}
    stdout, _, rc = _run_cmd([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", os.path.expanduser(path)
    ], timeout=15)
    if rc == 0 and stdout:
        try:
            info = json.loads(stdout)
            fmt = info.get("format", {})
            meta["duration_seconds"] = float(fmt.get("duration", 0))
            meta["bitrate"] = int(fmt.get("bit_rate", 0))
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "audio":
                    meta["codec"] = stream.get("codec_name", "")
                    meta["sample_rate"] = int(stream.get("sample_rate", 0))
                    meta["channels"] = int(stream.get("channels", 0))
                    break
        except (json.JSONDecodeError, ValueError):
            pass
    return meta


def _transcribe_audio(path: str) -> str:
    """Audio transcription placeholder.

    Replace with Whisper CLI, cloud STT API, or local model as needed.
    """
    return ""


def process_audio(path: str) -> MultimodalResult:
    """Process an audio file: metadata + transcription placeholder."""
    data, err = _safe_read(path, MAX_AUDIO_BYTES)
    if err:
        return MultimodalResult(ok=False, modality="audio", error=err)

    if _ext(path) not in AUDIO_EXTS:
        return MultimodalResult(
            ok=False, modality="audio",
            error=f"format tidak didukung: {_ext(path)}"
        )

    meta = _audio_metadata(path)
    text = _transcribe_audio(path)
    if not text:
        text = "[Audio processed — transcription not available]"

    return MultimodalResult(ok=True, modality="audio", text=text, metadata=meta)


# ── Video processing ──────────────────────────────────────────────

def _video_metadata(path: str) -> dict:
    """Extract video metadata via ffprobe if available."""
    meta = {"size_bytes": os.path.getsize(os.path.expanduser(path)), "format": _ext(path).lstrip(".")}
    stdout, _, rc = _run_cmd([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", os.path.expanduser(path)
    ], timeout=15)
    if rc == 0 and stdout:
        try:
            info = json.loads(stdout)
            fmt = info.get("format", {})
            meta["duration_seconds"] = float(fmt.get("duration", 0))
            meta["bitrate"] = int(fmt.get("bit_rate", 0))
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    meta["width"] = int(stream.get("width", 0))
                    meta["height"] = int(stream.get("height", 0))
                    meta["codec"] = stream.get("codec_name", "")
                    break
        except (json.JSONDecodeError, ValueError):
            pass
    return meta


def _extract_video_frames(path: str, num_frames: int = 3) -> list:
    """Extract keyframe images from video. Returns list of file paths."""
    expanded = os.path.expanduser(path)
    frames = []
    with tempfile.TemporaryDirectory() as td:
        stdout, stderr, rc = _run_cmd([
            "ffmpeg", "-i", expanded, "-vf",
            f"select='eq(pict_type\\,I)',scale=320:-1",
            "-vsync", "vfr", "-frames:v", str(num_frames),
            os.path.join(td, "frame_%03d.png")
        ], timeout=60)
        if rc == 0:
            frames = sorted([
                os.path.join(td, f)
                for f in os.listdir(td) if f.startswith("frame_")
            ])
    return frames


def process_video(path: str, extract_frames: bool = False) -> MultimodalResult:
    """Process a video file: metadata + optional frame extraction.

    Args:
        path: Local file path within sandbox.
        extract_frames: If True, extract keyframes for later image processing.
    """
    data, err = _safe_read(path, MAX_VIDEO_BYTES)
    if err:
        return MultimodalResult(ok=False, modality="video", error=err)

    if _ext(path) not in VIDEO_EXTS:
        return MultimodalResult(
            ok=False, modality="video",
            error=f"format tidak didukung: {_ext(path)}"
        )

    meta = _video_metadata(path)
    text_parts = []

    if extract_frames:
        frames = _extract_video_frames(path)
        if frames:
            meta["extracted_frames"] = len(frames)
            text_parts.append(f"[Extracted {len(frames)} keyframes]")

    text = "\n".join(text_parts) if text_parts else "[Video processed — metadata only]"
    return MultimodalResult(ok=True, modality="video", text=text, metadata=meta)


# ── PDF processing ────────────────────────────────────────────────

def _pdf_metadata(path: str) -> dict:
    """Extract PDF metadata via pymupdf or pdfinfo."""
    meta = {"size_bytes": os.path.getsize(os.path.expanduser(path)), "format": "pdf"}
    # Try pymupdf first
    try:
        import fitz
        doc = fitz.open(os.path.expanduser(path))
        meta["page_count"] = len(doc)
        info = doc.metadata or {}
        meta["title"] = info.get("title", "")
        meta["author"] = info.get("author", "")
        meta["subject"] = info.get("subject", "")
        doc.close()
        return meta
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: pdfinfo
    stdout, _, rc = _run_cmd(["pdfinfo", os.path.expanduser(path)], timeout=15)
    if rc == 0:
        for line in stdout.splitlines():
            if line.startswith("Pages:"):
                try:
                    meta["page_count"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Title:"):
                meta["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("Author:"):
                meta["author"] = line.split(":", 1)[1].strip()
    return meta


def _pdf_extract_text(path: str, max_pages: int = 50) -> str:
    """Extract text from PDF via pymupdf."""
    try:
        import fitz
        doc = fitz.open(os.path.expanduser(path))
        parts = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                parts.append(f"\n... (truncated at {max_pages} pages)")
                break
            parts.append(page.get_text())
        doc.close()
        return "\n".join(parts).strip()
    except ImportError:
        return ""
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def process_pdf(path: str, max_pages: int = 50) -> MultimodalResult:
    """Process a PDF file: text extraction + metadata.

    Args:
        path: Local file path within sandbox.
        max_pages: Maximum pages to extract text from.
    """
    data, err = _safe_read(path, MAX_PDF_BYTES)
    if err:
        return MultimodalResult(ok=False, modality="pdf", error=err)

    if _ext(path) not in PDF_EXTS:
        return MultimodalResult(
            ok=False, modality="pdf",
            error=f"format tidak didukung: {_ext(path)}"
        )

    meta = _pdf_metadata(path)
    text = _pdf_extract_text(path, max_pages)
    if not text:
        text = "[PDF processed — no extractable text (scanned PDF?)]"

    return MultimodalResult(ok=True, modality="pdf", text=text, metadata=meta)


# ── Unified dispatcher ────────────────────────────────────────────

def process_file(path: str, **kwargs) -> MultimodalResult:
    """Auto-detect modality from extension and dispatch to the right processor.

    Args:
        path: Local file path within sandbox.
        **kwargs: Passed through to the specific processor.
    """
    ext = _ext(path)
    if ext in IMAGE_EXTS:
        return process_image(path, **kwargs)
    elif ext in AUDIO_EXTS:
        return process_audio(path, **kwargs)
    elif ext in VIDEO_EXTS:
        return process_video(path, **kwargs)
    elif ext in PDF_EXTS:
        return process_pdf(path, **kwargs)
    else:
        return MultimodalResult(
            ok=False, modality="unknown",
            error=f"format tidak dikenali: {ext}"
        )


# ── Tool schemas (for agent tool registration) ────────────────────

MULTIMODAL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "process_image",
            "description": "Proses file gambar: OCR, ekstraksi metadata, dan caption.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file gambar dalam sandbox"},
                    "question": {"type": "string", "description": "Pertanyaan tentang gambar (untuk caption)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_audio",
            "description": "Proses file audio: metadata + transkripsi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file audio dalam sandbox"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_video",
            "description": "Proses file video: metadata + ekstraksi frame opsional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file video dalam sandbox"},
                    "extract_frames": {"type": "boolean", "description": "Ekstrak keyframe jika true"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_pdf",
            "description": "Proses file PDF: ekstraksi teks + metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file PDF dalam sandbox"},
                    "max_pages": {"type": "integer", "description": "Maksimal halaman diekstrak (default 50)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_file",
            "description": "Deteksi modality otomatis dari ekstensi dan proses file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file dalam sandbox"},
                },
                "required": ["path"],
            },
        },
    },
]