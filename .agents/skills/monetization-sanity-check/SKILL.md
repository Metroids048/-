---
name: monetization-sanity-check
description: Use this skill before Alpha模拟场 monetization work to prove the paid reason first and prevent premature payments, trading, copy-trading, or feature sprawl.
---

# Monetization Sanity Check

Use this before adding pricing, payment, subscription, report, or commercial copy.

## Required reading

- `AGENTS.md`
- `docs/current/CURRENT_MVP.md`
- `docs/current/DEFERRED_SCOPE.md`
- `docs/current/ACCEPTANCE_CHECKLIST.md`

## Decision rules

Allowed in P0:

- Show why a user might pay later.
- Preview strategy capacity, 7-day observation, review report, simulation accounts, and risk diagnosis.
- Keep all payment language as validation copy or candidate package copy.

Not allowed in P0:

- Payment checkout.
- Subscription account system.
- Real trading.
- Broker connection.
- Auto order placement.
- Copy-trading.
- Revenue promise.

## Output required

Before implementation, answer:

1. What paid reason does this make clearer?
2. Does it require payment infrastructure? If yes, defer it.
3. Does it imply investment advice, copy-trading, or revenue promise? If yes, rewrite it.
4. Which P0 acceptance checks prove the change works?
