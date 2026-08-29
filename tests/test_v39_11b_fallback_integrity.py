"""Test V39.12 — fallback chain hanya mengandung provider valid (dengan key).

Jika provider key tidak ada → jangan ikat kandidat (bukan error 404).
Ini buat hindari INCONCLUSIVE "semua model fallback habis" karena
provider dummy/error di chain.
"""
import inspect
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.utils.model_client import ModelClient


def test_endpoint_candidates_all_have_keys():
    """Tiap entry di _endpoint_candidates() wajib ada api_keynya."""
    mc = ModelClient()
    cands = mc._endpoint_candidates()
    assert len(cands) > 0, "harus ada minimal 1 provider valid"
    for url, model, key in cands:
        assert key, f"candidate {url}/{model} tanpa key — harusnya tidak masuk"


def test_gemini_key_optional():
    """Gemini bisa None — tapi kecuali, gak masuk chain."""
    mc = ModelClient(provider="gemini")
    # kalau gak ada key, candidates harus kosong / tidak error
    cands = mc._endpoint_candidates()
    for _, _, k in cands:
        assert k
