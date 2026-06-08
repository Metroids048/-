# P0_ACCEPTANCE.md

## 当前唯一产品

AI投资想法体检器。

一句话定位：看到热点想买？先让 AI 体检一下。

副标题：输入一句投资想法，生成虚拟样本回放、风险反例、小白提醒和可分享内容。不荐股、不跟单、不接真实资金、不提供买卖建议。

## 当前唯一入口

FastAPI 根路径 `/` 提供 `app/static/index.html`。

启动命令：

```powershell
py -3 -m uvicorn apps.api.alpha_sim.main:app --reload --port 8000
```

## 当前唯一 P0 API

- `GET /api/content/home`
- `GET /api/ideas/trending`
- `POST /api/ideas/diagnose`
- `POST /api/content/share-card`

## P0.5 二级研究上下文 API

以下接口只用于代码/标的研究上下文，不得作为当前首页主卖点，也不得输出买卖指令、目标价或收益承诺：

- `GET /api/assets/search?q=`
- `GET /api/assets/{symbol}/overview`

`POST /api/ideas/diagnose` 允许携带可选 `symbol` 字段，但用户输入原文必须保留，诊断结果仍必须包含 `replay_type: demo_virtual_sample`。

## 当前 P0 页面必须包含

- AI投资想法体检器
- 看到热点想买
- `ideaInput`
- `diagnoseIdea`
- `diagnosisCard`
- `trendingIdeaList`
- `contentGenerator`
- 不构成投资建议
- 不接真实资金
- 不提供买卖建议

## 当前 P0 页面不得包含

- Alpha模拟场
- 策略工厂
- 运行回测
- 加入模拟盘
- 7天观察
- 问问Alpha
- 风险卡
- 知识库
- 数据源
- 市场解释

## 当前 P0 JS 只能调用

- `/api/content/home`
- `/api/ideas/trending`
- `/api/ideas/diagnose`
- `/api/content/share-card`

首页可以提交可选代码上下文到 `/api/ideas/diagnose`，但不得直接调用行情、策略、回测、模拟盘或榜单 API。

## Legacy / P2 说明

- `apps/web` 是 P2/future，不参与当前 P0。
- 旧策略链路（compile / backtest / simulation / leaderboard）保留为 legacy，不得进入首页。

## 每次任务必须运行

```powershell
py -3 -m pytest tests/ -q
```

## 通过标准

1. pytest 通过
2. 四个 P0 API 返回 200
3. 首页可打开（`http://127.0.0.1:8000`）
4. 浏览器 console 无 JS 报错

## Codex 任务口令

开始前先阅读本文件，结束前逐条验收。
