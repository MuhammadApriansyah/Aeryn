"""Safety Router — Guardian, Guardrails, Verification.

Provides API endpoints for:
- Guardian: prompt injection detection, dangerous content, data exfiltration
- Guardrails: input/output validation, PII detection
- Verification: answer verification, claim checking
- Shadow mode: parity checking
- Security hardening: path validation, command sanitization
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/safety", tags=["safety"])


# ========================================
# Guardian — Injection & Dangerous Content Detection
# ========================================

class GuardianCheckRequest(BaseModel):
    text: str
    check_type: str = "all"  # "injection", "dangerous", "exfiltration", "all"


@router.post("/guardian/check")
async def guardian_check(req: GuardianCheckRequest):
    """Check text for safety issues."""
    from aeryn_core.safety.guardian import get_guardian
    
    guardian = get_guardian()
    
    if req.check_type in ("injection", "all"):
        result = guardian.check_input(req.text)
        if not result.safe:
            return {"safe": False, "risk": result.risk, "reason": result.reason, "action": result.action}
    
    if req.check_type in ("dangerous", "all"):
        from aeryn_core.safety.guardian import detect_dangerous
        result = detect_dangerous(req.text)
        if not result.safe:
            return {"safe": False, "risk": result.risk, "reason": result.reason, "action": result.action}
    
    if req.check_type in ("exfiltration", "all"):
        from aeryn_core.safety.guardian import detect_exfiltration
        result = detect_exfiltration(req.text)
        if not result.safe:
            return {"safe": False, "risk": result.risk, "reason": result.reason, "action": result.action}
    
    return {"safe": True, "risk": "none", "action": "allow"}


@router.post("/guardian/sanitize")
async def guardian_sanitize(text: str):
    """Sanitize output text."""
    from aeryn_core.safety.guardian import sanitize_output
    
    sanitized = sanitize_output(text)
    return {"sanitized": sanitized, "changed": sanitized != text}


# ========================================
# Guardian Enhanced — Multi-dimensional Risk
# ========================================

@router.post("/guardian/enhanced/check")
async def guardian_enhanced_check(text: str):
    """Enhanced guardian check with risk dimensions."""
    from aeryn_core.safety.guardian_enhanced import get_guardian
    
    guardian = get_guardian()
    result = guardian.check_input(text)
    
    return {
        "safe": result.safe,
        "risk": result.risk,
        "reason": result.reason,
        "action": result.action,
    }


# ========================================
# Guardrails — Input/Output Validation
# ========================================

class GuardrailRequest(BaseModel):
    text: str
    context: str = "general"


@router.post("/guardrails/validate-input")
async def guardrails_validate_input(req: GuardrailRequest):
    """Validate user input."""
    from aeryn_core.safety.guardrails import get_guardrails
    
    guardrails = get_guardrails()
    result = guardrails.validate_input(req.text, req.context)
    
    return {
        "valid": result.valid,
        "risk": result.risk,
        "issues": result.issues,
        "sanitized": result.sanitized,
    }


@router.post("/guardrails/validate-output")
async def guardrails_validate_output(req: GuardrailRequest):
    """Validate output text."""
    from aeryn_core.safety.guardrails import get_guardrails
    
    guardrails = get_guardrails()
    result = guardrails.validate_output(req.text, req.context)
    
    return {
        "valid": result.valid,
        "risk": result.risk,
        "issues": result.issues,
        "sanitized": result.sanitized,
    }


# ========================================
# Enhanced Guardrails — Validator Registry
# ========================================

@router.get("/guardrails/validators")
async def list_validators():
    """List all available validators."""
    from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails
    
    guardrails = get_enhanced_guardrails()
    validators = guardrails.get_all_validators()
    
    return {"validators": validators, "count": len(validators)}


# ========================================
# Critic — Response Critique
# ========================================

class CriticRequest(BaseModel):
    response: str
    context: str = ""


@router.post("/critic/pass")
async def critic_pass(req: CriticRequest):
    """Run critic on a response."""
    from aeryn_core.safety.critic_pass import make_critic
    
    critic = make_critic()
    result = critic(req.response, req.context)
    
    return {"critic_result": result}


@router.post("/critic/refine")
async def critic_refine(req: CriticRequest):
    """Refine a response using critic feedback."""
    from aeryn_core.safety.critic_refine import run_critic
    
    result = run_critic(req.response, req.context)
    
    return {"refined": result}


# ========================================
# OWASP Security — Agentic Security Scanning
# ========================================

class OWASPRequest(BaseModel):
    text: str
    scan_type: str = "all"


@router.post("/owasp/scan")
async def owasp_scan(req: OWASPRequest):
    """Scan for OWASP security issues."""
    from aeryn_core.safety.owasp_security import get_owasp_security
    
    scanner = get_owasp_security()
    result = scanner.scan(req.text)
    
    return {"scan_result": result}


# ========================================
# Injection Sweep — Vulnerability Scanning
# ========================================

class SweepRequest(BaseModel):
    target: str
    depth: int = 3


@router.post("/sweep/run")
async def sweep_run(req: SweepRequest):
    """Run injection sweep."""
    from aeryn_core.safety.injection_sweep import run_sweep
    
    result = run_sweep(req.target, req.depth)
    
    return {"sweep_result": result}


@router.get("/sweep/backlog")
async def sweep_backlog():
    """Get weakness backlog."""
    from aeryn_core.safety.injection_sweep import weakness_backlog
    
    backlog = weakness_backlog()
    
    return {"backlog": backlog}


# ========================================
# Verification — Answer Verification
# ========================================

class VerifyRequest(BaseModel):
    answer: str
    context: str = ""
    claims: List[str] = []


@router.post("/verify/answer")
async def verify_answer(req: VerifyRequest):
    """Verify an answer."""
    from aeryn_core.safety.verifier import verify_answer
    
    result = verify_answer(req.answer, req.context, req.claims)
    
    return {"verification": result}


@router.post("/verify/claims")
async def verify_claims(req: VerifyRequest):
    """Check claims in an answer."""
    from aeryn_core.safety.verification_gate import check_claims
    
    result = check_claims(req.answer, req.claims)
    
    return {"claims_result": result}


# ========================================
# Shadow Mode — Parity Checking
# ========================================

@router.post("/shadow/run")
async def shadow_run(text: str, expected: str = ""):
    """Run shadow check."""
    from aeryn_core.safety.shadow_mode import ShadowRunner
    
    runner = ShadowRunner()
    result = runner.run_with_shadow(text, expected)
    
    return {"shadow_result": result}


@router.get("/shadow/summary")
async def shadow_summary():
    """Get shadow mode summary."""
    from aeryn_core.safety.shadow_mode import ParityLedger
    
    ledger = ParityLedger()
    summary = ledger.summary()
    
    return {"summary": summary}


# ========================================
# Security Hardening
# ========================================

@router.post("/harden/validate-path")
async def harden_validate_path(path: str):
    """Validate a file path."""
    from aeryn_core.safety.security_hardening import validate_path
    
    result = validate_path(path)
    
    return {"valid": result}


@router.post("/harden/sanitize-command")
async def harden_sanitize_command(command: str):
    """Sanitize a command."""
    from aeryn_core.safety.security_hardening import sanitize_command
    
    result = sanitize_command(command)
    
    return {"sanitized": result}


# ========================================
# Production Guard
# ========================================

@router.post("/production/validate-payload")
async def production_validate_payload(payload: Dict[str, Any]):
    """Validate a run payload."""
    from aeryn_core.safety.production_guard import validate_run_payload
    
    result = validate_run_payload(payload)
    
    return {"valid": result, "issues": result.get("issues", [])}


@router.get("/production/rotate-files")
async def production_rotate_files():
    """Rotate data files if too large."""
    from aeryn_core.safety.production_guard import rotate_all_data_files
    
    result = rotate_all_data_files()
    
    return {"rotated": result}


# ========================================
# Research Guard
# ========================================

@router.post("/research/ungrounded")
async def research_ungrounded(text: str, tools_used: List[str] = []):
    """Check if text contains ungrounded factual claims."""
    from aeryn_core.safety.research_guard import is_ungrounded_factual
    
    result = is_ungrounded_factual(text, tools_used)
    
    return {"ungrounded": result}


# ========================================
# Health
# ========================================

@router.get("/health")
async def safety_health():
    """Safety module health check."""
    return {"status": "healthy", "module": "safety"}
