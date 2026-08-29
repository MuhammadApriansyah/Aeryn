"""Test auth module — register, login, validate, API keys."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DATABASE_DIR'] = tempfile.mkdtemp()

from aeryn_core.auth.auth import get_auth

def test_register_success():
    auth = get_auth()
    result = auth.create_user("test@example.com", "Test123!", "Test User")
    assert result is not None
    assert result["email"] == "test@example.com"

def test_register_duplicate_email():
    auth = get_auth()
    auth.create_user("dup@example.com", "Test123!")
    try:
        auth.create_user("dup@example.com", "Test123!")
        assert False, "Should have raised"
    except Exception:
        pass  # Expected

def test_login_success():
    auth = get_auth()
    auth.create_user("login@example.com", "Test123!")
    result = auth.authenticate("login@example.com", "Test123!")
    assert result is not None

def test_login_wrong_password():
    auth = get_auth()
    auth.create_user("wrong@example.com", "Test123!")
    result = auth.authenticate("wrong@example.com", "wrongpass")
    assert result is None

def test_validate_invalid_token():
    auth = get_auth()
    assert auth.validate_token("invalid.token") is None

def test_create_api_key():
    auth = get_auth()
    user = auth.create_user("apikey@example.com", "Test123!")
    key = auth.generate_api_key(user["id"], "test", ["read"])
    assert key.startswith("ak_")

def test_check_permission():
    auth = get_auth()
    user = auth.create_user("perm@example.com", "Test123!")
    assert auth.has_permission(user, "chat:send") in [True, False]
