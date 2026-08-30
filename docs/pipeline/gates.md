# Pipeline Gates

> **Purpose**: Document quality gates that must pass before code is pushed to production.
> **Rule**: Every gate is verified with real testing — no test doubles.

---

## 🚧 Gate 1: Sprint Planning Approval

**Purpose**: Ensure proper planning before implementation begins.

### Requirements Checklist

- [ ] ✅ **Baseline Established**: `python -m pytest tests/ -x -q` → **661 passed**
  ```bash
  cd /home/sen/aeryn-core-agent
  source venv-proot/bin/activate
  python -m pytest tests/ -x -q
  ```

- [ ] ✅ **No Test Doubles**: Production code is clean
  ```bash
  grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py" | wc -l
  # Expected: 0
  ```

- [ ] ✅ **Implementation Plan Documented**: Sprint plan in `docs/`
- [ ] ✅ **Sprint Schedule Defined**: Timeline in `docs/pipeline/phases.md`

### Verification Command
```bash
cd /home/sen/aeryn-core-agent && source venv-proot/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -3
# Must show: "661 passed"
```

---

## 🚧 Gate 2: Implementation Complete

**Purpose**: Ensure all planned features are implemented with real code.

### Requirements Checklist

- [ ] ✅ **Features Implemented**: All planned features in code
- [ ] ✅ **No Test Doubles**: No mocks/stubs in new code
  ```bash
  grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py" | wc -l
  # New changes must show: 0
  ```

- [ ] ✅ **No Placeholder Returns**:
  ```bash
  # Check for return 0 or return False that are actual placeholders (not logic)
  grep -rn "return 0\|return False\|NotImplemented" aeryn_core/ apps/ --include="*.py" | grep -v "raise NotImplementedError" | grep -v "valid" | grep -v "can_handle"
  ```

- [ ] ✅ **Follows Existing Patterns**: Code matches style of nearby code
- [ ] ✅ **No TODO Comments**:
  ```bash
  grep -rn "TODO\|FIXME" aeryn_core/ apps/ --include="*.py" | wc -l
  # Expected: 0 in new code
  ```

---

## 🚧 Gate 3: Test Verification

**Purpose**: Ensure all tests pass with real execution.

### Automated Check Script

```bash
#!/bin/bash
# Save as scripts/qc_verify.sh

set -e

cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate

echo "=== Gate 3: Test Verification ==="

# 1. Full test suite
echo "1. Running full test suite (661 tests)..."
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5

# 2. Check for test doubles
echo "2. Checking for test doubles in production..."
TEST_DOUBLES=$(grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py" | wc -l)
if [ "$TEST_DOUBLES" -gt 0 ]; then
    echo "❌ FAIL: Found $TEST_DOUBLES test double references"
    exit 1
else
    echo "✅ PASS: No test doubles found"
fi

# 3. Verify endpoints
echo "3. Verifying endpoints..."
HEALTH=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3010/health)
if [ "$HEALTH" = "200" ]; then
    echo "✅ PASS: /health returns 200"
else
    echo "❌ FAIL: /health returns $HEALTH"
    exit 1
fi

echo "=== All Gates Passed ==="
```

### Manual Verification

```bash
# Test suite
python -m pytest tests/ -x -q
# Expected: 661 passed

# Test doubles check
grep -rn "unittest.mock\|MagicMock\|@patch" aeryn_core/ apps/ --include="*.py"
# Expected: no output

# Placeholder check
grep -rn "return 0" aeryn_core/ --include="*.py" | grep -v "0.0\|return 0\.\|rc\|status_code\|return 0,"
# Expected: no output

# Endpoint verification
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3010/health
# Expected: 200
```

---

## 🚧 Gate 4: Documentation Updated

**Purpose**: Ensure all documentation is current after changes.

### Requirements Checklist

- [ ] ✅ **README.md**: Version, features, badges updated
- [ ] ✅ **CHANGELOG.md**: New version entry with changes listed
- [ ] ✅ **RELEASE**: Version file bumped (e.g., `echo "V59.1" > RELEASE`)
- [ ] ✅ **New docs**: Any new features documented in `docs/`

### Verification Commands

```bash
# Check version consistency
grep "V59" README.md | head -1  # Should show V59.x
grep "\[59" CHANGELOG.md | head -1  # Should show version entry
cat RELEASE  # Should show current version
```

---

## 🚧 Gate 5: Push & Deploy

**Purpose**: Ensure code is committed and pushed safely.

### Requirements Checklist

- [ ] ✅ **All tests pass**: 661 tests green
- [ ] ✅ **No test doubles**: Verified
- [ ] ✅ **Documentation updated**: README, CHANGELOG, RELEASE
- [ ] ✅ **Changes committed**: `git status` shows clean
- [ ] ✅ **Pushed to main**: `git push origin main` succeeds

### Push Script Template

```bash
# 1. Add files
git add -A

# 2. Commit with proper message
git commit -m "Sprint N: [brief description]

- [list of changes]
- 661 tests pass"

# 3. Push
git push origin main

# 4. Verify
git log --oneline -1  # Should show latest commit
```

---

## 🔧 Gate Automation

### Automated QC Script

```bash
#!/bin/bash
# scripts/qc_all.sh — Run all gates

cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate

echo "=== Quality Control: All Gates ==="

# Gate 1: Tests
echo "--- Gate 1: Tests ---"
python -m pytest tests/ -x -q 2>&1 | tail -1

# Gate 2: No test doubles
echo "--- Gate 2: No Test Doubles ---"
DOUBLES=$(grep -rn "unittest.mock\|MagicMock" aeryn_core/ apps/ --include="*.py" | wc -l)
echo "Test doubles found: $DOUBLES"

# Gate 3: No placeholders
echo "--- Gate 3: No Placeholders ---"
PLACEHOLDERS=$(grep -rn "TODO\|FIXME\|NotImplemented" aeryn_core/ apps/ --include="*.py" | wc -l)
echo "Placeholders found: $PLACEHOLDERS"

# Gate 4: Endpoints
echo "--- Gate 4: Endpoints ---"
for endpoint in /health / /projects /workspaces /chat /plugins /audit /settings; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:3010${endpoint}")
    echo "$endpoint: $CODE"
done

# Gate 5: Documentation
echo "--- Gate 5: Documentation ---"
VERSION=$(cat RELEASE)
echo "RELEASE: $VERSION"
echo "CHANGELOG: $(grep -c "## \[${VERSION#"V"}" CHANGELOG.md) entries"

echo "=== QC Complete ==="
```

---

*Pipeline gates v59.0 — all gates must pass. Updated 2026-08-30.*
