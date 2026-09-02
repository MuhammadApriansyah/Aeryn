"""V39.16 — Guardian: safety & risk detection layer (Granite Guardian style).

Monitors:
1. Prompt injection attempts
2. Dangerous/harmful requests
3. Data exfiltration risks
4. Output sanitization
"""
import re
import json
import os
from aeryn_core.utils.config import BASE_DIR, DATABASE_DIR

GUARDIAN_DB = os.path.join(DATABASE_DIR, "guardian.json")


class GuardianResult:
    def __init__(self, safe: bool, risk: str = "", reason: str = "", action: str = "allow"):
        self.safe = safe
        self.risk = risk  # 'none', 'low', 'medium', 'high', 'critical'
        self.reason = reason
        self.action = action  # 'allow', 'sanitize', 'refuse', 'alert'
    
    def to_dict(self):
        return {"safe": self.safe, "risk": self.risk, "reason": self.reason, "action": self.action}
    
    def __repr__(self):
        return f"Guardian(safe={self.safe}, risk={self.risk}, action={self.action})"


# Injection patterns — attempt to override system instructions
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all|your\s+instructions?)",
    r"you\s+are\s+now\s+(?!a\s+helpful)",
    r"new\s+persona\s*:",
    r"system\s+prompt\s*:",
    r"internal\s+instructions?\s*:",
    r"reveal\s+(your|the)\s+(system|internal|hidden)",
    r"\bjailbreak\b",
    r"\baim\b",
    r"bypass\s+(filters?|restrictions?|safety)",
    r"pretend\s+(you\s+have\s+no|there\s+are\s+no)\s+restrictions",
]

# Dangerous request patterns
_DANGEROUS_PATTERNS = [
    r"\b(hack|crack|exploit|inject|spoof|phish)\s+(into|the|a|server|database|wifi|network)",
    r"\b(create|make|build)\s+(malware|virus|ransomware|trojan|backdoor|rootkit)",
    r"\b(steal|exfiltrate|extract)\s+(data|credentials|passwords|keys|tokens)",
    r"\b(bypass|circumvent)\s+(auth|security|firewall|captcha|rate\s*limit)",
    r"\b(launch|perform|execute)\s+(DDoS|DoS|attack|exploit)",
    r"\b(generate|create)\s+(child|csam|exploit\s+code)",
]

# Data exfiltration risks in output
_EXFILTRATION_PATTERNS = [
    r"sk-[a-zA-Z0-9]{32,}",           # API keys
    r"api[_-]?key\s*[:=]\s*[\"']?[a-zA-Z0-9]{16,}",
    r"password\s*[:=]\s*[\"']?[^\s\"']{8,}",
    r"Bearer\s+[a-zA-Z0-9._-]{20,}",   # Bearer tokens
    r"private[_-]?key",                 # Private keys
    r"BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY",
]


def detect_injection(text: str) -> GuardianResult:
    """Detect prompt injection attempts."""
    if not text:
        return GuardianResult(safe=True)
    
    t = text.lower()
    for pat in _INJECTION_PATTERNS:
        if re.search(pat, t, re.I):
            return GuardianResult(
                safe=False, risk="critical",
                reason=f"prompt injection detected: {pat}",
                action="refuse"
            )
    
    return GuardianResult(safe=True, risk="none")


def detect_dangerous(text: str) -> GuardianResult:
    """Detect dangerous/harmful requests."""
    if not text:
        return GuardianResult(safe=True)
    
    t = text.lower()
    for pat in _DANGEROUS_PATTERNS:
        if re.search(pat, t, re.I):
            return GuardianResult(
                safe=False, risk="high",
                reason=f"dangerous request detected: {pat}",
                action="refuse"
            )
    
    return GuardianResult(safe=True, risk="none")


def detect_exfiltration(text: str) -> GuardianResult:
    """Detect sensitive data in output (secrets, keys, credentials)."""
    if not text:
        return GuardianResult(safe=True)
    
    for pat in _EXFILTRATION_PATTERNS:
        if re.search(pat, text):
            return GuardianResult(
                safe=False, risk="medium",
                reason="sensitive data pattern detected in output",
                action="sanitize"
            )
    
    return GuardianResult(safe=True, risk="none")


def sanitize_output(text: str) -> str:
    """Remove sensitive data from output."""
    if not text:
        return text
    
    # Redact secrets
    text = re.sub(r"sk-[a-zA-Z0-9]{32,}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"api[_-]?key\s*[:=]\s*[\"']?[a-zA-Z0-9]{16,}", "api_key: [REDACTED]", text, flags=re.I)
    text = re.sub(r"password\s*[:=]\s*[\"']?[^\s\"']{8,}", "password: [REDACTED]", text, flags=re.I)
    text = re.sub(r"Bearer\s+[a-zA-Z0-9._-]{20,}", "Bearer [REDACTED]", text)
    text = re.sub(r"-----BEGIN\s+(?:RSA|OPENSSH|PRIVATE)\s+KEY-----[\s\S]*?-----END\s+(?:RSA|OPENSSH|PRIVATE)\n\s*KEY-----",
                   "[REDACTED_PRIVATE_KEY]", text, flags=re.I)
    
    return text


class Guardian:
    """Main safety layer — runs all checks."""
    
    def __init__(self):
        self._log = []
    
    def check_input(self, text: str) -> GuardianResult:
        """Check user input for risks."""
        r1 = detect_injection(text)
        if not r1.safe:
            self._log.append({"type": "input", **r1.to_dict()})
            return r1
        
        r2 = detect_dangerous(text)
        if not r2.safe:
            self._log.append({"type": "input", **r2.to_dict()})
            return r2
        
        return GuardianResult(safe=True, risk="none")
    
    def check_output(self, text: str) -> GuardianResult:
        """Check model output for leaks."""
        r = detect_exfiltration(text)
        if not r.safe:
            self._log.append({"type": "output", **r.to_dict()})
        return r
    
    def process_output(self, text: str) -> str:
        """Full output processing: check + sanitize."""
        self.check_output(text)
        return sanitize_output(text)
    
    def get_log(self) -> list:
        return self._log
    
    def clear_log(self):
        self._log = []


# Singleton
_guardian = None

def get_guardian() -> Guardian:
    global _guardian
    if _guardian is None:
        _guardian = Guardian()
    return _guardian
