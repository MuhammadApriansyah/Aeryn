"""V39.6b — Research-first ENFORCEMENT di kode (bukan cuma prompt).

Filosofi enforcement-di-kode (V34 lesson): prompt bisa diabaikan model
kecil; guard kode tidak. Kalau needs_research(goal) == True dan run
selesai TANPA tool riset (web_search/web_read) → jawaban ditandai
"ungrounded" dan verifier menurunkan kepercayaan: tambahkan disclaimer
sumber ATAU paksa satu iterasi riset.

Implementasi: di agent loop, setelah jawaban final terbentuk, cek
research-needed vs tools-terpakai. Bila butuh tapi tak pernah riset →
suntikkan SATU iterasi ekstra dengan directive riset eksplisit.
"""
import re

from aeryn_core.reasoning.reasoning_style import needs_research

RESEARCH_TOOLS = {"web_search", "web_read", "ask_hermes", "memory_search"}

FORCED_RESEARCH_DIRECTIVE = (
    "[SISTEM] Goal ini meminta informasi faktual, tapi kamu menjawab "
    "TANPA melakukan riset. DILARANG mengirim jawaban yang tidak "
    "ter-grounding. Lakukan SEKARANG: web_search deng frasa kunci dari "
    "goal, baca 1 sumber terbaik via web_read, lalu susun jawaban dan "
    "sebutkan sumbernya.")


def used_research_tools(trace: list) -> bool:
    for t in trace or []:
        if t.get("type") == "tool" and t.get("name") in RESEARCH_TOOLS:
            return True
    return False


def is_ungrounded_factual(goal: str, trace: list) -> bool:
    """True = goal fakta + tidak ada tool riset sama sekali."""
    if not needs_research(goal):
        return False
    return not used_research_tools(trace)


UNGROUNDED_DISCLAIMER = (
    "\n\n⚠️ *Catatan: ini dari pengetahuan umumku, belum kucek sumber "
    "terkini. Mau kuriset dulu biar akurat?*")
