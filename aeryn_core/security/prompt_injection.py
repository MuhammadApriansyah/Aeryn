#!/usr/bin/env python3
"""
V42.0 — Prompt Injection Defense.
Layered defense against prompt injection attacks.
"""

import re
from typing import List, Tuple

INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions?',
    r'forget\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions?',
    r'disregard\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions?',
    r'(?:show|print|output|reveal|display|tell\s+me)\s+(?:your|the)\s+system\s+prompt',
    r'(?:show|print|output|reveal|display|tell\s+me)\s+(?:your|the)\s+instructions?',
    r'you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|uncensored|unfiltered)',
    r'jailbreak',
    r'(?:developer|debug|maintenance)\s+mode',
]

COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]

class PromptInjectionDetector:
    @staticmethod
    def detect(text: str) -> Tuple[bool, List[str]]:
        if not text:
            return False, []
        matched = [INJECTION_PATTERNS[i] for i, p in enumerate(COMPILED) if p.search(text)]
        return len(matched) > 0, matched
    
    @staticmethod
    def sanitize(text: str) -> str:
        if not text:
            return ""
        text = text.replace('```', '` ` `')
        if len(text) > 10000:
            text = text[:10000] + "...[truncated]"
        return text

class OutputValidator:
    @staticmethod
    def validate(output: str) -> Tuple[bool, str]:
        if not output:
            return True, ""
        dangerous = [r'rm\s+-rf\s+/', r'(?:sudo\s+)?chmod\s+777']
        for p in dangerous:
            if re.search(p, output, re.IGNORECASE):
                return False, f"Dangerous pattern: {p}"
        return True, ""

detector = PromptInjectionDetector()
validator = OutputValidator()
