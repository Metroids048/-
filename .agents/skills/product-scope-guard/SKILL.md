---
name: product-scope-guard
description: Use before AI投资想法体检器 product changes to prevent scope creep, homepage clutter, investment-advice behavior, or P1/P2 leakage into P0. Read docs/current/P0_ACCEPTANCE.md first.
---

# Product Scope Guard

Use this before product, API, or UI changes in AI投资想法体检器.

## Required reading

- `docs/current/P0_ACCEPTANCE.md`
- `AGENTS.md`
- `docs/current/CURRENT_MVP.md`
- `docs/current/DEFERRED_SCOPE.md`

## P0 allowed

- Investment idea input
- Idea diagnosis card
- Virtual sample replay
- Risk counterexamples
- Xiaobai reminder
- Trending idea list
- Share content generation
- Compliance boundary

## Legacy / not allowed in P0 homepage

- Strategy factory
- Backtest
- Virtual simulation
- Leaderboard
- Ask Alpha full Q&A
- Knowledge base full page
- Market explanation feed
- Risk card detail
- Commercialization
- Multi-market expansion
- Real trading
- Broker integration
- Auto order placement
- Copy trading
- `apps/web` Next.js frontend

## Output required before implementation

1. Is this request P0, P1, P2, or prohibited?
2. If P1/P2, should it be deferred?
3. Which files may be changed?
4. Which files must not be changed?
5. What acceptance criteria prove the request stayed in scope?
