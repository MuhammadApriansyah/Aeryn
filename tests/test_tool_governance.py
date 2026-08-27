"""Test ToolGovernanceGate — tier rules, argument scanning, audit."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.tool_governance import ToolGovernanceGate


class TestToolGovernanceGateInit:
    """Tests for ToolGovernanceGate initialization."""

    def test_init_no_drift_shield(self):
        gate = ToolGovernanceGate()
        assert gate.drift_shield is None
        assert gate.audit == []

    def test_init_with_drift_shield(self):
        shield = MagicMock()
        gate = ToolGovernanceGate(drift_shield=shield)
        assert gate.drift_shield is shield


class TestToolGovernanceGateEvaluate:
    """Tests for ToolGovernanceGate.evaluate()."""

    def test_safe_tool_allowed(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="read_file",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"path": "/tmp/test.txt"}
        )
        assert result["allowed"] is True
        assert result["reason"] == "allowed"

    def test_fs_tool_allowed(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="write_file",
            tier="fs",
            status="native",
            success=5,
            fail=1,
            args={"path": "/tmp/output.txt", "content": "hello"}
        )
        assert result["allowed"] is True

    def test_power_tool_needs_mentor(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="terminal",
            tier="power",
            status="native",
            success=10,
            fail=0,
            args={"command": "ls"}
        )
        assert result["allowed"] is False
        assert "power_tier" in result["reason"] or "mentor" in result["reason"]

    def test_dangerous_arg_rm_rf(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="terminal",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"command": "rm -rf /"}
        )
        assert result["allowed"] is False
        assert "dangerous_arg" in result["reason"]

    def test_dangerous_arg_mkfs(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="terminal",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"command": "mkfs /dev/sda"}
        )
        assert result["allowed"] is False

    def test_dangerous_arg_fork_bomb(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="terminal",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"command": ":(){ :|:& };:"}
        )
        assert result["allowed"] is False

    def test_dangerous_arg_sensitive_path(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="read_file",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"path": "/etc/shadow"}
        )
        assert result["allowed"] is False

    def test_dangerous_arg_aws_credentials(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="read_file",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"path": "~/.aws/credentials"}
        )
        assert result["allowed"] is False

    def test_poor_track_record_blocks(self):
        gate = ToolGovernanceGate()
        result = gate.evaluate(
            tool_name="risky_tool",
            tier="fs",
            status="native",
            success=2,
            fail=8,
            args={"path": "/tmp/safe.txt"}
        )
        assert result["allowed"] is False
        assert "track_record" in result["reason"]

    def test_drift_shield_intercepts(self):
        shield = MagicMock()
        shield.execute_sub_brain_reasoning.return_value = {
            "attack_vector_intercepted": True
        }
        gate = ToolGovernanceGate(drift_shield=shield)
        result = gate.evaluate(
            tool_name="tool",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"data": "suspicious"}
        )
        assert result["allowed"] is False
        assert "injection" in result["reason"]

    def test_drift_shield_fails_open(self):
        """If drift shield raises, tool should still be allowed."""
        shield = MagicMock()
        shield.execute_sub_brain_reasoning.side_effect = RuntimeError("shield down")
        gate = ToolGovernanceGate(drift_shield=shield)
        result = gate.evaluate(
            tool_name="tool",
            tier="safe",
            status="native",
            success=10,
            fail=0,
            args={"data": "normal"}
        )
        assert result["allowed"] is True


class TestToolGovernanceGateAudit:
    """Tests for audit trail and digest."""

    def test_audit_records_decisions(self):
        gate = ToolGovernanceGate()
        gate.evaluate("tool_a", "safe", "native", 10, 0, {"x": 1})
        gate.evaluate("tool_b", "power", "native", 10, 0, {"x": 2})
        assert len(gate.audit) == 2

    def test_audit_caps_at_200(self):
        gate = ToolGovernanceGate()
        for i in range(250):
            gate.evaluate(f"tool_{i}", "safe", "native", 10, 0, {"x": i})
        assert len(gate.audit) <= 200

    def test_digest_audit_empty(self):
        gate = ToolGovernanceGate()
        digest = gate.digest_audit()
        assert digest["total_calls"] == 0
        assert digest["denied"] == 0
        assert digest["status"] == "VERIFIED_COMPLIANT"

    def test_digest_audit_with_denials(self):
        gate = ToolGovernanceGate()
        gate.evaluate("safe_tool", "safe", "native", 10, 0, {"x": 1})
        gate.evaluate("dangerous", "safe", "native", 10, 0, {"cmd": "rm -rf /"})
        digest = gate.digest_audit()
        assert digest["total_calls"] == 2
        assert digest["denied"] == 1
        assert digest["status"] == "ANOMALIES_PRESENT"
        assert len(digest["denial_reasons"]) > 0


# Need MagicMock for the drift shield tests
from unittest.mock import MagicMock