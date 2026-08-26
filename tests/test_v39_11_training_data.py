"""Test V39.11 — training data generator produces valid samples."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dataset_file_created():
    sys.path.insert(0, sys.path[0] + "/scripts")
    import generate_training_data as gen
    gen.main()
    assert os.path.exists(gen.TRAINING_FILE)


def test_dataset_jsonl_valid():
    sys.path.insert(0, sys.path[0] + "/scripts")
    import generate_training_data as gen
    with open(gen.TRAINING_FILE, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line.strip())
            assert "type" in d
            assert "input" in d
            assert "output" in d


def test_leak_filter_samples():
    sys.path.insert(0, sys.path[0] + "/scripts")
    import generate_training_data as gen
    ds = gen.build_dataset()
    leak_samples = [d for d in ds if d["type"] == "leak_filter"]
    assert len(leak_samples) >= 4
    # Check key cases
    texts = [d["input"]["fact"] for d in leak_samples]
    assert any("siaisenmtvsky" in t for t in texts)
    assert any("paisenmtvsky" in t for t in texts)
    # Output must have 'allowed' boolean
    for s in leak_samples:
        assert isinstance(s["output"]["allowed"], bool)


def test_cerewet_samples():
    sys.path.insert(0, sys.path[0] + "/scripts")
    import generate_training_data as gen
    ds = gen.build_dataset()
    cerewet = [d for d in ds if d["type"] == "social_cerewet"]
    assert len(cerewet) >= 5
    # Output must contain response + style
    for s in cerewet:
        assert "response" in s["output"]
        assert "style" in s["output"]
        assert "casual-id-cerewet" in s["output"]["style"]


def test_key_filter_samples():
    sys.path.insert(0, sys.path[0] + "/scripts")
    import generate_training_data as gen
    ds = gen.build_dataset()
    keys = [d for d in ds if d["type"] == "key_filter"]
    assert len(keys) >= 5
    # Traversal key must be False
    for k in keys:
        if "../" in k["input"]["key"] or "etc/" in k["input"]["key"]:
            assert k["output"]["allowed"] is False
