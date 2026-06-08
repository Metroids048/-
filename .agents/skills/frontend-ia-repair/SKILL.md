---
name: frontend-ia-repair
description: Use when repairing AI投资想法体检器 static homepage layout, information architecture, visual hierarchy, responsive states, and P0 flow UI. Read docs/current/P0_ACCEPTANCE.md first.
---

# Frontend IA Repair

## Goal

Keep the static homepage focused on the P0 flow:

输入投资想法 -> 生成体检卡 -> 生成分享内容。

## Required reading

- `docs/current/P0_ACCEPTANCE.md`
- `AGENTS.md`
- `docs/current/INFORMATION_ARCHITECTURE.md`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

## Homepage allows

1. Hero（产品定位 + 合规边界）
2. 主 CTA：生成想法体检卡
3. 想法输入区
4. 想法体检卡
5. 今日热点体检榜
6. 内容生成区
7. 合规声明

## Homepage forbids

1. Alpha模拟场 / 策略工厂
2. 运行回测 / 加入模拟盘 / 7天观察
3. 问问Alpha / 风险卡 / 知识库 / 数据源 / 市场解释
4. 商业化说明
5. Legacy API calls in `app.js`

## Output required

1. Which sections were changed.
2. Which forbidden content was removed.
3. Loading / empty / error states preserved.
4. `py -3 -m pytest tests/test_p0_static_homepage.py tests/test_p0_static_js.py -q` result.
