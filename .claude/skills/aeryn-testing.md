# Aeryn Testing Strategy

## Running Tests

### Full Suite (Required After Every Change)

```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/ -x -q
```

Expected output: `**661 passed**` in ~35 seconds

### Individual Test Files

```bash
python -m pytest tests/test_adaptive.py -x -q
python -m pytest tests/test_api_endpoints.py -x -q
python -m pytest tests/test_auth.py -x -q
```

### Verbose Mode

```bash
python -m pytest tests/ -x -v --tb=short
```

## Test Philosophy

**NO test doubles in production code.** This is a strict rule.

- ✅ Real tests verify real behavior
- ✅ Tests use actual database connections (SQLite)
- ✅ Tests exercise real API endpoints
- ✅ Tests validate real data transformations
- ❌ No mocks, stubs, or fakes in production code
- ❌ No `unittest.mock` in `aeryn_core/` or `apps/`

## Test Coverage

| Area | Test Count | Description |
|------|-----------|-------------|
| Adaptive System | ~50 tests | Self-healing, error detection, fallback chains |
| Auth & Billing | ~80 tests | API keys, rate limiting, subscription plans |
| Memory System | ~120 tests | Vault, search, temporal memory, social memory |
| API Endpoints | ~150 tests | FastAPI endpoint validation |
| Safety | ~80 tests | Guardrails, sandbox, OWASP compliance |
| Platform | ~90 tests | Plugin system, notifications, task queue |
| Self-Improvement | ~30 tests | Feedback loop, prompt optimization |
| Web Dashboard | ~61 tests | SPA routing, health checks |

## Writing New Tests

### Test File Structure

```python
# tests/test_my_feature.py
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.my_module import MyClass

def test_my_function():
    # Arrange
    obj = MyClass()
    
    # Act
    result = obj.do_something("test")
    
    # Assert
    assert result == expected_value
    assert result is not None

def test_error_case():
    obj = MyClass()
    with pytest.raises(SomeException):
        obj.invalid_operation()
```

### Test Naming Convention

- `test_*` for successful cases
- `test_*_error` for error cases
- `test_*_empty` for empty input
- `test_*_invalid` for invalid input

### Test Fixtures

Tests use real SQLite databases in `tests/` directory. Database is created fresh for each test run:

```python
@pytest.fixture(autouse=True)
def setup_db():
    # Real database setup
    os.makedirs("tests/data", exist_ok=True)
    yield
    # Real cleanup
    import shutil
    if os.path.exists("tests/data"):
        shutil.rmtree("tests/data")
```

## Verifying No Test Doubles

```bash
# Check for mocks in production code
grep -rn "from unittest.mock import\|import mock" aeryn_core/ apps/ --include="*.py"

# Should return 0 results
# If it returns results, that's a violation
```

## CI Pipeline

Tests must pass before merge:

```bash
# 1. Run tests
python -m pytest tests/ -x -q

# 2. Verify no test doubles
grep -rn "unittest.mock" aeryn_core/ apps/ --include="*.py"

# 3. Check import works
python -c "from aeryn_core import *"

# All three must pass
```
