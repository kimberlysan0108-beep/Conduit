from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, JSON, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    account_age_days: Mapped[int] = mapped_column(default=100)

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    currency: Mapped[str] = mapped_column(default="usd")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(default="active")
    plan: Mapped[str] = mapped_column(default="standard")
    cancelled_at: Mapped[str | None]

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount_cents > 0"), CheckConstraint("refunded_cents >= 0 AND refunded_cents <= amount_cents"))
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    subscription_id: Mapped[str | None] = mapped_column(ForeignKey("subscriptions.id"))
    amount_cents: Mapped[int]
    refunded_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(default=now)
    status: Mapped[str] = mapped_column(default="succeeded")
    duplicate_of: Mapped[str | None]
    provider_id: Mapped[str | None]

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(default="processing")
    address: Mapped[str] = mapped_column(default="123 College Ave, Berkeley CA")
    amount_cents: Mapped[int] = mapped_column(default=2000)
    missing_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    replaced: Mapped[bool] = mapped_column(Boolean, default=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    sku: Mapped[str]
    quantity: Mapped[int] = mapped_column(default=1)

class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[str]
    tracking: Mapped[str | None]

class Case(Base):
    __tablename__ = "support_cases"
    __table_args__ = (UniqueConstraint("customer_id", "request_key"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    request_key: Mapped[str]
    request_hash: Mapped[str]
    message: Mapped[str]
    target_id: Mapped[str | None]
    address: Mapped[str | None]
    state: Mapped[str] = mapped_column(default="UNDERSTAND")
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(default=now)
    shadow: Mapped[bool] = mapped_column(Boolean, default=False)

class Action(Base):
    __tablename__ = "agent_actions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"))
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    request_hash: Mapped[str]
    action: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    provider_reference: Mapped[str | None]
    result: Mapped[dict] = mapped_column(JSON, default=dict)

class Refund(Base):
    __tablename__ = "refunds"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"))
    action_id: Mapped[str] = mapped_column(ForeignKey("agent_actions.id"), unique=True)
    amount_cents: Mapped[int]
    provider_reference: Mapped[str | None] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default="succeeded")

class Credit(Base):
    __tablename__ = "credits"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    action_id: Mapped[str] = mapped_column(ForeignKey("agent_actions.id"), unique=True)
    amount_cents: Mapped[int]

class FraudFlag(Base):
    __tablename__ = "fraud_flags"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    score: Mapped[int] = mapped_column(default=0)
    reason: Mapped[str] = mapped_column(default="")

class PolicyException(Base):
    __tablename__ = "policy_exceptions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    target_id: Mapped[str]
    action: Mapped[str]
    max_amount_cents: Mapped[int]
    expires_at: Mapped[str]
    approved_by: Mapped[str]

class ProviderEvent(Base):
    __tablename__ = "provider_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    object_id: Mapped[str]
    event_type: Mapped[str]
    created: Mapped[int]
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="pending")

class Audit(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"))
    timestamp: Mapped[str] = mapped_column(default=now)
    tool_name: Mapped[str]
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float] = mapped_column(default=0)
    authorization: Mapped[str] = mapped_column(default="READ")
    idempotency_key: Mapped[str | None]
    error: Mapped[str | None]

class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey("support_cases.id"))
    plan_hash: Mapped[str]
    actor: Mapped[str]
    role: Mapped[str]
    decision: Mapped[str]
    timestamp: Mapped[str] = mapped_column(default=now)
