#!/usr/bin/env python3
"""Test rate_limiter module."""
import sys, os, time
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.rate_limiter import RateLimiter, CircuitBreaker, get_circuit_breaker

def test_rate_limiter():
    rl = RateLimiter()
    # Test basic rate limiting (default free limits: 100/min)
    result1 = rl.check("user_test_1", "/test", "GET")
    assert result1["allowed"] == True
    result2 = rl.check("user_test_1", "/test", "GET")
    assert result2["allowed"] == True

def test_rate_limiter_separate_keys():
    rl = RateLimiter()
    # Different users should have separate limits
    result1 = rl.check("user_test_a", "/test", "GET")
    result2 = rl.check("user_test_b", "/test", "GET")
    assert result1["allowed"] == True
    assert result2["allowed"] == True

def test_circuit_breaker():
    cb = CircuitBreaker(max_failures=2, base_wait=1.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_opened()
    assert cb.should_skip()

def test_circuit_breaker_recovery():
    cb = CircuitBreaker(max_failures=1, base_wait=0.1)
    cb.record_failure()
    time.sleep(0.15)
    assert not cb.should_skip()
