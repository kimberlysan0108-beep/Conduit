# Design: idempotency

## Problem

The provider may act before a network timeout reaches the caller.

## Goals

Never duplicate the same logical mutation on retry; serialize competing balances.

## Alternatives

Trust client retries, in-memory cache, or durable SQL action ledger plus provider key.

## Chosen design

Persist case identity first; bind action key to plan hash; use unique constraints and customer row locks; reconcile uncertain outcomes.

## Tradeoffs

Provider calls hold locks; SQL/provider cannot be one atomic transaction. Conservative pending-action blocking sacrifices availability.

## Failure modes

Crash after provider commit, reused request key, expired provider idempotency window, concurrent cases.

## Rollout / test plan

Repeat property tests, concurrent case test, post-acceptance timeout, signed event replay, PostgreSQL concurrency CI.

