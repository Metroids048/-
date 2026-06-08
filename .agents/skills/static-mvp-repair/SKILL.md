---
name: static-mvp-repair
description: Use when modifying app/static HTML, CSS, or JS for the FastAPI-served P0 MVP. Read docs/current/P0_ACCEPTANCE.md first.
---

# Static MVP Repair

## Current frontend

Use only:
- app/static/index.html
- app/static/app.js
- app/static/styles.css

Do not develop:
- apps/web

## Required APIs

- /api/content/home
- /api/ideas/diagnose
- /api/ideas/trending
- /api/content/share-card

## Required checks

- DOM ids match JS selectors
- loading / empty / error states exist
- mobile layout works
- tests pass
