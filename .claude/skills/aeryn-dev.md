# Aeryn Development Workflow

## How to Add New Features

### Step 1: Check Existing Patterns First

Before writing any code, always check if a similar pattern already exists:

```bash
# Search for similar functionality
grep -r "def get_" aeryn_core/ --include="*.py" | head -20
grep -r "class.*Manager" aeryn_core/ --include="*.py" | head -20
grep -r "router\." apps/api/aeryn_api.py | head -20
```

Most features follow a **singleton manager pattern**:
- `get_<feature>_manager()` or `get_<feature>()` returns singleton instance
- Manager class encapsulates all state and logic
- Initialization happens lazily on first call

### Step 2: Implement the Feature

Create the module in the appropriate `aeryn_core/` subdirectory:

```python
# aeryn_core/<category>/my_feature.py

class MyFeature:
    def __init__(self):
        self._initialized = False
        self._data = {}
    
    def initialize(self):
        """Lazy initialization."""
        if self._initialized:
            return
        # Setup code here
        self._initialized = True
    
    def do_something(self, param: str) -> dict:
        """Main feature logic."""
        self.initialize()
        return {"result": param}

# Singleton
_instance = None

def get_my_feature() -> MyFeature:
    global _instance
    if _instance is None:
        _instance = MyFeature()
    return _instance
```

### Step 3: Add API Endpoint (if needed)

In `apps/api/aeryn_api.py`, add FastAPI endpoints:

```python
# Import at top
from aeryn_core.<category>.my_feature import get_my_feature

# Add endpoint
@app.get("/api/v1/my-feature")
async def my_feature_endpoint():
    feature = get_my_feature()
    return feature.do_something("default")

@app.post("/api/v1/my-feature")
async def my_feature_post(data: dict):
    feature = get_my_feature()
    return feature.do_something(data.get("param", ""))
```

### Step 4: Add SPA Feature (if needed)

In `apps/web/static/js/dashboard.js`, add to the IIFE:

```javascript
// Add to navItems if new page
{ id: 'myfeature', icon: '🔧', label: 'My Feature', category: 'work' }

// Add page handler
function showMyFeaturePage() {
  var container = document.getElementById('page-content');
  container.innerHTML = '<div class="page">' +
    '<h1>My Feature</h1>' +
    '<div class="card">Content here</div>' +
    '</div>';
}

// Add to router
case 'myfeature':
  showMyFeaturePage();
  break;
```

### Step 5: Write Tests

```python
# tests/test_my_feature.py
import pytest
from aeryn_core.<category>.my_feature import get_my_feature

class TestMyFeature:
    def setup_method(self):
        self.feature = get_my_feature()
    
    def test_do_something(self):
        result = self.feature.do_something("test")
        assert result["result"] == "test"
    
    def test_singleton(self):
        a = get_my_feature()
        b = get_my_feature()
        assert a is b
```

### Step 6: Run Tests

```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/test_my_feature.py -x -q
python -m pytest tests/ -x -q  # Full suite
```

## How to Run Tests and Verify Changes

### Full Test Suite
```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/ -x -q
```

### Single Test File
```bash
python -m pytest tests/test_safety_engine.py -x -q
```

### Single Test Function
```bash
python -m pytest tests/test_safety_engine.py::TestSafetyEngine::test_sanitize -x -q
```

### With Verbose Output
```bash
python -m pytest tests/ -x -v
```

### Check Test Count
```bash
python -m pytest tests/ --collect-only -q | tail -1
```

## How to Add API Endpoints (FastAPI Pattern)

The API file `apps/api/aeryn_api.py` is 4,182 lines. Key patterns:

### 1. Import at top of file
```python
from aeryn_core.<category>.<module> import get_<manager>, SomeClass
```

### 2. Define Pydantic models for request/response
```python
class MyRequest(BaseModel):
    param1: str = Field(..., description="Parameter 1")
    param2: int = Field(default=10, ge=0, le=100)
```

### 3. Add route with proper decorators
```python
@app.get("/api/v1/items", tags=["items"])
async def list_items(
    limit: int = 50,
    offset: int = 0,
    auth: str = Header(None)
):
    """List items with pagination."""
    items = get_item_manager().list_items(limit=limit, offset=offset)
    return {"items": items, "total": len(items)}
```

### 4. Error handling pattern
```python
@app.post("/api/v1/items", tags=["items"])
async def create_item(data: MyRequest):
    try:
        result = get_item_manager().create(data.param1, data.param2)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error("create_item failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")
```

### 5. WebSocket pattern
```python
@app.websocket("/ws/items")
async def items_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            result = process_item(data)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
```

## How to Add SPA Features (Vanilla JS Pattern)

The dashboard `apps/web/static/js/dashboard.js` is 964 lines. Key patterns:

### 1. Everything in IIFE
```javascript
(function() {
  'use strict';
  // All code here
})();
```

### 2. State variables at top
```javascript
var myFeatureData = null;
var myFeatureEnabled = false;
```

### 3. Functions for features
```javascript
function loadMyFeature() {
  fetch('/api/v1/my-feature')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      myFeatureData = data;
      renderMyFeature();
    })
    .catch(function(err) {
      showErrorBoundary(err.message, err.stack);
    });
}
```

### 4. DOM manipulation
```javascript
function renderMyFeature() {
  var container = document.getElementById('page-content');
  if (!container) return;
  
  var html = '<div class="page">' +
    '<h1>My Feature</h1>' +
    '<div class="card">' +
    '<p>' + (myFeatureData.message || 'No data') + '</p>' +
    '</div></div>';
  
  container.innerHTML = html;
}
```

### 5. Navigation routing
```javascript
case 'myfeature':
  showMyFeaturePage();
  break;
```

## Self-Improvement System (Adaptive)

The adaptive system lives in `aeryn_core/adaptive/__init__.py` (34K). It provides:

### Key Features
1. **Error Detection & Auto-Recovery** — Catches exceptions and retries with backoff
2. **Recursive Self-Improvement Loop** — Learns from past errors
3. **Adaptive Behavior Adjustment** — Adjusts parameters based on success/failure
4. **Self-Healing Infrastructure** — Restarts failed components
5. **Continuous Learning** — Stores error patterns in SQLite
6. **Health Monitoring** — Tracks system health metrics
7. **Fallback Chain** — Cascading fallback for failed operations
8. **Performance Optimization** — Auto-tunes based on metrics

### How to Use Adaptive Features

```python
from aeryn_core.adaptive import get_adaptive_system

adaptive = get_adaptive_system()

# Record an error for learning
adaptive.record_error("api_call", error_message, context)

# Get adaptive recommendation
recommendation = adaptive.get_recommendation("api_call", context)

# Check if component should be retried
if adaptive.should_retry("component_name"):
    # Retry logic
    pass
```

### Adding New Adaptive Behaviors

1. Add detection logic in `aeryn_core/adaptive/__init__.py`
2. Create recovery strategies as methods
3. Register in the main `AdaptiveSystem` class
4. Add tests in `tests/test_adaptive_engine.py`

## Common Pitfalls

1. **Don't add npm packages** — Frontend is vanilla JS only
2. **Don't add PostgreSQL** — SQLite only
3. **Don't use test doubles in production** — Real implementations only
4. **Don't skip WAL patch** — Always import `aeryn_core.utils.patch_sqlite` first
5. **Don't modify ecosystem.config.cjs without testing** — PM2 restart required
6. **Don't add routes that conflict with SPA** — `/plugins` API conflicts with SPA route
7. **Don't forget to activate venv** — `source venv-proot/bin/activate`