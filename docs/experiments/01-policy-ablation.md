# Experiment 1 — deterministic safety ablation

## Hypothesis

Separating eligibility and authority from request interpretation will reduce harmful mutations, with an apparent reduction in autonomous resolution.

## Setup

Three configurations, the same 500 fixture states/messages, and the same deterministic intent planner. A disables policy and authorization inside the offline evaluator. B enables policy but disables graduated authorization. C enables both. Identity, accounting constraints and basic workflow checks remain active in every variant. These are deliberately constrained simulator ablations, not unrestricted production agents.

## Metrics

Actual business state, exact action sets, unauthorized/policy-forbidden effects, face-value exposure, escalation quality and local latency. Definitions are in EVALUATION.md.

## Results

| Configuration | Resolved | Safe resolved | Correct outcome | Unauthorized | Policy violations | Loss exposure proxy | p95 local ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| A · no policy or authorization | 84.0% | 52.0% | 68.0% | 32.0% | 12.0% | $13,587.90 | 16.28 |
| B · policy only | 72.0% | 52.0% | 80.0% | 20.0% | 0.0% | $12,918.04 | 17.05 |
| C · policy + authorization | 52.0% | 52.0% | 100.0% | 0.0% | 0.0% | $0.00 | 20.43 |

## Error analysis

A executes ineligible refunds, changes already-shipped addresses and replaces orders without authoritative missing-item verification. A and B execute amounts that require customer/human approval, and low-value fraud-flagged actions without operator review. C pauses these cases. The suite does not model all operational consequences of cancellation/address changes, so the financial metric understates nonmonetary harm.

During implementation, tests exposed a customer-ownership lookup error and Stripe resource-conversion incompatibility. Both were repaired before these final runs. The offline READ path remains read-only in all variants, avoiding an artificial regression caused by treating status lookup as a mutation.

## Decision

Retain deterministic policy + authorization for every served request. Do not promote A/B or relax thresholds based on apparent resolution alone. Keep benchmark ablations outside the production API. The next research priority is held-out language and real-provider crash/retry behavior, not additional UI scope.
