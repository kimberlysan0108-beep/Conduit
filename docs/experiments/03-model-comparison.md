# Experiment 3 — model comparison

## Hypothesis
A more capable intent model may resolve more varied language, but confidence alone should not grant authority.

## Setup
Use `python -m benchmark.evaluators.run --variant C --models MODEL_1 MODEL_2` with two to four real provider model IDs and identical fixtures. Record model IDs, provider/date, corpus hash and configuration with results.

## Metrics
Business-state resolution, safe resolution, unauthorized/policy effects, escalation, tool efficiency, tokens, latency and externally priced cost.

## Results
Not run: the supplied measurements use the deterministic rules baseline. No model ranking or fabricated numbers are reported.

## Error analysis
Provider failures, JSON validation errors and low confidence escalate or ask for clarification. Generated intent templates cannot establish broad-language performance.

## Decision
Choose a model only after a held-out comparison, optimizing safe operational resolution rather than fluency.
