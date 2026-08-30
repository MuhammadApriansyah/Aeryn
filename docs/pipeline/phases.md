# Development Pipeline

> **Purpose**: Document the Aeryn development pipeline — phases, team roles, gates, and templates.
> **Rule**: Real workflow based on actual Sprint methodology used in Aeryn V59.

---

## 🔄 Pipeline Phases

### Phase 1: Planning (Sprint 0)

**Duration**: 1-2 days  
**Goal**: Verify existing code, document findings, plan implementation

Steps:
1. Audit existing codebase for placeholders and test doubles
2. Verify all 661 tests pass
3. Document findings in `docs/` directory
4. Create implementation plan with Sprint breakdown

Deliverables:
- Audit report
- Implementation plan
- Sprint schedule

### Phase 2: Implementation (Sprint 1-N)

**Duration**: 1-2 weeks per sprint  
**Goal**: Implement features without test doubles

Steps:
1. Implement features following existing patterns
2. Write tests for each new function
3. Run full suite: `python -m pytest tests/ -x -q`
4. **All 661 tests must pass**
5. Update README + CHANGELOG + RELEASE
6. Push to `origin/main`

Deliverables:
- Working code (no test doubles)
- Updated tests
- Documentation updates

### Phase 3: Audit & QC (Per Sprint)

**Duration**: 1-2 hours per sprint  
**Goal**: Verify real implementation, no placeholder code

Steps:
1. Full suite test run
2. Endpoint verification via curl
3. No test doubles check: `grep -rn "unittest.mock" aeryn_core/ apps/`
4. Code audit for placeholder returns
5. Push verification

Deliverables:
- Audit report
- QC checklist

### Phase 4: Documentation (Per Sprint)

**Duration**: 1 day per sprint  
**Goal**: Keep documentation current

Steps:
1. Update CLAUDE.md with any new patterns
2. Update AGENTS.md with new directory structure
3. Update CHANGELOG.md with new changes
4. Update RELEASE file with version bump
5. Add new docs as needed

Deliverables:
- Updated documentation
- Version bump

---

## 👥 Team Roles

| Role | Responsibilities |
|------|-----------------|
| **Lead Agent** | Overall direction, code review, test verification |
| **Implementation Agent** | Write production code, follow conventions |
| **Testing Agent** | Verify tests pass, check for test doubles |
| **Documentation Agent** | Update docs after each sprint |
| **QC Agent** | Final audit + QC, curl verification |

---

## 🚧 Pipeline Gates

### Gate 1: Sprint Planning Approval

**Requirements**:
- [ ] Audit baseline established (661 tests pass)
- [ ] No test doubles in existing code
- [ ] Implementation plan documented
- [ ] Sprint schedule defined

### Gate 2: Implementation Complete

**Requirements**:
- [ ] All planned features implemented
- [ ] No test doubles in new code
- [ ] No placeholder returns (return 0, return False, NotImplemented)
- [ ] Code follows existing patterns

### Gate 3: Test Verification

**Requirements**:
- [ ] `python -m pytest tests/ -x -q` → 661+ passed
- [ ] `grep -rn "unittest.mock" aeryn_core/ apps/ --include="*.py"` → 0 results
- [ ] `grep -rn "TODO\|FIXME\|NotImplemented" aeryn_core/ apps/ --include="*.py"` → 0 results (in new code)
- [ ] All endpoints return 200 or appropriate error codes

### Gate 4: Documentation Updated

**Requirements**:
- [ ] README.md updated with new features
- [ ] CHANGELOG.md has new version entry
- [ ] RELEASE file bumped
- [ ] New docs files created as needed

### Gate 5: Push & Deploy

**Requirements**:
- [ ] All changes committed
- [ ] Pushed to `origin/main`
- [ ] Version tag created if new sprint

---

## 📋 Templates

### Sprint Planning Template

```markdown
## Sprint X Plan (VYY.Z — Weeks A-B)

### Goals
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

### Files to Create/Modify
| # | File | Action | Lines |
|---|------|--------|-------|
| 1 | path/to/file | Create | ~100 |

### Implementation Order
1. ...

### Success Criteria
- [ ] 661 tests pass
- [ ] No test doubles
- [ ] All endpoints 200
- [ ] Docs updated
```

### Test Verification Template

```bash
# Run tests
python -m pytest tests/ -x -q

# Check for test doubles
grep -rn "unittest.mock" aeryn_core/ apps/ --include="*.py"

# Check for placeholders
grep -rn "return 0\|return False\|NotImplemented" aeryn_core/ apps/ --include="*.py" | grep -v "raise NotImplementedError" | grep -v "valid"

# Verify endpoints
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3010/health
```

### Commit Message Template

```
Sprint X: [brief description]

- Implemented feature A
- Fixed issue B
- Updated documentation

Tests: 661 passed
```

---

## 📊 Sprint Tracking

| Sprint | Status | Tests | Docs | Push |
|--------|--------|-------|------|------|
| Sprint 0 | ✅ Complete | 661 | 2 docs | ✅ Pushed |
| Sprint 1 | ✅ Complete | 661 | 7 docs | ✅ Pushed |
| Sprint 2 | ✅ Complete | 661 | 4 docs | ✅ Pushed |
| Sprint 3 | In Progress | — | — | — |
| Sprint 4 | Pending | — | — | — |

---

*Pipeline v59.0 — updated 2026-08-30*
