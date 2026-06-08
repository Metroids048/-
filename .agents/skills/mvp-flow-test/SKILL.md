---
name: mvp-flow-test
description: Use after changing AI投资想法体检器 API, frontend, or services to verify the P0 flow diagnose to share-card. Read docs/current/P0_ACCEPTANCE.md first. Legacy compile/backtest/simulation/leaderboard is P2 only.
---

# MVP Flow Test

## P0 flow to verify

1. `GET /api/v1/health`
2. `GET /api/content/home`
3. `GET /api/ideas/trending`
4. `POST /api/ideas/diagnose`
5. `POST /api/content/share-card`

## Required checks

- API returns valid JSON.
- Frontend can render returned fields.
- No undefined/null values break rendering.
- Errors show user-friendly messages.
- Compliance disclaimer appears in flow.
- `replay_type` is `demo_virtual_sample`.
- Share-card works with `diagnosis` fallback payload.

## Legacy flow (P2 only, not homepage)

- `POST /api/strategies/compile`
- `POST /api/backtests`
- `POST /api/simulations`
- `GET /api/leaderboards`

## Test command

```powershell
py -3 -m pytest tests/ -q
```

## Output required

1. Commands run.
2. Passed tests.
3. Failed tests.
4. Manual checks performed.
5. Remaining risks.
