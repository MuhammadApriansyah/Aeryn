"""Test V39.12 — fine-tuning dataset generator v2 (CoT + Critic + Persona)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dataset_file_exists():
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    assert os.path.exists(OUTPUT_FILE), f"Dataset not found: {OUTPUT_FILE}"


def test_dataset_valid_jsonl():
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    ok = 0
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            assert "type" in obj
            assert "input" in obj
            assert "output" in obj
            assert "metadata" in obj
            assert "sample_id" in obj["metadata"]
            ok += 1
    assert ok >= 10, f"Only {ok} samples, need >= 10"


def test_cot_samples_present():
    """Ensure CoT reasoning samples exist."""
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    cot = []
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            if obj["type"] == "cot_reasoning":
                cot.append(obj)
    assert len(cot) >= 5, f"Only {len(cot)} cot samples"


def test_critic_samples_present():
    """Ensure critic pattern samples exist."""
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    critic = []
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            if obj["type"] == "critic_pattern":
                critic.append(obj)
    assert len(critic) >= 3, f"Only {len(critic)} critic samples"


def test_persona_samples_present():
    """Ensure persona integration samples exist."""
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    persona = []
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            if obj["type"] == "persona_integration":
                persona.append(obj)
    assert len(persona) >= 4, f"Only {len(persona)} persona samples"


def test_error_recovery_samples_present():
    """Ensure error recovery samples exist."""
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    recovery = []
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            if obj["type"] == "error_recovery":
                recovery.append(obj)
    assert len(recovery) >= 3, f"Only {len(recovery)} recovery samples"


def test_sample_id_is_sha256_short():
    """Sample ID must be first 12 chars of sha256."""
    import hashlib
    from scripts.archive.generate_finetune_v3912 import OUTPUT_FILE
    with open(OUTPUT_FILE) as f:
        for line in f:
            obj = json.loads(line)
            sid = obj["metadata"]["sample_id"]
            assert len(sid) == 12, f"Sample ID wrong length: {len(sid)}"
            # Must be hex
            try:
                int(sid, 16)
            except ValueError:
                assert False, f"Sample ID not hex: {sid}"