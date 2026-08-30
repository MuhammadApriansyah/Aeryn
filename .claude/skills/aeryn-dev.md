# Aeryn Development Workflow (Claude Code / Cursor)

## Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/MuhammadApriansyah/Aeryn.git
cd Aeryn

# 2. Create and activate virtual environment
python3 -m venv venv-proot
source venv-proot/bin/activate

# 3. Install dependencies (Python 3.11 required)
pip install -r requirements.txt
```

## Key Architecture Decisions

### Backend: Monolithic FastAPI (apps/api/aeryn_api.py)

- **Single file**: `aeryn_api.py` is 4154+ lines — understand before modifying
- **No Docker**: Runs directly via `venv-proot/bin/python`
- **Database**: SQLite only (no PostgreSQL). PostgreSQL connection errors are EXPECTED and handled gracefully via fallback
- **SQLite Patch**: `aeryn_core/utils/patch_sqlite.py` enables WAL + busy_timeout

### Frontend: Vanilla SPA (apps/web/)

- **Zero JS dependencies** — pure HTML, CSS, JavaScript
- **Single HTML file**: `dashboard.html` (2814 bytes)
- **Single JS file**: `dashboard.js` (964 lines)
- **Single CSS file**: `dashboard.css` (462 lines)
- Client-side routing via `window.history.pushState`
- Routes: `/`, `/projects`, `/workspaces`, `/chat`, `/plugins`, `/audit`, `/settings`

### Memory System

- `aeryn_core/memory/vault.py` — Obsidian-style knowledge base
- `aeryn_core/memory/social_memory.py` — User relationship tracking
- `aeryn_core/memory/hybrid_search.py` — BM25 + vector search
- `aeryn_core/memory/temporal_memory.py` — Time-based memory
- `aeryn_core/memory/enhanced_memory.py` — Entity + preference extraction

### Auth & Billing

- `aeryn_core/auth/auth.py` — Token validation
- `aeryn_core/auth/api_keys.py` — API key management
- `aeryn_core/auth/rate_limiter.py` — Rate limiting (Python + Rust)
- `aeryn_core/billing/billing.py` — Subscription plans
- `aeryn_core/billing/usage_metering.py` — Token usage tracking

### Safety

- `aeryn_core/safety/safety_engine.py` — Prompt injection detection
- `aeryn_core/safety/enhanced_guardrails.py` — Input/output validation
- `aeryn_core/safety/enhanced_sandbox.py` — 4-level execution sandbox
- `aeryn_core/safety/owasp_security.py` — OWASP compliance

### Adaptive System

- `aeryn_core/adaptive/__init__.py` — Self-healing orchestrator
- `aeryn_core/reasoning/self_improvement.py` — Feedback-based optimization

## Development Workflow

### 1. Check Existing Patterns

Before adding new code, examine:

```bash
# For API endpoints — check existing patterns
grep -n "@app.get\|@app.post" apps/api/aeryn_api.py | tail -10

# For SPA features — check existing renderers
grep -n "function render" apps/web/static/js/dashboard.js

# For memory modules — check existing patterns
ls aeryn_core/memory/

# For tests — check existing test patterns
ls tests/ | head -10
```

### 2. Add API Endpoint

```python
# In apps/api/aeryn_api.py, add near related endpoints:
@app.post("/api/v1/new-feature")
async def new_feature_endpoint(req: RequestNewFeature):
    engine = get_some_engine()
    result = engine.do_something(req.param)
    if not result:
        return {"status": "error", "message": "Failed"}
    return {"status": "ok", "result": result}
```

### 3. Add SPA Feature

```javascript
// In apps/web/static/js/dashboard.js

// 1. Add state
var myFeatureData = null;

// 2. Add to navItems array
{ id: 'myfeature', icon: '🔧', label: 'My Feature' }

// 3. Add case to renderPage()
case 'myfeature':
  renderMyFeature(container);
  break;

// 4. Add render function
function renderMyFeature(container) {
  if (!myFeatureData) {
    showLoading(container, 'Loading...');
    return;
  }
  container.innerHTML = '<div class="card"><h2>My Feature</h2>...</div>';
}

// 5. Add data fetch
function fetchMyFeature() {
  fetch('/api/py/my-feature')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      myFeatureData = data;
      if (currentPage === 'myfeature') renderPage();
    });
}
```

### 4. Run Tests

```bash
# MUST RUN AFTER EVERY CHANGE
source venv-proot/bin/activate
python -m pytest tests/ -x -q

# Run specific test file
python -m pytest tests/test_specific.py -x -q

# Run with verbose output
python -m pytest tests/ -x -v
```

### 5. Deploy

```bash
# Test passes → commit → push
git add -A
git commit -m "feat: your change description"
git push origin main

# Update docs
echo "V59.1" > RELEASE  # Update version
```

## Testing Strategy

- **Always run full suite**: `python -m pytest tests/ -x -q`
- **661 tests must pass**
- **NO test doubles** in production code — real implementations only
- Tests verify real functionality, not mocks
