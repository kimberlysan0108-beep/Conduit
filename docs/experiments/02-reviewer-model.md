# Experiment 2 — high-risk reviewer

## Hypothesis
A reviewer may detect proposal errors, but may add false rejections and cost.

## Setup
Compare a live model's C run against C with `--reviewer MODEL_ID` on identical fixtures. The reviewer cannot lower deterministic authority or permit denied actions. Only high-risk proposals are reviewed.

## Metrics
Harmful actions, fixture-defined false rejection rate, reviewed case count, safe resolution, p50/p95 latency and token usage. Monetary API cost requires actual provider pricing.

## Results
Not run: no live model credentials were supplied. Mock contract tests are not reviewer-performance results.

## Error analysis
Unavailable/malformed reviews fail closed to human investigation. Because baseline C already prevents known fixture violations, zero additional reduction may simply indicate insufficient benchmark diversity.

## Decision
Do not enable a reviewer by default. Run against held-out semantic errors and compare operational outcomes before accepting its additional latency/cost.
