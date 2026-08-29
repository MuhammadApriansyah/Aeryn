#!/usr/bin/env python3
"""Test sandbox modules."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

def test_detector():
    from aeryn_core.sandbox.detector import EnvironmentDetector
    caps = EnvironmentDetector.get_capabilities()
    assert "level" in caps
    assert "bubblewrap" in caps
    assert 0 <= caps["level"] <= 3
    print(f"✓ Detector (level={caps['level']}, caps={caps})")

def test_basic_sandbox():
    from aeryn_core.sandbox.level0_basic import BasicSandbox
    sb = BasicSandbox()
    result = sb.execute(["echo", "hello sandbox"])
    assert result.get("returncode") == 0
    assert "hello sandbox" in result.get("stdout", "")
    print("✓ BasicSandbox")

def test_basic_whitelist():
    from aeryn_core.sandbox.level0_basic import BasicSandbox
    sb = BasicSandbox()
    result = sb.execute(["rm", "-rf", "/"])
    assert "error" in result
    print("✓ BasicSandbox whitelist")

def test_namespace_sandbox():
    from aeryn_core.sandbox.level1_namespace import NamespaceSandbox
    sb = NamespaceSandbox()
    result = sb.execute(["echo", "namespace test"])
    assert result.get("returncode") == 0
    assert "namespace test" in result.get("stdout", "")
    print("✓ NamespaceSandbox")

def test_fallback_orchestrator():
    from aeryn_core.sandbox.fallback import FallbackOrchestrator
    orch = FallbackOrchestrator()
    status = orch.status()
    assert "level" in status
    result = orch.execute(["echo", "fallback test"])
    assert "fallback test" in result.get("stdout", "")
    print(f"✓ FallbackOrchestrator (level={status['level']})")

def test_bubblewrap_sandbox():
    from aeryn_core.sandbox.level2_bubblewrap import BubblewrapSandbox
    sb = BubblewrapSandbox()
    if sb.is_available():
        result = sb.execute(["echo", "bwrap test"])
        assert result.get("returncode") == 0
        print("✓ BubblewrapSandbox")
    else:
        print("⊘ BubblewrapSandbox (not available, skipped)")

if __name__ == "__main__":
    test_detector()
    test_basic_sandbox()
    test_basic_whitelist()
    test_namespace_sandbox()
    test_fallback_orchestrator()
    test_bubblewrap_sandbox()
    print("\n✅ All sandbox tests passed!")
