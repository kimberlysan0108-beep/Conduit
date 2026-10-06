# Brief coverage and explicit boundaries

| Brief requirement | Implementation / evidence | Boundary |
|---|---|---|
| Three business domains | Refunds/credits; cancellation; orders | Upgrade/downgrade and failed-payment recovery excluded |
| Merchant simulator | `models.py`, seed, APIs | Test customers, USD |
| Typed tools/APIs | Pydantic request/plan/intent models; OpenAPI | Raw writes not exposed outside a case |
| Explicit state machine | `agent/service.py` | One action per case |
| Deterministic policy | `policies/engine.py` | Versioned Python rules |
| Graduated authority/risk | `risk/engine.py`, bound approvals | Heuristic, uncalibrated risk |
| Idempotency/verification | SQL ledger, provider key, reconciliation | External-call lock duration limits scale |
| Stripe/webhooks | Test adapter, signature/dedup/replay handlers | Real Stripe test run needs credentials |
| Retrieval | BM25 + TF-IDF; optional API vectors | Five-document regression corpus |
| Memory separation | Claims, authoritative evidence, operational docs | No learned cross-case memory |
| ConduitBench | 500 generated cases, 25 families | Not 500 independent natural-language tasks |
| Metrics and ablations | A/B/C results; business-state oracles | Offline rule planner measured |
| Reviewer/model comparison | Configured runners and usage logging | Not run against external APIs |
| Fault injection | Timeouts, stale source, malformed/rate-limit markers, replay tests | No real infrastructure chaos campaign |
| Operator console | Approve/reduce/reject, evidence, trajectories | Local demo identity |
| Shadow mode | No-mutation path + labeled comparison script | No organization study performed |
| Engineering/testing | Migration, Docker, CI, unit/property/integration/E2E/fault tests | PostgreSQL checks included for CI |
| Final communication | Design docs, report, experiment report, HTML presentation | Public deployment remains external setup |
