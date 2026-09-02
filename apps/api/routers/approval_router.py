"""Approval Router — Human-in-the-Loop endpoints for tool approval."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    approval_id: str
    decision: str  # "approve" | "reject"
    edited_args: Optional[Dict[str, Any]] = None
    decided_by: str = "sen"


@router.get("/pending")
async def list_pending():
    """List all pending approval requests."""
    from aeryn_core.safety.guardrail_engine import get_guardrail_engine
    engine = get_guardrail_engine()
    pending = engine.approval_store.pending()
    return {"pending": [req.to_dict() for req in pending], "count": len(pending)}


@router.post("/decide")
async def decide(req: ApprovalDecision):
    """Approve or reject an approval request."""
    from aeryn_core.safety.guardrail_engine import get_guardrail_engine
    engine = get_guardrail_engine()

    if req.decision == "approve":
        result = engine.approve(req.approval_id, req.decided_by, req.edited_args)
    elif req.decision == "reject":
        result = engine.reject(req.approval_id, req.decided_by)
    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")

    return result


@router.get("/policies")
async def list_policies():
    """List all tool guardrail policies."""
    from aeryn_core.safety.guardrail_engine import get_guardrail_engine
    engine = get_guardrail_engine()
    policies = {name: p.to_dict() for name, p in engine.policies.items()}
    return {"policies": policies}


@router.post("/policies/{tool_name}")
async def set_policy(tool_name: str, policy: Dict[str, Any]):
    """Update a tool policy."""
    from aeryn_core.safety.guardrail_engine import get_guardrail_engine, ToolPolicy, RiskLevel
    engine = get_guardrail_engine()

    new_policy = ToolPolicy(
        tool_name=tool_name,
        risk_level=RiskLevel(policy.get("risk_level", "medium")),
        requires_approval=policy.get("requires_approval", False),
        forbidden_patterns=policy.get("forbidden_patterns", []),
        human_description=policy.get("human_description", ""),
    )
    engine.policies[tool_name] = new_policy
    return {"status": "ok", "tool": tool_name, "policy": new_policy.to_dict()}