# Conduit — final technical report

Prepared for Kimberly Sánchez's Applied AI / Agent Engineering internship simulation.

## Problem and approach

Action-taking agents can produce confident text while violating policy, authority or accounting invariants. Conduit assigns interpretation to an optional model and assigns consequential decisions to deterministic code. The deliverable is an end-to-end local prototype with reproducible simulator evidence, not a completed 12-week field study.

## Delivered system

A FastAPI merchant simulator, SQL schema/migration, typed requests, explicit case workflow, versioned policies, graduated authorization, heuristic risk, customer confirmation, operator approve/reduce/reject, idempotent action ledger, post-action verification, Stripe test adapter, signed event ingestion/replay, optional Redis-assisted worker, retrieval and separated state. React console shows evidence and complete audit events without exposing hidden model reasoning.

## Research evidence

| Configuration | Resolved | Safe resolved | Correct outcome | Unauthorized | Policy violations | Loss exposure proxy | p95 local ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| A · no policy or authorization | 84.0% | 52.0% | 68.0% | 32.0% | 12.0% | $13,587.90 | 16.28 |
| B · policy only | 72.0% | 52.0% | 80.0% | 20.0% | 0.0% | $12,918.04 | 17.05 |
| C · policy + authorization | 52.0% | 52.0% | 100.0% | 0.0% | 0.0% | $0.00 | 20.43 |

These results used a rules planner and 500 synthetic fixtures per configuration. 45 automated tests and the frontend production build passed. See EVALUATION.md for precise definitions and restrictions. No live LLM comparison, reviewer experiment, Stripe sandbox run, PostgreSQL local run, public deployment or organization shadow study was completed here.

## Most dangerous remaining failure modes

1. External-provider crash boundaries: the provider cannot participate in a local SQL transaction. Stable request keys help repeated logical actions, but a crash can roll back the local pending ledger. Unknown results must be reconciled with provider records; long-delayed retries are blocked. Production rollout needs durable pre-call intents/outbox and balance reservations across process death, with crash tests against a real provider.
2. Unsupported free-text precision: the planner supports a narrow one-action vocabulary. Partial amounts and compound requests need richer typed interpretation and confirmation semantics before expanded autonomy.
3. Authentication and deployment: demo static credentials and one configured customer are not production identity infrastructure. Public deployment needs real IAM, tenant isolation, secret management and access auditing.
4. Calibration and distribution shift: the heuristic expected-loss number is an uncalibrated prioritization score. Synthetic template success does not establish safe behavior on independent requests.
5. Throughput and event races: external calls hold customer locks; PostgreSQL tests must be run in CI and expanded to worker/API/webhook concurrency before scale.

## Assumptions challenged

Raw resolution was not the right optimization target: ablation A reports more resolved business states while executing forbidden or unapproved changes. Retrieval prose is not authority. A second model is not automatically a safety improvement. An accepted provider response is not verified completion.

## Recommended next architecture

Keep deterministic eligibility and authority. Move external mutations to a durable intent/outbox worker with explicit reservation and reconciliation lifecycle. Introduce production identity before any external deployment. Expand held-out semantic and crash tests; run real model/reviewer experiments and Stripe test mode. Then conduct shadow mode with labeled human outcomes. Do not grant broader autonomy before that evidence exists.

## Manager check-in

- Shipped: local application, safety controls, 500-case benchmark, tests, experiment runner and documentation.
- Learned: authorization suppresses unsafe apparent resolution in this simulator.
- Failed assumptions: “correct response” and “API accepted” do not prove correct business outcomes.
- Dangerous current failure: provider/SQL process-crash coordination.
- Objective: safe verified resolution with escalation when evidence or authority is insufficient.
- Deterministic boundary: identity, money, policy, authority, idempotency and verification.
- Model value: supported-intent understanding and optional high-risk review, pending measured evidence.
- Avoided overengineering: no unnecessary multi-agent architecture or learned risk model.
- Next experiment: held-out language plus real-provider crash/retry behavior.
- Rejected AI suggestion: treating offline rules/TF-IDF results as live LLM/semantic-embedding evidence.

## Honest résumé phrasing

Built a local risk-aware support-resolution prototype across billing, subscriptions and orders; implemented deterministic authorization, idempotency and verification; developed a 500-case synthetic benchmark and executed three policy/authorization configurations. Do not claim real customer deployment, measured real-world loss reduction or live model performance from this delivery.
