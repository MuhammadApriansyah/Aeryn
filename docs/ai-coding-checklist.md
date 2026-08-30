# AI Coding Agent Checklist (V59)

> **Purpose**: Checklist for AI coding agents (Claude Code, Cursor, OpenCode) when working on Aeryn.
> **Rule**: All items must pass before PR submission. No test doubles. Real testing only.

---

## ✅ Pre-Flight

- [ ] Read `CLAUDE.md` and `AGENTS.md`
- [ ] Understand the specific module/feature being modified
- [ ] Check working directory is `/home/sen/aeryn-core-agent`
- [ ] Activate venv: `source venv-proot/bin/activate`
- [ ] Backend running: `curl http://127.0.0.1:3010/health` → `{"status":"healthy"}`

## ✅ Code Standards

- [ ] **No test doubles** — no `unittest.mock`, no `MagicMock`, no stubs in `aeryn_core/` or `apps/`
- [ ] Follow existing patterns (check nearby code)
- [ ] Python: type hints, absolute imports, snake_case
- [ ] JavaScript: vanilla JS only (no npm packages), camelCase, `safeExecute()` wrapper
- [ ] CSS: dark/light theme support, `prefers-reduced-motion`
- [ ] Imports ordered: `patch_sqlite` first in Python files

## ✅ Changes Review

- [ ] **File size awareness**: `aeryn_api.py` is 4165+ lines, `dashboard.js` is 964 lines — understand before modifying
- [ ] **SQLite WAL**: Import `aeryn_core.utils.patch_sqlite` first if using SQLite
- [ ] **No PostgreSQL**: PostgreSQL errors are expected — the system uses SQLite. Don't try to install PostgreSQL.
- [ ] **No Docker**: All services run natively via PM2
- [ ] **Error handling**: Wrap in try/catch with `safeExecute()` (JS) or `with_retry`/`with_fallback` (Python)
- [ ] **Security**: Validate inputs, use `sanitize_output()` for LLM outputs
- [ ] **Memory**: Use `AerynVault` or `SocialMemory` for persistent data, no hardcoded values

## ✅ Feature Implementation

For **API endpoints** (`apps/api/aeryn_api.py`):
- [ ] Add endpoint following existing pattern (check nearby endpoints)
- [ ] Return consistent dict format: `{"status": "ok", "result": ...}` or `{"error": "..."}`
- [ ] Handle DB errors gracefully (fallback or return error)
- [ ] Add to `SPA routes` section if it's a new page route

For **SPA features** (`apps/web/static/js/dashboard.js`):
- [ ] Add to `navItems` array if it's a new page
- [ ] Add route in `server.py` (both `@app.get` and SPA route)
- [ ] Add render function with `safeExecute()` wrapper
- [ ] Add case to `renderPage()` switch
- [ ] Handle empty, loading, and error states
- [ ] Use `localStorage` for data persistence (no mock data)
- [ ] Add keyboard shortcuts where relevant

## ✅ Testing

- [ ] Run full suite: `python -m pytest tests/ -x -q`
- [ ] **All 661 tests pass**
- [ ] New feature has tests (at least 1 test per function)
- [ ] No `unittest.mock` introduced in production code
- [ ] Verify: `grep -rn "unittest.mock" aeryn_core/ apps/ --include="*.py"` → 0 results

## ✅ Audit & QC

- [ ] Real verification: `curl http://127.0.0.1:3010/health` → 200
- [ ] SPA routes: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3010/projects` → 200
- [ ] Static files: CSS/JS return 200
- [ ] No placeholder text in user-facing UI
- [ ] All functions return real values (no `return 0` placeholders)

## ✅ Documentation

- [ ] Update README.md (version, features, badges)
- [ ] Update CHANGELOG.md (new version entry)
- [ ] Update RELEASE file (version bump)
- [ ] Update relevant docs/ files if behavior changed

## ✅ Git & Push

- [ ] `git add -A`
- [ ] Commit: `git commit -m "type(scope): concise description"`
- [ ] Push: `git push origin main`
- [ ] Verify push succeeded (check URL or GitHub)

---

## ⚠️ Known Issues (Do Not "Fix")

- PostgreSQL connection errors → EXPECTED, SQLite fallback works
- `/plugins` direct URL → 500 (API route conflict), use client-side nav
- `RateLimiter.check()` TypeError → non-fatal, caught by middleware

---

## 🔄 Sprint Workflow

1. **Sprint N**: Implement features
2. **Sprint N Verify**: Full test + audit + QC + push
3. **Update documentation**: README + CHANGELOG + RELEASE
4. **Repeat** for Sprint N+1

---

*Checklist v59.0 — updated 2026-08-30*
