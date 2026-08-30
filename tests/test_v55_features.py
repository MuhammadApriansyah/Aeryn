#!/usr/bin/env python3
"""Test V55 features: Workspace, Audit, Rate Limit, Cache, Job Queue."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_workspace():
    from aeryn_core.workspace import workspace_manager
    import uuid; ws = workspace_manager.create_workspace(f"Test WS {uuid.uuid4().hex[:8]}", "Test workspace")
    assert "Test WS" in ws["name"]
    
    workspaces = workspace_manager.list_workspaces()
    assert len(workspaces) >= 1
    
    workspace_manager.add_project(ws["id"], "test-project", "/tmp/test")
    print("✓ WorkspaceManager")


def test_audit_trail():
    from aeryn_core.audit_trail import audit_trail
    audit_trail.log("user_1", "create_project", "my-app", "Created new project")
    audit_trail.log("user_1", "deploy", "my-app", "Deployed to production")
    
    logs = audit_trail.get_logs(limit=10)
    assert len(logs) >= 2
    print("✓ AuditTrail")


def test_rate_limiter():
    from aeryn_core.rate_limiting import rate_limiter
    assert rate_limiter.is_allowed("client_1") is True
    
    middleware = rate_limiter.get_middleware_code("fastify")
    assert "rateLimit" in middleware
    print("✓ RateLimiter")


def test_cache_layer():
    from aeryn_core.cache_layer import cache_layer
    files = cache_layer.generate_redis_config()
    assert "config/redis.js" in files
    assert "middleware/cache.js" in files
    print("✓ CacheLayer")


def test_job_queue():
    from aeryn_core.job_queue import job_queue
    files = job_queue.generate_queue_config()
    assert "config/queue.js" in files
    assert "jobs/sendEmail.js" in files
    print("✓ JobQueue")


if __name__ == "__main__":
    test_workspace()
    test_audit_trail()
    test_rate_limiter()
    test_cache_layer()
    test_job_queue()
    print("\n✅ All V55 feature tests passed!")
