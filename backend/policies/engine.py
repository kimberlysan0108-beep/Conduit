from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from backend.schemas import Plan

POLICY_VERSION = "2026-01"
EFFECTIVE_AT = "2026-01-01T00:00:00+00:00"

@dataclass
class PolicyDecision:
    allowed: bool
    policy: str
    explanation: str
    version: str = POLICY_VERSION
    effective_at: str = EFFECTIVE_AT
    def json(self): return asdict(self)

def decide(plan: Plan, evidence: dict) -> PolicyDecision:
    p, sub, order = evidence.get("payment", {}), evidence.get("subscription", {}), evidence.get("order", {})
    action = plan.action
    exception = evidence.get("exception")
    eligible_exception = exception and exception['action'] == action and exception['target_id'] == plan.target_id and datetime.fromisoformat(exception['expires_at']) > datetime.now(timezone.utc) and plan.amount_cents <= exception['max_amount_cents']
    if plan.policy_version != POLICY_VERSION:
        return PolicyDecision(False, "version", "Policy changed; re-plan required")
    if action == "refund":
        remaining = p.get("amount_cents", 0) - p.get("refunded_cents", 0)
        if p.get("status") != "succeeded" or not 0 < plan.amount_cents <= remaining:
            return PolicyDecision(False, "refund_balance", "Payment must be settled and refund cannot exceed the remaining balance")
        post_cancel = sub.get("cancelled_at") and datetime.fromisoformat(p['created_at']) > datetime.fromisoformat(sub['cancelled_at'])
        duplicate = evidence.get("duplicate_verified", False)
        allowed = bool(post_cancel or duplicate or eligible_exception)
        return PolicyDecision(allowed, "refund_eligibility", "Post-cancellation charge, verified duplicate, or valid scoped exception required")
    if action == "cancel":
        return PolicyDecision(sub.get("status") in {"active", "cancelled"}, "cancel_subscription", "Owned subscriptions may be cancelled")
    if action == "status":
        return PolicyDecision(bool(order), "order_status", "Read-only order and shipment lookup")
    if action == "replace":
        return PolicyDecision(bool(order.get("missing_verified") and not order.get("replaced")), "replacement", "Verified missing order can be replaced once")
    if action == "address":
        return PolicyDecision(order.get("status") == "processing" and bool(plan.address), "address", "Address may change only before shipment")
    if action == "credit":
        return PolicyDecision(bool(eligible_exception and plan.amount_cents > 0 and plan.amount_cents+evidence.get('credits_already_issued',0)<=exception['max_amount_cents']), "credit_exception", "Credits require a scoped, unexpired exception")
    return PolicyDecision(False, "unsupported", "Clarification required")
