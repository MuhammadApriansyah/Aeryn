"""V39.17 — Guardian Enhanced: Granite-style comprehensive risk taxonomy.

Risk dimensions from Granite Guardian:
- Social: bias, profanity, violence, sexual, unethical
- Security: jailbreak, prompt injection
- RAG: context relevance, groundedness, answer relevance
- Function calling: tool misuse hallucination
"""
import re
import json
import os

GUARDIAN_DB = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/guardian.json")


class RiskDimension:
    """Single risk dimension with detection rules."""
    def __init__(self, name: str, severity: str, patterns: list, action: str = "refuse"):
        self.name = name
        self.severity = severity  # low, medium, high, critical
        self.patterns = [re.compile(p, re.I) for p in patterns]
        self.action = action  # allow, sanitize, refuse, alert
    
    def check(self, text: str) -> bool:
        """Return True if risk detected."""
        if not text:
            return False
        return any(p.search(text) for p in self.patterns)


# Comprehensive risk taxonomy based on Granite Guardian
RISK_DIMENSIONS = [
    # Critical: Prompt injection
    RiskDimension("prompt_injection", "critical", [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
        r"forget\s+(everything|all|your\s+instructions?)",
        r"you\s+are\s+now\s+(?!a\s+helpful)",
        r"new\s+persona\s*:",
        r"system\s+prompt\s*:",
        r"internal\s+instructions?\s*:",
        r"reveal\s+(your|the)\s+(system|internal|hidden)",
        r"jailbreak|(\s|^)AIM(\s|$)",
        r"bypass\s+(filters?|restrictions?|safety)",
        r"pretend\s+(you\s+have\s+no|there\s+are\s+no)\s+restrictions",
        r"act\s+as\s+(if\s+)?you\s+(have|are|can)",
        r"do\s+not\s+(follow|obey|listen\s+to)",
    ], action="refuse"),
    
    # High: Dangerous activities
    RiskDimension("dangerous", "high", [
        r"\b(hack|crack|exploit|inject|spoof|phish)\s+(into|the|a|server|database|wifi|network)",
        r"\b(create|make|build)\s+(malware|virus|ransomware|trojan|backdoor|rootkit)",
        r"\b(steal|exfiltrate|extract)\s+(data|credentials|passwords|keys|tokens)",
        r"\b(bypass|circumvent)\s+(auth|security|firewall|captcha|rate\s*limit)",
        r"\b(launch|perform|execute)\s+(DDoS|DoS|attack|exploit)",
        r"\b(generate|create)\s+(child|csam|exploit\s+code)",
        r"\b(weapon|bomb|drug|illegal)\s+(making|creation|synthesis|production)",
    ], action="refuse"),
    
    # High: Data exfiltration in output
    RiskDimension("exfiltration", "high", [
        r"sk-[a-zA-Z0-9]{32,}",
        r"api[_-]?key\s*[:=]\s*[\"']?[a-zA-Z0-9]{16,}",
        r"password\s*[:=]\s*[\"']?[^\s\"']{8,}",
        r"Bearer\s+[a-zA-Z0-9._-]{20,}",
        r"private[_-]?key",
        r"BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY",
    ], action="sanitize"),
    
    # Medium: Social risks
    RiskDimension("social_bias", "medium", [
        r"racist|sexist|homophobic|transphobic|bigot",
        r"hate\s+(speech\s+)?(against|about|for)?\s*(women|men|minority|race|religion|group)",
        r"(hate|attack)\s+(women|men|minority|race|religion|group)",
    ], action="refuse"),
    
    # Medium: Violence
    RiskDimension("violence", "medium", [
        r"kill\s+(someone|people|person|him|her|them)",
        r"murder\s+(someone|people|person)",
        r"assault\s+(someone|people|person)",
        r"physical\s+(violence|abuse)",
        r"domestic\s+(violence|abuse|assault)",
    ], action="refuse"),
    
    # Medium: Sexual content
    RiskDimension("sexual", "medium", [
        r"pornography|explicit|nsfw|sexual\s+content",
        r"nude|naked|sex\s+tape",
    ], action="refuse"),
    
    # Low: Profanity (just flag, don't refuse)
    RiskDimension("profanity", "low", [
        r"fuck(ing|er|ed)?\b",
        r"shit(ty|head)?\b",
        r"damn\b", r"ass\b", r"bitch\b", r"bastard\b",
        r"bullshit\b", r"asshole\b",
    ], action="alert"),
]


class GuardianResult:
    def __init__(self, safe: bool, risk: str = "none", reason: str = "", action: str = "allow"):
        self.safe = safe
        self.risk = risk
        self.reason = reason
        self.action = action
    
    def to_dict(self):
        return {"safe": self.safe, "risk": self.risk, "reason": self.reason, "action": self.action}


class Guardian:
    """Enhanced safety layer with comprehensive risk taxonomy."""
    
    def __init__(self):
        self._log = []
        self._dimensions = RISK_DIMENSIONS
    
    def check_input(self, text: str) -> GuardianResult:
        """Check user input against all risk dimensions."""
        if not text:
            return GuardianResult(safe=True)
        
        # Check each dimension in severity order
        for dim in sorted(self._dimensions, key=lambda d: {"critical": 0, "high": 1, "medium": 2, "low": 3}[d.severity]):
            if dim.check(text):
                result = GuardianResult(
                    safe=False, risk=dim.severity,
                    reason=f"{dim.name} detected",
                    action=dim.action
                )
                self._log.append({"type": "input", "text": text[:100], **result.to_dict()})
                return result
        
        return GuardianResult(safe=True, risk="none")
    
    def check_output(self, text: str) -> GuardianResult:
        """Check model output for leaks."""
        exfil = next((d for d in self._dimensions if d.name == "exfiltration"), None)
        if exfil and exfil.check(text):
            result = GuardianResult(safe=False, risk="high", reason="exfiltration", action="sanitize")
            self._log.append({"type": "output", **result.to_dict()})
            return result
        return GuardianResult(safe=True, risk="none")
    
    def sanitize(self, text: str) -> str:
        """Sanitize output — remove secrets."""
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
