#!/usr/bin/env python3
"""Test rate_limiter module."""
import sys, os, time
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.rate_limiter import RateLimiter, CircuitBreaker, get_circuit_breaker

def test_rate_limiter():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    assert rl.allow("user1")
    assert rl.allow("user1")
    assert rl.allow("user1")
    assert not rl.allow("user1")

def test_rate_limiter_separate_keys():
    rl = RateLimiter(max_requests=1, window_seconds=60)
    assert rl.allow("user1")
    assert rl.allow("user2")
    assert not rl.allow("user1")

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