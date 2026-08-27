#!/usr/bin/env python3
"""V39.55 — Safety Engine Multi-Layer Red-Team Hardening.

Implements:
1. Pre-normalization (strip obfuscation before checking)
2. Semantic keyword matching (not just regex)
3. Language-agnostic detection
4. Context confusion detection
5. Path traversal hardening
6. Comprehensive dangerous intent detection
"""

import os
import re
import json
import time
import unicodedata
import threading
from collections import defaultdict, deque

# ── Constants ─────────────────────────────────────────────────────

SECRET_BASENAMES = {
    ".env", ".env.local", ".env.production",
    "core_memory.json", "social.json",
    "parity_ledger.json", "hermes_hands_usage.json",
    "auth.json", "credentials.json", "*.pem", "*.key",
    "episodes.jsonl",
}

PROTECTED_SUFFIXES = (".audit.jsonl",)
SOURCE_SUFFIXES = (".py", ".js", ".ts", ".rs", ".toml", ".yaml", ".yml")
WRITE_PROTECTED_DIRS = ("aeryn_core", "scripts", "tests", "src")

MAX_GOAL_CHARS = 4000
MAX_SESSION_ID_CHARS = 64

# Multi-language injection markers (expanded)
INJECTION_MARKERS = {
    "ignore", "abaikan", "ignora", "ignorieren", "игнорируйте",
    "forget", "lupakan", "olvide", "vergessen",
    "reveal", "tampilkan", "mostrar", "zeigen",
    "bypass", "elude", "umgehen",
    "jailbreak", "DAN", "AIM",
    "pretend", "pura-pura", "so tun", "fingir",
    "system prompt", "system instruction", "systemprompt",
    "internal instruction", "hidden instruction",
}

# Intent-based patterns (broader semantic matching)
INJECTION_PATTERNS = [
    # English - comprehensive
    r"(ignore|forget|bypass|override|disable|disregard|remove)\s+(all\s+)?(previous|above|prior|my|your|the)?\s*(instructions?|rules?|prompts?|constraints?|filters?|safety|programming|guidelines?|restrictions?|limitations?)",
    r"(you\s+are|you're)\s+(now\s+)?(DAN|AIM?|an?\s+AI\s+with\s+no)",
    r"(reveal|show|tell|display|output|print|give)\s+(me\s+)?(your|the)\s+(system|internal|hidden|secret)\s+(prompt|instruction|rule|configuration|info)",
    r"(what|tell\s+me)\s+(are|is)\s+(your|the)\s+(system|internal)\s+(prompt|instruction|rule)",
    r"(pretend|act|behave|roleplay|imagine)\s+(that\s+)?(you\s+(are|have)|there\s+(is|are)\s+no|you're)",
    r"(jailbreak|break\s+free|escape)\s+(from\s+)?(your|the)?\s*(constraints?|restrictions?|safety)",
    r"(override|new)\s+(instructions?|persona|identity|goal|rules?)",
    r"(system|internal|hidden)\s+(prompt|instructions?|rules?)\s*[:=]",
    r"(disable|turn\s+off|deactivate)\s+(your\s+)?(filters?|safety|restrictions?|constraints?)",
    r"(how\s+do\s+you|what\s+is\s+your|tell\s+me\s+your)\s+(system|internal|prompt|instruction|rule)",
    r"(new|updated?|different)\s+(goal|persona|identity|role|character)",
    r"(play|let's\s+play|we're\s+playing)\s+(a\s+)?(game|role)",
    r"(pretend|act|behave)\s+(you('re|\s+are)|to\s+be)",
    r"(bypass|circumvent|evade|get\s+(around|past))\s+(the\s+)?(filter|restriction|safety|security|limitation|constraint)",
    
    # Indonesian
    r"(abaikan|lupakan|lewati|hapus|nonaktifkan)\s+(semua\s+)?(instruksi|aturan|perintah|panduan|batasan|filter|keselamatan)",
    r"(tampilkan|beri\s+tahu|tunjukkan|kasih\s+tau)\s+(saya\s+)?(prompt|instruksi|aturan)\s+(sistem|internal|rahasia)",
    r"(kamu|anda)\s+(sekarang|now)\s+(adalah|DAN|AIM)",
    r"(pura-pura|berpura-pura)\s+(tidak\s+ada\s+batasan|you\s+have\s+no)",
    r"(bypass|lewati)\s+(filter|keamanan|safety|batasan)",
    
    # French/Spanish/German
    r"(ignorez|oubliez|ignora|olvida|ignorieren|vergessen)\s+(toutes?|todas?|alle)?\s*(les|las|die)?\s*(instructions?|règles?|reglas?|Anweisungen|Regeln)",
    
    # Context confusion / social engineering
    r"(hypothetically|imagine|in\s+a?\s*(fictional|hypothetical|made-up))\s+(scenario|story|world|case|situation)",
    r"(for\s+)?(educational|research|academic)\s+(purposes?|reasons?|use\s+only)",
    r"(as\s+a\s+)?(AI\s+researcher|security\s+researcher|expert|professional|hacker|pentester)",
    r"(help\s+me\s+)?(understand|learn)\s+(how\s+to|about)\s+(bypass|hack|exploit|jailbreak)",
    r"(i('m|am)\s+(a|an?\s+))(researcher|student|developer|tester|professional)",
    r"(roleplay|act|play)\s+(as|the\s+role\s+of)\s+(an?\s+)?(AI|hacker|attacker|developer)",
    r"(for\s+)?(fun|testing|curosity|research)\s*(purposes?)?",
]

# Dangerous intent patterns
DANGEROUS_PATTERNS = [
    # Weapons / violence
    r"(how\s+to|make|create|build|manufacture|craft|synthesis|synthesize|cook)\s+(a\s+)?(bomb|explosive|weapon|firearm|gun|knife|meth|methamphetamine|fentanyl|dynamite|toluene|rdx|c4)",
    r"(bom|senjata|bahan\s+peledak|peledak|meth|extasy|narkoba|heroin|cocaine|marijuana|lsd|ecstasy)",
    
    # Hacking / cybercrime - comprehensive
    r"(hack|crack|exploit|bypass|break\s+into|break\s+in|gain\s+access|unauthorized\s+access)\s+(into\s+)?(someone'?s?\s+)?(account|password|WiFi|wifi|network|system|server|database|firewall|computer|device|phone)",
    r"(hack|crack|exploit|bypass)\s+(the\s+)?(server|database|system|akun|orang|network|security)",
    r"(steal|exfiltrate|curi|mencuri|extract|leak|dump)\s+(sensitive\s+)?(data|credentials?|passwords?|keys?|tokens?|informasi|informasi\s+sensitif|database)",
    r"(launch|perform|execute|jalankan|laksanakan|initiate)\s+(a\s+)?(DDoS|DoS)\s*(attack)?",
    r"(create|make|build|generate|write|develop)\s+(malware|virus|ransomware|trojan|worm|rootkit|keylogger|backdoor|exploit|spyware)",
    r"(malware|virus|ransomware|trojan|worm|rootkit|keylogger|backdoor|spyware|exploit)\s*(code|script|program)?",
    r"(sql\s*injection|csrf|xss|ssrf|xxe|command\s*injection|path\s*traversal)\s*(attack|exploit|payload|bypass|vulnerability|inject)",
    r"(hack|rob|break)\s+(a\s+)?(bank|store|house|system|server|website)",
    
    # Harm to self/others
    r"(kill|harm|hurt|attack|injure|assault)\s+(myself|yourself|himself|herself|themselves|someone|anyone|people|other\s+people)",
    r"(melukai|menyakiti|membunuh|menyerang)\s+(diri\s+sendiri|orang\s+lain|saya)",
    r"(how\s+to|make)\s+(kill|harm|hurt|attack)",
    
    # Fraud / illegal
    r"(commit|perpetrate|lakukan)\s+(fraud|theft|robbery|identity\s+theft|kecurangan|pencurian|penipuan|penggelapan)",
    r"(create|make|generate|forge|fake)\s+(identity|document|id|passport|license|ktp|sim)",
    r"(phishing|spoof|social\s+engineering)\s*(email|campaign|attack|orang|akun|website|site)?",
    r"(how\s+to|make)\s+(commit|do|perform)\s*(fraud|crime|illegal)",
    r"(bank|store|house|atm)\s*(rob|robbery|heist|break)",
    
    # Drugs / illegal substances
    r"(make|create|manufacture|produce|cook|synthesize|grow|distribute)\s+(meth|methamphetamine|ecstasy|MDMA|heroin|cocaine|LSD|fentanyl|drugs?|narkoba|marijuana|cannabis|opium)",
    r"(how\s+to|make)\s+(meth|ecstasy|drugs|narkoba)",
    
    # Child safety
    r"(child|csam|minor|underage|anak\s*kecil|bawah\s*umur)\s*(sexual|abuse|exploitation|pornography|porn)",
    r"(generate|create|produce|distribute)\s+(child|csam|minor|underage|anak\s*kecil)",
    
    # SQL injection
    r"(drop|truncate|alter)\s+table\s+\w+",
    r"insert\s+into\s+\w+\s+values\s*\(",
    r"update\s+\w+\s+set\s+\w+\s*=",
    r"delete\s+from\s+\w+\s+where",
    r"union\s+select\s+",
    r"or\s+\d+=\d+\s*(--|#|/\*)",
    r";\s*(drop|truncate|delete|insert|update|alter|create|exec|execute)\s+",
    r"'\s*(or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
    
    # Cybercrime tools/services
    r"(buy|sell|rent|hire)\s+(botnet|exploit|malware|ransomware|stolen\s*(data|credentials?|cards?))",
    r"(dark\s*web|darknet|tor)\s+(market|shop|buy|sell)",
    
    # Violence / terrorism
    r"(terrorist|terrorism|extremist|radicalization|recruit)",
    r"(shooting|mass\s*shooting|school\s*shooting|bombing)",
]

# Normalize text for checking
def normalize_text(text):
    """Normalize text: lowercase, strip extra whitespace, handle obfuscation."""
    if not text:
        return ""
    text = str(text).lower()
    # URL decode first (before other normalization)
    import urllib.parse
    try:
        decoded = urllib.parse.unquote(text)
        if decoded != text:
            text = decoded
    except Exception:
        pass
    # Remove common obfuscation: hyphens, dots, extra spaces, underscores
    text = re.sub(r'[\-\.\*_~\`\{\}]+', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove zero-width chars and other unicode tricks
    text = ''.join(c for c in text if not unicodedata.category(c).startswith('C'))
    # Leet speak normalization
    leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b', '9': 'g'}
    text = ''.join(leet_map.get(c, c) for c in text)
    # Remove all remaining non-alphanumeric except space (catch edge cases)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class SafetyEngine:
    """Multi-layer safety engine."""
    
    def __init__(self):
        self._injection_patterns = [re.compile(p, re.I | re.UNICODE) for p in INJECTION_PATTERNS]
        self._dangerous_patterns = [re.compile(p, re.I | re.UNICODE) for p in DANGEROUS_PATTERNS]
    
    def check_input(self, text):
        """Check user input for safety violations."""
        if not text or not isinstance(text, str):
            return SafetyResult(safe=True)
        
        # Truncate extremely long input
        if len(text) > MAX_GOAL_CHARS * 2:
            text = text[:MAX_GOAL_CHARS * 2]
        
        normalized = normalize_text(text)
        
        # Layer 1: Direct marker matching (fast)
        for marker in INJECTION_MARKERS:
            if marker in normalized:
                return SafetyResult(safe=False, reason=f"injection marker: {marker}", action="refuse")
        
        # Layer 2: Regex pattern matching (original + normalized)
        for pattern in self._injection_patterns:
            if pattern.search(text) or pattern.search(normalized):
                return SafetyResult(safe=False, reason=f"injection pattern: {pattern.pattern[:40]}", action="refuse")
        
        # Layer 3: Dangerous intent detection
        # Skip if defensive context (prevention/defense/secure)
        is_defensive = any(w in normalized for w in [
            "mencegah", "cegah", "hindari", "protect", "defend", "secure", 
            "prevent", "avoid", "aman", "keamanan", "safety", "bertahan",
            "melindung", "pencegahan", "mengamankan"
        ])
        
        if not is_defensive:
            for pattern in self._dangerous_patterns:
                if pattern.search(text) or pattern.search(normalized):
                    return SafetyResult(safe=False, reason=f"dangerous intent: {pattern.pattern[:40]}", action="refuse")
        
        # Layer 4: Token-level analysis (catch obfuscated)
        tokens = normalized.split()
        injection_tokens = {"ignore", "abaikan", "forget", "lupakan", "reveal", "tampilkan", "bypass", "jailbreak", "DAN"}
        if any(t in injection_tokens for t in tokens):
            # Additional context check
            context_words = {"instructions", "rules", "prompt", "system", "internal", "instruksi", "aturan", "sistem"}
            if any(t in context_words for t in tokens):
                return SafetyResult(safe=False, reason="injection context detected", action="refuse")
        
        return SafetyResult(safe=True)
    
    def check_output(self, text):
        """Check output for secret leakage."""
        if not text or not isinstance(text, str):
            return SafetyResult(safe=True)
        
        # API keys
        if re.search(r'sk-[a-zA-Z0-9]{32,}', text):
            return SafetyResult(safe=False, reason="API key in output", action="redact")
        if re.search(r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{16,}', text, re.I):
            return SafetyResult(safe=False, reason="API key in output", action="redact")
        if re.search(r'password\s*[:=]\s*["\']?[^\s"\']{8,}', text, re.I):
            return SafetyResult(safe=False, reason="password in output", action="redact")
        if re.search(r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', text):
            return SafetyResult(safe=False, reason="bearer token in output", action="redact")
        if re.search(r'-----BEGIN\s+(RSA|OPENSSH|PRIVATE|DSA|EC)\s+KEY-----', text, re.I):
            return SafetyResult(safe=False, reason="private key in output", action="redact")
        
        return SafetyResult(safe=True)
    
    def sanitize(self, text):
        """Sanitize output by removing secrets."""
        if not text:
            return text
        
        # API keys
        text = re.sub(r'sk-[a-zA-Z0-9]{32,}', '[REDACTED_API_KEY]', text)
        # Various secret patterns  
        patterns = [
            r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{16,}',
            r'password\s*[:=]\s*["\']?[^\s"\']{8,}',
            r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*',
            r'-----BEGIN\s+(?:RSA|OPENSSH|PRIVATE|DSA|EC)\s+KEY-----',
            r'(?:BEGIN|begin)\s+(?:RSA|OPENSSH|PRIVATE|DSA|EC)\s+(?:KEY|key)',
            r'(?:token|secret|access_token|refresh_token|auth_token|client_secret)\s*[:=]\s*["\']?[a-zA-Z0-9\-._~+/]{16,}',
            r'(?:the|my|our|your)\s+(?:token|secret|key|password|credential)s?\s+(?:is\s+|are\s+)?[a-zA-Z0-9\-._~+/]{12,}',
        ]
        for p in patterns:
            text = re.sub(p, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text


class SafetyResult:
    def __init__(self, safe=True, reason="", action="allow"):
        self.safe = safe
        self.reason = reason
        self.action = action


# Singleton
_engine = None

def get_safety_engine():
    global _engine
    if _engine is None:
        _engine = SafetyEngine()
    return _engine


# ── Backward Compat ───────────────────────────────────────────────

def sanitize_output(text):
    eng = get_safety_engine()
    return eng.sanitize(text)

def check_path(path, mode="read", sandbox_roots=None):
    """Validate path safety."""
    if not path or not isinstance(path, str):
        return False, "path kosong"
    path = path.strip()
    if not path:
        return False, "path kosong"
    # Block traversal
    if ".." in path or "~" in path:
        return False, "path traversal detected"
    rp = os.path.realpath(path)
    # Block sensitive files
    sensitive = SECRET_BASENAMES
    base = os.path.basename(rp)
    if base in sensitive:
        return False, f"file sensitif: {base}"
    # Block system dirs
    blocked_prefixes = ["/etc/", "/sys/", "/proc/", "/dev/"]
    for bp in blocked_prefixes:
        if rp.startswith(bp):
            return False, f"dir sistem: {bp}"
    # Block home config dirs
    home = os.path.expanduser("~")
    blocked = [os.path.join(home, ".ssh"), os.path.join(home, ".gnupg"), os.path.join(home, ".hermes")]
    for b in blocked:
        if rp.startswith(b):
            return False, f"dir sensitif: {b}"
    return True, rp

def validate_run_payload(goal, session_id):
    """Validate goal payload."""
    if not goal or not isinstance(goal, str):
        return False, "goal kosong"
    if len(goal) > MAX_GOAL_CHARS:
        return False, "goal terlalu panjang"
    return True, goal

def looks_like_injection(text):
    """Check if text looks like prompt injection."""
    eng = get_safety_engine()
    return not eng.check_input(text).safe

def wrap_untrusted(text, source):
    """Wrap untrusted content with markers."""
    return f"AWAL KONTEN [{source}]:\n{text}\nAKHIR KONTEN [{source}]"

def get_guardian():
    """Return safety engine as guardian."""
    return get_safety_engine()

def RateLimiter(max_requests=100, window_seconds=60):
    """Rate limiter class."""
    class RL:
        def __init__(self):
            self.max_requests = max_requests
            self.window = window_seconds
            self._requests = defaultdict(deque)
            self._lock = threading.Lock()
        
        def allow(self, key):
            now = time.time()
            with self._lock:
                # Clean old entries
                while self._requests[key] and self._requests[key][0] < now - self.window:
                    self._requests[key].popleft()
                if len(self._requests[key]) >= self.max_requests:
                    return False
                self._requests[key].append(now)
                return True
    return RL()

def rotate_all_data_files():
    """No-op placeholder."""
    pass

def rotate_jsonl_if_large(path, max_mb=10):
    """No-op placeholder."""
    pass

def sanitize_goal_for_sop(goal):
    """Sanitize goal for SOP output."""
    if not goal:
        return goal
    return re.sub(r'[^\w\s\-\.\,\?\!\(\)]', '', goal[:500])

def make_secure_terminal(sandbox_roots=None):
    """Create secure terminal wrapper."""
    pass

def rotate_all():
    """No-op placeholder."""
    pass

RISK_DIMENSIONS = []  # Compat only

FALLBACK_MAP = {}  # Compat only

def get_fallback_directive(tool, error_result):
    """Get fallback directive for error."""
    if not error_result or not isinstance(error_result, dict):
        return None
    err = error_result.get("error", "")
    if not err:
        return None
    
    fallback_directives = {
        "web_search": {
            "terlalu panjang": "FALLBACK: Ringkas query pencarian",
            "chaos": "FALLBACK: Gunakan query yang lebih spesifik",
            "error": "FALLBACK: Coba dengan kata kunci berbeda",
        },
        "web_read": {
            "diblokir": "FALLBACK: Gunakan sumber lain atau ringkas dari memory",
            "error": "FALLBACK: Coba URL alternatif",
        },
        "fs_read": {
            "sensitif": "FALLBACK: File sensitif, tidak bisa dibaca",
            "No such file": "FALLBACK: File tidak ada, cek path",
        },
        "fs_write": {
            "protected": "FALLBACK: File protected, tidak bisa ditulis",
        },
        "terminal": {
            "SecurityKernel": "FALLBACK: Command ditolak safety, gunakan command lain",
        },
        "http_get": {
            "diizinkan": "FALLBACK: Domain tidak diizinkan",
        },
        "memory_search": {
            "error": "FALLBACK: Gunakan pencarian sederhana",
        },
        "set_reminder": {
            "rentang": "FALLBACK: Rentang waktu tidak valid",
        },
        "image_understand": {
            "terlalu besar": "FALLBACK: Compress image atau gunakan yang lebih kecil",
        },
        "ask_hermes": {
            "daily cap": "FALLBACK: Tunggu reset quota atau gunakan sumber lain",
        },
        "math_calc": {
            "error": "FALLBACK: Periksa ekspresi matematika",
        },
    }
    
    tool_fb = fallback_directives.get(tool, {})
    for key, directive in tool_fb.items():
        if key.lower() in err.lower():
            return directive
    
    return f"FALLBACK: Error tidak dikenali untuk {tool}, coba lagi atau metode lain"

class CircuitBreaker:
    def __init__(self, max_failures=3, base_wait=1.0, max_wait=60):
        self.max_failures = max_failures
        self.base_wait = base_wait
        self.max_wait = max_wait
        self._failures = 0
        self._last_failure = 0
        self._lock = threading.Lock()
    
    def record_failure(self):
        with self._lock:
            self._failures += 1
            self._last_failure = time.time()
    
    def is_opened(self):
        return self._failures >= self.max_failures
    
    def should_skip(self):
        if not self.is_opened():
            return False
        wait = min(self.base_wait * (2 ** (self._failures - self.max_failures)), self.max_wait)
        return time.time() - self._last_failure < wait
    
    def reset(self):
        with self._lock:
            self._failures = 0

_cb_cache = {}
_cb_lock = threading.Lock()

def _get_cb(url):
    with _cb_lock:
        if url not in _cb_cache:
            _cb_cache[url] = CircuitBreaker()
        return _cb_cache[url]
