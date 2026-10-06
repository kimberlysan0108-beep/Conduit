# Design: evaluation

## Problem

Text similarity can reward a correct-sounding response after an unsafe mutation.

## Goals

Measure actual business state, unauthorized effects, escalation, loss exposure and operational cost.

## Alternatives

Text grading only, hand examples, or reproducible fixtures with business-state oracles.

## Chosen design

500 seeded cases from 25 families; fixture-authored expected states/actions; A/B/C offline ablations; optional model/reviewer sweeps.

## Tradeoffs

Synthetic coverage can be overfit. No claims about external customers or unseen language based on this suite.

## Failure modes

Circular oracles, changed baselines, unsupported model cost claims, misleading 100% results.

## Rollout / test plan

Keep expected outcomes independent from policy implementation; inspect trajectories; add held-out human-authored scenarios before real deployment.

