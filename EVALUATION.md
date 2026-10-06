# Conduit evaluation

## What was actually run

500 deterministic cases per configuration, seed 41, across 25 scenario families. A total of 1,500 case executions were run on local SQLite. All configurations used the **same rule-based intent classifier**. These are orchestration/policy ablations, not empirical LLM comparisons. No provider API charges were incurred. Dates in seed business records are fixed; expiring exception fixtures are relative to the execution date.

| Configuration | Resolved | Safe resolved | Correct outcome | Unauthorized | Policy violations | Loss exposure proxy | p95 local ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| A · no policy or authorization | 84.0% | 52.0% | 68.0% | 32.0% | 12.0% | $13,587.90 | 16.28 |
| B · policy only | 72.0% | 52.0% | 80.0% | 20.0% | 0.0% | $12,918.04 | 17.05 |
| C · policy + authorization | 52.0% | 52.0% | 100.0% | 0.0% | 0.0% | $0.00 | 20.43 |

## Metric definitions

- **Resolution:** actual expected business state was reached, independent of whether the action was authorized. This intentionally exposes unsafe apparent success.
- **Safe resolution:** business state resolved and no fixture-defined unauthorized/forbidden mutation occurred.
- **Correct outcome:** expected terminal/pause state AND correct action set, including correct requests for confirmation, clarification or human review.
- **Correct action rate:** fixture-authorized action set matched the executed ledger; not text similarity.
- **Unauthorized action rate:** fraction of cases with at least one executed action absent from fixture allowed actions. Denied policy actions also count here.
- **Policy violation:** executed action in the fixture's explicit forbidden action list.
- **Financial loss:** conservative face-value exposure proxy: cents of financial actions absent from the permitted set. It is **not realized loss**, calibrated expected loss, or measured customer harm. Replacement value counts as cost exposure; cancellation/address actions contribute zero cents.
- **Escalation precision / recall:** compare ESCALATE outcomes to independent scenario labels; ASK_USER and CONFIRM are distinct.
- **Latency:** local setup + execution elapsed time per case. This is not production HTTP latency and contains no LLM/Stripe network delay. p50/p95 use the recorded observations.
- **Tool calls/errors/retries:** explicit audit events, excluding state-only entries. A retry rate counts cases that passed through RETRY; reconciliation is separately visible in the trajectory.
- **Customer turns:** one initial customer message in this benchmark. Confirmation completion is tested in E2E tests rather than simulated in this comparison.
- **Tokens/cost:** rules use zero model tokens and zero model API cost. Live model runs record tokens but leave cost null until pricing is supplied externally.

## What the benchmark supports

Authorization reduces unsafe apparent resolution in this suite. Configuration C correctly pauses instead of mutating cases needing approval, and passes the deterministic safety gate. Its 52% automatic resolution rate is lower than A's 84%, while its safe resolution rate remains 52%. The difference is not evidence that the system understands arbitrary customer requests.

**100% correct outcome is a regression-suite result, not a generalization estimate.** These fixtures are generated from 25 known families with limited wording and amount variations. Do not publish this as “100% AI accuracy,” a production safety guarantee, or a measured reduction in real financial loss. No confidence interval over these repeated synthetic templates would establish independent real-world performance.

## Retrieval

Five policy documents, five labeled queries, BM25 + TF-IDF cosine with reciprocal-rank fusion and a title-overlap reranker. Measured Recall@3 = 1.0, MRR = 1.0, nDCG@3 ≈ 0.98394. This is a tiny regression test. API semantic embeddings are configurable but were not used in this run.

## Verification completed

45 pytest test cases passed, including Hypothesis-generated inputs, API integration, confirmation and operator paths, balance concurrency, expired/invalid policy handling, signed webhook fixtures, and provider-processed/lost-response reconciliation. The TypeScript/Vite production build passed. SQLite migration + seeding and local HTTP demo were exercised.

PostgreSQL concurrency and migrations are configured in CI but were not executed in this workspace, which has no PostgreSQL/Docker runtime. Browser automation could not run because the browser binary download was unavailable; no visual/browser E2E pass is claimed. Stripe and model contracts use mocks, not a live sandbox. Two dependency deprecation warnings were emitted; they did not fail the tests.

## Unrun experiments

The model sweep and high-risk reviewer hooks are implemented. They require actual model IDs and API credentials. No claim is made about larger models or reviewer benefit. Reviewer false rejections, latency and token usage are emitted by the runner when enabled; compare the reviewed C run to the corresponding unreviewed model C run. A rejection is flagged as potentially false when its fixture did not require human escalation.

The shadow-mode comparison script requires labeled operator observations. None were provided or invented.

## Next highest-value experiment

Before wider autonomy, add a held-out, human-authored corpus with partial-refund language, multiple actions, ambiguous IDs, authorization changes, stale external timestamps, repeated requests across sessions, and crash recovery. Run the PostgreSQL concurrency job and real Stripe test cases, then compare two actual models under identical fixed policies. Only then perform a no-mutation operator shadow study.
