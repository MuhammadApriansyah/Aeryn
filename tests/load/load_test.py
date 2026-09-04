#!/usr/bin/env python3
"""Load Test — concurrency, throughput, latency, error rate, memory.

Real load (not mock): fires N concurrent requests at /v1/chat and measures
P50/P95/P99 latency, throughput, error rate, and memory growth.
"""

import asyncio
import aiohttp
import time
import json
import sys
from collections import defaultdict

BASE = "http://127.0.0.1:3010"


async def fire_request(session, i):
    """Fire one chat request. Returns (latency, status, error)."""
    start = time.time()
    try:
        async with session.post(
            f"{BASE}/v1/chat",
            json={"message": f"Count from 1 to {i % 10 + 1}", "session_id": f"load_{i}"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            await resp.read()
            latency = time.time() - start
            return latency, resp.status, None
    except Exception as e:
        latency = time.time() - start
        return latency, None, str(e)


async def run_load(n_requests, concurrency):
    """Run n_requests with given concurrency."""
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(concurrency)
        
        async def bounded(i):
            async with sem:
                return await fire_request(session, i)
        
        tasks = [bounded(i) for i in range(n_requests)]
        results = await asyncio.gather(*tasks)
    
    return results


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0
    idx = int(len(sorted_vals) * p / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


async def get_memory():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE}/health") as resp:
                data = await resp.json()
                return data.get("memory_mb", 0)
    except:
        return 0


async def main():
    levels = [10, 50, 100]
    
    print("=" * 70)
    print("AERYN LOAD TEST — /v1/chat concurrency")
    print("=" * 70)
    
    mem_start = await get_memory()
    print(f"Memory before: {mem_start} MB\n")
    
    for n in levels:
        # Use concurrency = n (all at once)
        concurrency = n
        t0 = time.time()
        results = await run_load(n, concurrency)
        total_time = time.time() - t0
        
        latencies = sorted([r[0] for r in results])
        statuses = [r[1] for r in results]
        errors = [r for r in results if r[2] is not None]
        
        # Count status codes
        status_counts = defaultdict(int)
        for s in statuses:
            status_counts[s or "error"] += 1
        
        ok_count = sum(1 for s in statuses if s == 200)
        error_count = sum(1 for s in statuses if s != 200)
        
        throughput = n / total_time if total_time > 0 else 0
        
        print(f"--- {n} concurrent requests ---")
        print(f"  Throughput: {throughput:.1f} req/sec")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Latency P50: {percentile(latencies, 50)*1000:.0f}ms")
        print(f"  Latency P95: {percentile(latencies, 95)*1000:.0f}ms")
        print(f"  Latency P99: {percentile(latencies, 99)*1000:.0f}ms")
        print(f"  Success (200): {ok_count}/{n}")
        print(f"  Error rate: {error_count}/{n} ({100*error_count/n:.1f}%)")
        print(f"  Status breakdown: {dict(status_counts)}")
        if errors:
            print(f"  First error: {errors[0][2][:80]}")
        print()
    
    mem_end = await get_memory()
    print(f"Memory after: {mem_end} MB (delta: {mem_end - mem_start:+.1f} MB)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())