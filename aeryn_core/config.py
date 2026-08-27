"""V39.60 — Centralized configuration for Aeryn."""

import os

# Base paths
BASE_DIR = os.path.expanduser("~/aeryn-core-agent")
VAULT_DIR = os.path.join(BASE_DIR, "Personalisasi", "Vault")
DATABASE_DIR = os.path.join(BASE_DIR, "Personalisasi", "Database")
TRAINING_DIR = os.path.join(DATABASE_DIR, "training")

# Vault layers
VAULT_LAYERS = ["Raw", "Wiki", "Projects", "System", "Daily", "Skills"]

# Safety
MAX_GOAL_CHARS = 4000
MAX_SESSION_ID_CHARS = 64
MAX_FAKTA_PER_ORANG = 50

# Rate limiting
RATE_LIMIT_MAX = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Circuit breaker
CB_MAX_FAILURES = 3
CB_BASE_WAIT = 1.0
CB_MAX_WAIT = 60

# Search
SEARCH_LIMIT = 10
SEARCH_CACHE_TTL = 30  # seconds

# Sensitive files (never read/write)
SECRET_BASENAMES = {
    ".env", ".env.local", ".env.production",
    "core_memory.json", "social.json",
    "parity_ledger.json", "hermes_hands_usage.json",
    "auth.json", "credentials.json",
}

# System directories (read-only)
SYSTEM_DIRS = ["/etc", "/sys", "/proc", "/dev"]

# Home config directories (protected)
HOME = os.path.expanduser("~")
PROTECTED_DIRS = [
    os.path.join(HOME, ".ssh"),
    os.path.join(HOME, ".gnupg"),
    os.path.join(HOME, ".hermes"),
]


def get_db_path(name: str) -> str:
    """Get path to a database file."""
    return os.path.join(DATABASE_DIR, f"{name}.db")


def get_vault_path(layer: str, filename: str = None) -> str:
    """Get path to vault directory or file."""
    base = os.path.join(VAULT_DIR, layer)
    if filename:
        return os.path.join(base, filename)
    return base


def ensure_dirs():
    """Create all required directories."""
    for d in [VAULT_DIR, DATABASE_DIR, TRAINING_DIR]:
        os.makedirs(d, exist_ok=True)
    for layer in VAULT_LAYERS:
        os.makedirs(os.path.join(VAULT_DIR, layer), exist_ok=True)
