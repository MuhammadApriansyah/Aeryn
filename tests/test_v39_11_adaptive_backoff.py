"""Test V39.11 — model_client circuit breaker + single-attempt fix."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core import model_client as mc
from aeryn_core.model_client import CircuitBreaker


def test_circuit_breaker_exists():
    assert hasattr(mc, "CircuitBreaker")


def test_circuit_breaker_states():
    cb = CircuitBreaker(max_failures=1)
    assert cb.is_opened() is False
    cb.record_failure()
    assert cb.is_opened() is True
    assert cb.retry_after() > 0
    cb.reset()
    assert not cb.is_opened()


def test_adaptive_backoff():
    cb = CircuitBreaker(max_failures=2)
    cb.record_failure()
    w1 = cb.retry_after()
    cb.record_failure()
    w2 = cb.retry_after()
    assert w2 > w1


def test_skip_after_max_failures():
    cb = CircuitBreaker(max_failures=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_opened()
    assert cb.should_skip() is True
    cb._fail_time -= 9999
    assert cb.should_skip() is False


def test_single_attempt_in_codebase():
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),
        "aeryn_core", "model_client.py")).read()
    assert "for attempt in range(1)" in src
