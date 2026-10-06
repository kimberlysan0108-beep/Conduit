# Design: policy engine

## Problem

Prompt-only policy can be overridden by customer instructions.

## Goals

Keep eligibility versioned and independently testable.

## Alternatives

Prompt text, a general-purpose DSL, or typed Python rules.

## Chosen design

Typed Python rules for refund balance/cancellation, owned cancellation, missing-order replacement, pre-shipment address and exception credits. Documents support explanation only.

## Tradeoffs

Small rule set is readable; editing policy requires code review. USD and scoped workflows only.

## Failure modes

Timestamp ambiguity, expired exceptions, already-refunded balances, and shipped orders.

## Rollout / test plan

Boundary/property tests, adversarial prose test, recheck policy after approval, policy ablation in an isolated simulator.

