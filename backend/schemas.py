from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Intent(StrEnum):
    refund = "refund"
    cancel = "cancel"
    status = "status"
    replace = "replace"
    address = "address"
    credit = "credit"
    clarify = "clarify"

class Understanding(Strict):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    explanation: str = Field(max_length=500)

class CaseRequest(Strict):
    message: str = Field(min_length=1, max_length=8000)
    target_id: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, min_length=8, max_length=300)
    request_key: str = Field(min_length=8, max_length=100)

class DecisionRequest(Strict):
    decision: str = Field(pattern="^(approve|reject|modify)$")
    amount_cents: int | None = Field(default=None, gt=0)
    note: str = Field(default="", max_length=1000)

class LookupRequest(Strict):
    id: str

class PolicyLookup(Strict):
    query: str
    k: int = Field(default=3, ge=1, le=10)

class RefundRequest(Strict):
    payment_id: str
    amount_cents: int = Field(gt=0)
    reason: str
    idempotency_key: str

class MutationRequest(Strict):
    case_id: str

class Plan(Strict):
    action: Intent
    target_id: str
    amount_cents: int = Field(default=0, ge=0)
    address: str | None = None
    policy_version: str = "2026-01"

class CaseView(Strict):
    id: str
    customer_id: str
    message: str
    target_id: str | None
    state: str
    plan: dict
    evidence: dict
    result: dict
    created_at: str
    shadow: bool
