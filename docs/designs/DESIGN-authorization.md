# Design: authorization

## Problem

An eligible action may still exceed permitted autonomy.

## Goals

Enforce READ/AUTO/CONFIRM/HUMAN/DENY with configurable financial thresholds.

## Alternatives

Binary allow/deny; model self-approval; graduated deterministic authorization.

## Chosen design

Derive identity from server credentials, validate target ownership, calculate heuristic risk and bind approval to plan hash.

## Tradeoffs

More customer turns and manual review; risk score is not calibrated.

## Failure modes

Forged authority in messages, stale approval, changed balance, operator attempts to override policy.

## Rollout / test plan

Boundary tests and randomized amounts; HTTP authorization tests; benchmark independently checks forbidden and unauthorized effects.

