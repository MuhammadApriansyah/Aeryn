# Aeryn — Testing Strategy

## Test Location

All tests are in the `/home/sen/aeryn-core-agent/tests/` directory.

```
tests/
├── test_adaptive_engine.py
├── test_core.py
├── test_features.py
├── test_fullstack.py
├── test_graph_memory.py
├── test_hybrid_search.py
├── test_mcp_multiagent.py
├── test_oneclick.py
├── test_orchestrator.py
├── test_rate_limiter.py
├── test_sandbox.py
├── test_security_cost.py
├── test_supersession.py
├── test_tool_governance.py
├── test_v29_*.py through test_v57_features.py
└── ... (91 total test files)
```

## How to Run Tests

### Full Suite
```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/ -x -q
```

**Options:**
- `-x` — Stop on first failure
- `-q` — Quiet mode (one line per result)
- `-v` — Verbose mode (full test names)
- `--tb=short` — Short tracebacks

### Single File
```bash
python -m pytest tests/test_safety_engine.py -x -q
```

### Single Test
```bash
python -m pytest tests/test_safety_engine.py::TestSafetyEngine::test_sanitize -x -q
```

### By Keyword
```bash
python -m pytest tests/ -k "rate_limit" -x -q
```

## Test Count

- **91 test files**
- **661 total tests**
- Coverage spans: auth, billing, memory, reasoning, safety, API, platform

## Test Patterns

### Pattern 1: Real Testing (NO Test Doubles)

**CRITICAL:** Production code must NEVER contain mocks, stubs, or fakes. All testing uses real implementations.

```python
# CORRECT — Real implementation
def test_vault_storage():
    vault = AerynVault()
    entry = VaultEntry(key="test", value={"data": 123}, layer=LAYER_WIKI)
    vault.store(entry)
    result = vault.retrieve("test")
    assert result.value == {"data": 123}

# WRONG — Mock in production test path
def test_with_mock():
    mock_vault = Mock(AerynVault)  # Don't do this in production code
    mock_vault.retrieve.return_value = fake_entry
```

### Pattern 2: Singleton Reset

Since many components are singletons, tests may need reset:

```python
class TestMyFeature:
    def setup_method(self):
        # Get fresh singleton instance
        self.feature = get_my_feature()
        # Reset state if needed
        self.feature._reset()
```

### Pattern 3: SQLite In-Memory for Tests

```python
def test_database_operation():
    # Use in-memory DB for isolation
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO test (data) VALUES ('hello')")
    result = conn.execute("SELECT data FROM test").fetchone()
    assert result[0] == "hello"
```

### Pattern 4: Pydantic Validation Tests

```python
def test_request_validation():
    # Valid request
    req = MyRequest(param1="valid", param2=50)
    assert req.param2 == 50
    
    # Invalid request raises ValidationError
    with pytest.raises(ValidationError):
        MyRequest(param1="", param2=-1)
```

### Pattern 5: API Endpoint Tests

```python
from fastapi.testclient import TestClient

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### Pattern 6: Async Tests

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### Pattern 7: Error Recovery Tests

```python
def test_retry_mechanism():
    recovery = get_error_recovery()
    
    call_count = 0
    
    @with_retry(max_attempts=3, delay=0.1)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = flaky()
    assert result == "success"
    assert call_count == 3
```

## Test File Naming

| Pattern | Example |
|---------|---------|
| `test_<feature>.py` | `test_safety_engine.py` |
| `test_v<version>_<feature>.py` | `test_v38_1_subagents.py` |
| `test_<category>.py` | `test_features.py` |

## Writing New Tests

### Step 1: Create test file
```python
# tests/test_my_new_feature.py
"""
Tests for My New Feature.
"""

import pytest
from aeryn_core.<category>.my_new_feature import get_my_new_feature


class TestMyNewFeature:
    """Test suite for MyNewFeature."""
    
    def setup_method(self):
        """Reset state before each test."""
        self.feature = get_my_new_feature()
        self.feature._reset()
    
    def test_basic_functionality(self):
        """Test basic operation works."""
        result = self.feature.do_something("input")
        assert result is not None
        assert "output" in result
    
    def test_edge_case_empty_input(self):
        """Test behavior with empty input."""
        with pytest.raises(ValueError):
            self.feature.do_something("")
    
    def test_singleton_pattern(self):
        """Verify singleton behavior."""
        a = get_my_new_feature()
        b = get_my_new_feature()
        assert a is b
    
    def test_state_persistence(self):
        """Verify state persists across calls."""
        self.feature.set_state("key", "value")
        assert self.feature.get_state("key") == "value"
    
    def test_concurrent_access(self):
        """Test thread safety if applicable."""
        import threading
        
        results = []
        
        def worker():
            results.append(self.feature.do_something("input"))
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 10
```

### Step 2: Run new tests
```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/test_my_new_feature.py -x -v
```

### Step 3: Verify full suite still passes
```bash
python -m pytest tests/ -x -q
```

## Test Categories

| Category | Files | What's Tested |
|----------|-------|---------------|
| Auth | `test_rate_limiter.py`, `test_v36_credential_health.py` | API keys, rate limits, credentials |
| Billing | `test_security_cost.py` | Plans, pricing, usage |
| Memory | `test_graph_memory.py`, `test_hybrid_search.py`, `test_supersession.py` | Vault, search, graph, decay |
| Safety | `test_sandbox.py`, `test_production_guard.py` | Sandbox, guardrails, security |
| Features | `test_v50_features.py` through `test_v57_features.py` | Sprint features |
| Platform | `test_mcp_multiagent.py`, `test_tool_governance.py` | MCP, multi-agent, tools |
| API | `test_fullstack.py`, `test_core.py` | End-to-end API flows |
| Adaptive | `test_adaptive_engine.py` | Self-improvement system |

## Test Fixtures

Common fixtures can be defined in `conftest.py` (if needed):

```python
# tests/conftest.py
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def vault():
    from aeryn_core.memory.vault import AerynVault
    v = AerynVault()
    v._reset()
    return v

@pytest.fixture
def rate_limiter():
    from aeryn_core.auth.rate_limiter import get_rate_limiter
    rl = get_rate_limiter()
    rl._reset()
    return rl
```

## Coverage Gaps

When writing tests, focus on:
1. **Error paths** — Not just happy paths
2. **Edge cases** — Empty input, null values, boundary conditions
3. **State management** — Singleton state, persistence, cleanup
4. **Concurrency** — Thread safety for shared resources
5. **Validation** — Pydantic model validation, input sanitization

## Continuous Testing

After ANY code change:
```bash
python -m pytest tests/ -x -q
```

This runs all 661 tests and stops on first failure.