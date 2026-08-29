"""V30.3 — DynamicSchema: tool schema diparameterisasi per goal.

Masalah: schema statis menggoda model menebak argumen (mis. path yang tak
ada). Solusi: sebelum run, analisis goal → tambahkan hint konkret ke
schema description (path yang disebut user, URL, query keyword), dan
susulkan tool yang jelas tidak relevan — mengurangi noise & halusinasi.

Murni transformasi dict schema; tidak mengubah registry global.
"""
import re
from copy import deepcopy

# token goal → tool relevan
TOOL_HINTS = {
    "fs_read": ("file", "baca", "readme", ".json", ".toml", ".md",
                ".py", ".txt", "config", "cargo.toml", "package.json"),
    "http_get": ("http", "url", "fetch", "endpoint", "api"),
    "web_search": ("cari", "search", "berita", "harga", "tutorial", "siapa",
                   "apa itu"),
    "terminal": ("ls", "list direktori", "proses", "ps", "df"),
}


def _goal_paths(goal: str) -> list:
    """Path file / URL / filename ber-ekstensi yang disebut di goal."""
    abs_paths = re.findall(r"(/[\w./-]{2,}|https?://[\w./-]+)", goal)
    filenames = re.findall(r"\b[\w-]+\.(?:toml|json|md|py|txt|yaml|yml)\b",
                           goal, re.I)
    # unik, jaga urutan
    seen, out = set(), []
    for p in abs_paths + filenames:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def relevant_tools(goal: str) -> set:
    low = goal.lower()
    rel = {t for t, kws in TOOL_HINTS.items()
           if any(k in low for k in kws)}
    # default: kalau tak ada hint kuat, biarkan semua (jangan terlalu agresif)
    return rel or set()


def build_dynamic_schemas(base_schemas: list, goal: str) -> list:
    """Kembalikan salinan schema dengan description diperkaya hint konteks.

    - Path/URL dari goal ditulis eksplisit di description (model tak perlu
      menebak).
    - Tool tak-relevan tetap disertakan TAPI diberi suffix "(mungkin tidak
      relevan untuk goal ini)" bila ada tool lain yang lebih cocok.
    """
    paths = _goal_paths(goal)
    rel = relevant_tools(goal)
    out = []
    for s in base_schemas:
        s = deepcopy(s)
        name = s.get("function", {}).get("name") or s.get("name")
        desc_key = "description"
        container = s
        if "function" in s:                      # format OpenAI tools
            container = s["function"]
        desc = container.get(desc_key, "")
        extras = []
        if name == "fs_read" and paths:
            local = [p for p in paths if not p.startswith("http")]
            if local:
                extras.append(f"path kandidat dari goal: {', '.join(local[:3])}")
        if name == "http_get" and paths:
            urls = [p for p in paths if p.startswith("http")]
            if urls:
                extras.append(f"url kandidat: {urls[0]}")
        if rel and name not in rel:
            better = ", ".join(sorted(rel))
            extras.append(f"(kemungkinan tidak relevan; pertimbangkan: {better})")
        if extras:
            container[desc_key] = f"{desc} [{'; '.join(extras)}]"
        out.append(s)
    return out


def schema_stats(schemas: list) -> dict:
    """Introspeksi kecil buat test/debug."""
    return {"count": len(schemas),
            "enriched": sum(1 for s in schemas
                            if "[" in ((s.get("function") or s).get(
                                "description", "")))}
