# Pipeline Templates

> **Purpose**: Standard templates for development pipeline operations.
> **Rule**: Copy-paste templates — no need to start from scratch.

---

## 🏗️ Sprint Planning Template

```markdown
# Sprint N Plan (VYY.Z — Weeks A-B)

## Overview
Brief description of what this sprint accomplishes.

## Goals
- [ ] Goal 1: Description
- [ ] Goal 2: Description  
- [ ] Goal 3: Description

## Files to Create/Modify
| # | File | Action | Lines | Priority |
|---|------|--------|-------|----------|
| 1 | `path/to/file` | Create | ~100 | ⭐⭐⭐⭐⭐ |
| 2 | `path/to/file` | Modify | +50 lines | ⭐⭐⭐⭐ |

## Implementation Order
1. First task (prerequisite for all others)
2. Second task (depends on first)
3. Third task (parallel with second)
...

## Success Criteria
- [ ] 661 tests pass
- [ ] No test doubles in production code
- [ ] All endpoints return 200
- [ ] README + CHANGELOG + RELEASE updated
- [ ] Pushed to origin/main

## Dependencies
- List any external dependencies

## Risks
- Risk 1: Mitigation strategy
- Risk 2: Mitigation strategy
```

---

## 🧪 Test Verification Template

```bash
#!/bin/bash
# tests/verify_sprint_N.sh

set -e

echo "=== Sprint N Test Verification ==="

# 1. Full test suite
echo "1. Running full test suite..."
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5

# 2. Check for test doubles
echo "2. Checking for test doubles..."
DOUBLES=$(grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py" | wc -l)
if [ "$DOUBLES" -gt 0 ]; then
    echo "❌ FAIL: Found $DOUBLES test double references"
    grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py"
    exit 1
else
    echo "✅ PASS: No test doubles in production code"
fi

# 3. Check for placeholders
echo "3. Checking for placeholders..."
PLACEHOLDERS=$(grep -rn "#.*TODO\|#.*FIXME\|pass$" aeryn_core/ --include="*.py" | grep -v "pass  #" | grep -v "pass  #" | wc -l)
if [ "$PLACEHOLDERS" -gt 0 ]; then
    echo "⚠️ WARNING: Found $PLACEHOLDERS potential placeholders"
    grep -rn "#.*TODO\|#.*FIXME\|pass$" aeryn_core/ --include="*.py" | grep -v "pass  #"
fi

# 4. Verify endpoints
echo "4. Verifying endpoints..."
for endpoint in /health /projects /workspaces /chat; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:3010${endpoint}")
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $endpoint: $CODE"
    else
        echo "  ⚠️ $endpoint: $CODE"
    fi
done

# 5. Verify static files
echo "5. Verifying static files..."
for file in "/web/static/css/dashboard.css" "/web/static/js/dashboard.js"; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:3010${file}")
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $file: $CODE"
    else
        echo "  ❌ $file: $CODE"
        exit 1
    fi
done

echo "=== All Verifications Complete ==="
```

---

## 📝 Commit Message Template

```
Sprint N: [brief description of changes]

Changes:
- Implemented: [feature description]
- Fixed: [bug fix description]
- Docs: [documentation changes]

Tests: 661 passed
No test doubles introduced
```

Example:
```
Sprint 3: Pipeline and channel documentation

Changes:
- Implemented: 4 pipeline documentation files
- Fixed: Updated sprint tracking table
- Docs: phases.md, team.md, gates.md, templates.md

Tests: 661 passed
```

---

## 📊 Sprint Tracking Template

Add to `docs/documentation-todo.md`:

```markdown
### Sprint N (VYY — Week A-B)
| # | File | Priority | Status |
|---|------|----------|--------|
| 1 | `path/to/file` | ⭐⭐⭐⭐⭐ | ❌ |
| 2 | `path/to/file` | ⭐⭐⭐⭐ | ❌ |
```

---

## 🔄 Handoff Template

For cross-session agent sync:

```bash
handoff.py --task "Complete Sprint N implementation: [specific task]"
```

Context to include:
- Current working directory
- Sprint status
- Files modified
- Tests passing count
```

---

## 📋 QC Checklist Template

```markdown
## Sprint N QC Verification

### Code Quality
- [ ] No `unittest.mock` in aeryn_core/ or apps/
- [ ] No `TODO` or `FIXME` comments in new code
- [ ] No placeholder returns (return 0, return False, NotImplemented)
- [ ] Code follows existing patterns

### Testing
- [ ] `python -m pytest tests/ -x -q` → 661 passed
- [ ] New tests added for new features
- [ ] All endpoints return expected status codes

### Documentation
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] RELEASE file bumped
- [ ] New docs created if needed

### Deployment
- [ ] All changes committed with proper message
- [ ] Pushed to `origin/main`
- [ ] Version tag updated if major change
```

---

*Pipeline templates v59.0 — Updated 2026-08-30.*
