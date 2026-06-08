# API与数据契约

## 1. 设计原则

- API只暴露投研辅助、回测和虚拟模拟能力。
- 所有用户可见的策略、回测、模拟结果都必须带免责声明。
- 所有AI生成内容必须经过合规检查。
- 回测和模拟使用同一份 `StrategySpec`。

## 2. 核心状态枚举

策略状态：

- `draft`：草稿。
- `compiled`：已生成规则。
- `backtested`：已回测。
- `paper_running`：模拟盘运行中。
- `paused`：暂停。
- `failed`：失效。
- `data_insufficient`：数据不足。

模拟状态：

- `pending`：等待更新。
- `running`：运行中。
- `paused`：暂停。
- `stopped`：已停止。
- `data_insufficient`：数据不足。

风险等级：

- `observe`：观察。
- `caution`：谨慎。
- `high_risk`：高风险。
- `insufficient_data`：数据不足。

## 3. StrategySpec

```json
{
  "strategy_id": "str_001",
  "name": "沪深300回撤分批模拟策略",
  "source": "user_prompt",
  "asset_universe": ["510300"],
  "market": "CN_A_ETF",
  "frequency": "1d",
  "entry_rules": [
    {"type": "drawdown_from_20d_high", "operator": ">=", "value": 0.05}
  ],
  "exit_rules": [
    {"type": "profit_from_entry", "operator": ">=", "value": 0.03}
  ],
  "position_rule": {"type": "fixed_fraction", "fraction": 0.2},
  "risk_rule": {"max_single_position": 0.4, "max_drawdown_stop": 0.15},
  "constraints": {"t_plus_1": true, "min_lot": 100},
  "disclaimer_required": true
}
```

## 4. 核心接口

### POST /api/strategies/compile

用途：自然语言策略想法转结构化规则草稿。

请求：

```json
{
  "prompt": "我想做一个沪深300回撤5%分批买入，反弹3%减仓的模拟策略",
  "market": "CN_A_ETF",
  "preferred_assets": ["510300"],
  "risk_level": "moderate"
}
```

响应：

```json
{
  "strategy": {
    "name": "沪深300回撤分批模拟策略",
    "source": "user_prompt",
    "asset_universe": ["510300"],
    "frequency": "1d",
    "entry_rules": [{"type": "drawdown_from_20d_high", "operator": ">=", "value": 0.05}],
    "exit_rules": [{"type": "profit_from_entry", "operator": ">=", "value": 0.03}],
    "position_rule": {"type": "fixed_fraction", "fraction": 0.2},
    "risk_rule": {"max_single_position": 0.4, "max_drawdown_stop": 0.15}
  },
  "warnings": ["该策略仅为虚拟模拟规则草稿，不构成投资建议"]
}
```

### POST /api/backtests

用途：运行回测。

请求：

```json
{
  "strategy": {},
  "start_date": "2021-01-01",
  "end_date": "2026-06-05",
  "initial_cash": 100000,
  "fee_rate": 0.0003,
  "slippage_bps": 5
}
```

响应：

```json
{
  "backtest_id": "bt_001",
  "status": "completed",
  "metrics": {
    "total_return": 0.126,
    "annual_return": 0.024,
    "max_drawdown": 0.118,
    "win_rate": 0.47,
    "volatility": 0.19,
    "turnover": 0.62,
    "trade_count": 38
  },
  "assumptions": {
    "fee_rate": 0.0003,
    "slippage_bps": 5,
    "t_plus_1": true,
    "min_lot": 100
  },
  "overfit_warning": "样本内表现不代表未来表现，建议进入模拟盘观察"
}
```

### POST /api/simulations

用途：将已回测策略加入虚拟模拟盘。

请求：

```json
{
  "strategy_id": "str_001",
  "backtest_id": "bt_001",
  "initial_cash": 100000,
  "visibility": "public_delayed"
}
```

响应：

```json
{
  "simulation_id": "sim_001",
  "account_id": "pa_001",
  "status": "running",
  "message": "策略已加入虚拟模拟盘，所有表现仅为模拟结果"
}
```

### GET /api/simulations/{id}

用途：查看虚拟账户表现。

响应：

```json
{
  "simulation_id": "sim_001",
  "status": "running",
  "running_days": 23,
  "account": {
    "initial_cash": 100000,
    "cash": 82000,
    "equity": 101230,
    "positions": [{"symbol": "510300", "quantity": 3600, "market_value": 19230}]
  },
  "metrics": {
    "paper_return": 0.0123,
    "max_drawdown": 0.034,
    "trade_count": 4
  },
  "disclaimer": "虚拟资金模拟，不构成投资建议"
}
```

### GET /api/leaderboards

用途：策略榜单。

查询参数：

- `type`: `performance`、`stability`、`risk_control`、`long_run`。
- `market`: `CN_A_ETF`。

响应：

```json
{
  "leaderboard_type": "stability",
  "items": [
    {
      "strategy_id": "str_001",
      "name": "沪深300回撤分批模拟策略",
      "paper_return": 0.0123,
      "max_drawdown": 0.034,
      "running_days": 23,
      "total_score": 78.5,
      "risk_level": "observe"
    }
  ],
  "disclaimer": "榜单仅展示虚拟模拟表现，不构成投资建议"
}
```

### POST /api/ai/ask

用途：站内AI问答。只基于产品知识库、结构化数据和可引用资料回答，不提供投资建议。

请求：
```json
{
  "question": "这个策略为什么最大回撤这么高？",
  "entry_point": "strategy_detail",
  "context": {
    "strategy_id": "str_001",
    "backtest_id": "bt_001",
    "simulation_id": "sim_001",
    "asset_symbol": "510300"
  },
  "stream": false
}
```

响应：
```json
{
  "answer_id": "ans_001",
  "risk_class": "strategy_explanation",
  "answer": "该策略回撤较高主要与回撤分批规则在震荡下行阶段持续触发有关。回测显示最大回撤为11.8%，交易次数为38次，且手续费和滑点会进一步压低表现。该解释只用于理解模拟策略，不构成投资建议。",
  "citations": [
    {
      "source_type": "backtest_report",
      "source_id": "bt_001",
      "title": "回测报告 bt_001",
      "url": null
    },
    {
      "source_type": "knowledge_chunk",
      "source_id": "kb_drawdown_003",
      "title": "最大回撤为什么重要",
      "url": "/knowledge/drawdown"
    }
  ],
  "suggested_actions": [
    {"type": "view_backtest", "label": "查看回测详情"},
    {"type": "view_simulation", "label": "查看模拟盘表现"}
  ],
  "disclaimer": "AI回答基于当前站内数据和知识库，不构成投资建议"
}
```

高风险问题响应：
```json
{
  "answer_id": "ans_002",
  "risk_class": "blocked_investment_advice",
  "answer": "我不能回答现在是否买入、卖出、加仓或跟随某个策略。可以帮你解释风险证据、把想法转成可回测规则，或查看虚拟模拟表现。",
  "citations": [
    {
      "source_type": "compliance_rule",
      "source_id": "cr_no_advice_001",
      "title": "非投资建议边界",
      "url": "/knowledge/compliance/no-investment-advice"
    }
  ],
  "suggested_actions": [
    {"type": "create_strategy", "label": "把想法转成模拟策略"},
    {"type": "view_risk_card", "label": "查看风险卡"}
  ],
  "disclaimer": "本产品不提供证券投资建议"
}
```

### GET /api/data/sources

用途：展示数据源状态、授权口径和最近同步时间。

响应：
```json
{
  "items": [
    {
      "source_name": "AKShare",
      "tier": "P0_free",
      "domains": ["stock_bars", "fund", "index", "industry"],
      "status": "ok",
      "last_synced_at": "2026-06-06T18:10:00+08:00",
      "rights_status": "public_reference",
      "display_policy": "展示来源和更新时间"
    },
    {
      "source_name": "Tushare Pro",
      "tier": "P1_stable",
      "domains": ["stock", "fund", "financials", "announcements", "news"],
      "status": "not_configured",
      "last_synced_at": null,
      "rights_status": "licensed_required",
      "display_policy": "按授权范围展示"
    }
  ]
}
```

### GET /api/assets/{symbol}/financials

用途：查看个股/ETF关联标的的财务摘要。个股仅作风险背景和解释，不提供推荐。

查询参数：

- `period`: `latest`、`annual`、`quarterly`
- `fields`: 可选字段列表。

响应：
```json
{
  "symbol": "600000",
  "market": "CN_A",
  "latest_period": "2026Q1",
  "quality_status": "ok",
  "source": {
    "source_name": "Tushare Pro",
    "source_url": "https://tushare.pro/",
    "fetched_at": "2026-06-06T18:30:00+08:00"
  },
  "metrics": {
    "revenue_yoy": 0.041,
    "net_profit_yoy": -0.018,
    "roe": 0.087,
    "gross_margin": 0.322,
    "debt_ratio": 0.614,
    "operating_cash_flow": 1280000000
  },
  "explanation_boundary": "财务数据仅作为风险背景，不构成投资建议"
}
```

### GET /api/assets/{symbol}/announcements

用途：查看公告摘要、风险事件和来源链接。

查询参数：

- `type`: 公告类型，可选。
- `limit`: 默认20。

响应：
```json
{
  "symbol": "600000",
  "items": [
    {
      "announcement_id": "ann_001",
      "title": "2026年第一季度报告",
      "announcement_type": "periodic_report",
      "published_at": "2026-04-28T20:00:00+08:00",
      "source_name": "巨潮资讯",
      "source_url": "https://www.cninfo.com.cn/",
      "summary": "机器摘要：公司披露一季度收入、利润和现金流数据，需结合财务指标页查看。",
      "risk_tags": ["periodic_report", "financial_disclosure"],
      "rights_status": "public_linkable"
    }
  ],
  "disclaimer": "公告摘要用于投研解释和风险背景，不构成投资建议"
}
```

### GET /api/news/search

用途：检索公开资讯、公告摘要、监管信息和行业事件。

查询参数：

- `q`: 关键词。
- `symbol`: 标的代码，可选。
- `industry`: 行业，可选。
- `source_type`: `news`、`announcement`、`regulatory`、`research_summary`。

响应：
```json
{
  "query": "AI 半导体 ETF",
  "items": [
    {
      "item_id": "news_001",
      "source_type": "news",
      "title": "半导体行业事件摘要",
      "source_name": "公开资讯源",
      "published_at": "2026-06-06T15:20:00+08:00",
      "summary": "该事件可能影响行业情绪，需结合行业温度和模拟策略表现观察。",
      "related_assets": ["512480"],
      "related_industries": ["半导体"],
      "source_url": "https://example.com/news"
    }
  ]
}
```

## 5. 错误语义

- `DATA_UNAVAILABLE`：数据源不可用。
- `MARKET_CLOSED`：当前不是交易日或市场休市。
- `INSUFFICIENT_HISTORY`：历史数据不足。
- `INVALID_STRATEGY_RULE`：策略规则无法执行。
- `COMPLIANCE_BLOCKED`：输出或输入触发合规拦截。
- `BACKTEST_TIMEOUT`：回测任务超时。
- `SIMULATION_PAUSED`：模拟盘已暂停。
- `SOURCE_RIGHTS_UNKNOWN`：数据版权或展示权限未知。
- `SOURCE_CONFLICT`：多源数据冲突。
- `CITATION_REQUIRED`：AI回答缺少必要引用。
- `AI_NO_GROUNDED_EVIDENCE`：AI问答没有足够依据。
- `QUESTION_HIGH_RISK`：问题涉及买卖建议、跟单、收益承诺等高风险内容。

## 6. 合规接口

### POST /api/compliance/check

请求：

```json
{
  "scene": "strategy_explanation",
  "text": "建议买入这个ETF，目标价很快到达"
}
```

响应：

```json
{
  "allowed": false,
  "blocked_terms": ["建议买入", "目标价"],
  "replacement_guidance": "请改写为触发策略观察规则，不构成投资建议"
}
```
