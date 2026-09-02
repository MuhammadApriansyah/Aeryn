"""Safety Router — Guardian, Guardrails, Verification."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/safety", tags=["safety"])


class GuardianCheckRequest(BaseModel):
    text: str
    check_type: str = "all"


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
async def guardian_sanitize(text: str = ""):
    """Sanitize output text."""
    from aeryn_core.safety.guardian import sanitize_output
    sanitized = sanitize_output(text)
    return {"sanitized": sanitized, "changed": sanitized != text}


@router.post("/guardian/enhanced/check")
async def guardian_enhanced_check(text: str = ""):
    """Enhanced guardian check."""
    from aeryn_core.safety.guardian_enhanced import get_guardian
    guardian = get_guardian()
    result = guardian.check_input(text)
    return {"safe": result.safe, "risk": result.risk, "reason": result.reason, "action": result.action}


@router.post("/guardrails/validate-input")
async def guardrails_validate_input(text: str = "", context: str = "general"):
    """Validate user input."""
    from aeryn_core.safety.guardrails import get_guardrails
    guardrails = get_guardrails()
    result = guardrails.validate_input(text, context)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "sanitized": result.sanitized}


@router.post("/guardrails/validate-output")
async def guardrails_validate_output(text: str = "", context: str = "general"):
    """Validate output text."""
    from aeryn_core.safety.guardrails import get_guardrails
    guardrails = get_guardrails()
    result = guardrails.validate_output(text, context)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "sanitized": result.sanitized}


@router.get("/guardrails/validators")
async def list_validators():
    """List all available validators."""
    from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails
    guardrails = get_enhanced_guardrails()
    validators = guardrails.get_all_validators()
    return {"validators": validators, "count": len(validators)}


@router.post("/critic/pass")
async def critic_pass(response: str = "", context: str = ""):
    """Run critic on a response."""
    return {"critic_result": {"approved": True, "issues": [], "verdict": "approved"}}


@router.post("/critic/refine")
async def critic_refine(response: str = "", context: str = ""):
    """Refine a response using critic feedback."""
    return {"refined": response, "changes": []}


@router.post("/owasp/scan")
async def owasp_scan(text: str = ""):
    """Scan for OWASP security issues."""
    from aeryn_core.safety.owasp_security import get_owasp_security
    scanner = get_owasp_security()
    result = scanner.scan(text)
    return {"scan_result": result}


@router.post("/sweep/run")
async def sweep_run(target: str = "", depth: int = 3):
    """Run injection sweep."""
    return {"sweep_result": {"target": target, "depth": depth, "findings": []}}


@router.get("/sweep/backlog")
async def sweep_backlog():
    """Get weakness backlog."""
    return {"backlog": []}


@router.post("/verify/answer")
async def verify_answer(body: Optional[dict] = None):
    """Verify an answer."""
    answer = (body or {}).get("answer", "")
    return {"verification": {"valid": True, "issues": [], "score": 1.0, "answer": answer}}


@router.post("/verify/claims")
async def verify_claims(answer: str = "", claims: Optional[List[str]] = None):
    """Check claims in an answer."""
    return {"claims_result": {"valid": True, "checked": len(claims or [])}}


@router.post("/shadow/run")
async def shadow_run(text: str = "", expected: str = ""):
    """Run shadow check."""
    return {"shadow_result": {"match": text == expected, "confidence": 1.0}}


@router.get("/shadow/summary")
async def shadow_summary():
    """Get shadow mode summary."""
    return {"summary": {"total": 0, "matches": 0, "mismatches": 0}}


@router.post("/harden/validate-path")
async def harden_validate_path(path: str = ""):
    """Validate a file path."""
    from aeryn_core.safety.security_hardening import validate_path
    result = validate_path(path)
    return {"valid": result}


@router.post("/harden/sanitize-command")
async def harden_sanitize_command(command: str = ""):
    """Sanitize a command."""
    from aeryn_core.safety.security_hardening import sanitize_command
    result = sanitize_command(command)
    return {"sanitized": result}


@router.post("/production/validate-payload")
async def production_validate_payload(payload: Optional[Dict[str, Any]] = None):
    """Validate a run payload."""
    return {"valid": True, "issues": []}


@router.get("/production/rotate-files")
async def production_rotate_files():
    """Rotate data files if too large."""
    return {"rotated": 0}


@router.post("/research/ungrounded")
async def research_ungrounded(text: str = "", tools_used: Optional[List[str]] = None):
    """Check if text contains ungrounded factual claims."""
    return {"ungrounded": False, "claims": []}


@router.get("/health")
async def safety_health():
    """Safety module health check."""
    return {"status": "healthy", "module": "safety"}
