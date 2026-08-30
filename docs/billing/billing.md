# Billing & Pricing Documentation

> **Purpose**: Document Aeryn's billing system, API key management, and usage metering.
> **Rule**: All billing code is REAL — no test doubles. Tests verify real billing logic.

---

## 🏗️ Billing System Overview

### Components

| Module | File | Purpose |
|--------|------|---------|
| `billing.py` | `aeryn_core/billing/billing.py` | Subscription plans, pricing, billing logic |
| `usage_metering.py` | `aeryn_core/billing/usage_metering.py` | Token usage tracking and stats |
| `api_keys.py` | `aeryn_core/auth/api_keys.py` | API key generation and validation |
| `auth.py` | `aeryn_core/auth/auth.py` | Token authentication and validation |

### Architecture

```
User → API Key → Auth Validation → Rate Limiter → Usage Metering → Billing Check → Feature Access
```

### Database

All billing data stored in SQLite (`Personalisasi/Database/`):
- `api_keys.db` — API key storage (hashed)
- `billing.db` — Subscription data
- `usage.db` — Token usage logs

---

## 💰 Pricing Tiers

### Free Tier

| Limit | Value |
|-------|-------|
| Requests/day | 100 |
| Tokens/month | 1,000,000 |
| Concurrent sessions | 1 |
| API keys | 2 |

### Pro Tier ($9/month)

| Limit | Value |
|-------|-------|
| Requests/day | Unlimited |
| Tokens/month | 10,000,000 |
| Concurrent sessions | 10 |
| API keys | 10 |
| Support | Priority |

### Enterprise Tier ($49/month)

| Limit | Value |
|-------|-------|
| Requests/day | Unlimited |
| Tokens/month | 100,000,000 |
| Concurrent sessions | Unlimited |
| API keys | Unlimited |
| Support | 24/7 Dedicated |

---

## 🔑 API Key Management

### Generate API Key

```python
from aeryn_core.auth.api_keys import get_api_key_manager

manager = get_api_key_manager()
key = manager.create_key(
    user_id="user123",
    name="Production Key",
    plan="pro"  # or "free", "enterprise"
)
# Returns: {"key": "ak_live_xxxxxx", "hashed": "xxxx", "created_at": "..."}
```

### Validate API Key

```python
from aeryn_core.auth.api_keys import get_api_key_manager

manager = get_api_key_manager()
key_data = manager.validate_key("ak_live_xxxxxx")
# Returns: {"id": ..., "user_id": ..., "plan": ..., "created_at": ...} or None
```

### List Keys

```python
keys = manager.list_keys("user123")
```

### Revoke Key

```python
manager.revoke_key("ak_live_xxxxxx")
```

---

## 📊 Usage Metering

### Record Usage

```python
from aeryn_core.billing.usage_metering import get_usage_metering

meter = get_usage_metering()
meter.record_usage(
    user_id="user123",
    tokens_used=1500,
    endpoint="/chat"
)
```

### Get Usage Stats

```python
stats = meter.get_usage_stats("user123")
# Returns: {"total_tokens": 45000, "daily_tokens": [...], "monthly_tokens": [...], "limits": {...}}
```

### Check Limits

```python
can_proceed = meter.check_limits("user123", tokens=1500)
# Returns: True/False
```

---

## 🧾 Billing API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/billing/plans` | GET | List available plans | API Key |
| `/billing/subscription` | GET | Get current subscription | API Key |
| `/billing/upgrade` | POST | Upgrade subscription | API Key |
| `/billing/usage` | GET | Get usage statistics | API Key |
| `/billing/limits` | GET | Check if within limits | API Key |

---

## 💳 API Key API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/keys` | GET | List all API keys | Token |
| `/api/keys/create` | POST | Create new API key | Token |
| `/api/keys/revoke` | POST | Revoke an API key | Token |

---

## 🧪 Testing Billing Logic

All billing tests use real logic — no mocks.

```bash
# Run billing tests
python -m pytest tests/test_billing.py -x -q

# Run auth tests
python -m pytest tests/test_auth.py -x -q
```

### Test Coverage

| Test File | Tests | What's Covered |
|-----------|-------|----------------|
| `tests/test_auth.py` | 45 | Token validation, API key crud |
| `tests/test_billing.py` | 15 | Plan limits, upgrade/downgrade |
| `tests/test_api_keys.py` | 30 | Key generation, validation, revocation |
| `tests/test_usage_metering.py` | 25 | Usage recording, limit checking |

---

## ⚠️ Compliance Notes

- All billing data encrypted at rest (SQLite with SQLCipher)
- PCI DSS compliant — no card data stored directly
- GDPR compliant — usage data retained for 365 days then auto-deleted
- SOC 2 Type II — audit logs for all billing events
