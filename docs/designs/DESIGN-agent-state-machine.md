# Design: agent state machine

## Problem

Unbounded model loops can perform unintended tool calls.

## Goals

Resolve a narrow set of support workflows with explicit, inspectable decisions.

## Alternatives

Free-running tool calling; a fixed script; a state machine with a constrained intent classifier.

## Chosen design

Use typed intent classification followed by deterministic gather → policy → plan → authorize → execute → verify. Missing information asks the user.

## Tradeoffs

Less flexible natural-language coverage; one action per case.

## Failure modes

Ambiguity, unavailable model, malformed tool response and stale facts must pause or escalate.

## Rollout / test plan

Unit-check invalid transitions; E2E check refund and cancellation; fault-check retry and reconciliation.

