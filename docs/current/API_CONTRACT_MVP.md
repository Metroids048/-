# API_CONTRACT_MVP.md

## 当前 P0 API

### GET `/api/v1/health`

用途：健康检查。

最低返回字段：

- `status`
- `service`
- `version`

### GET `/api/content/home`

用途：返回新首页文案与合规边界。

最低返回字段：

- `product_name`
- `positioning`
- `hero_promise`
- `primary_cta`
- `compliance_boundary`

### POST `/api/ideas/diagnose`

用途：对用户投资想法进行体检并返回风险解释。

最低返回字段：

- `idea_id`
- `raw_idea`（保留用户原文）
- `idea_type`
- `emotion_tag`
- `diagnosis_summary`
- `replay_type`（固定为 `demo_virtual_sample`）
- `replay_note`（固定为：以下为虚拟/示例样本回放，非真实历史统计，不代表未来表现。）
- `historical_replay`
- `risk_flags`
- `failure_cases`
- `xiaobai_reminder`
- `disclaimer`

可选字段：

- `warning`（用户输入含禁词时返回）
- `diagnosis_basis`（体检依据标签）
- `diagnosis_lens`（小白可读解释）
- `symbol`：P0.5 可选代码上下文，仅用于体检依据，不改变用户原文。

## P0.5 二级研究上下文 API

### GET `/api/assets/search?q=&limit=`

用途：统一股票、ETF、基金、指数等标的搜索入口，服务代码详情页或体检上下文，不作为当前首页主卖点。

最低返回字段：

- `query`
- `items`
- `disclaimer`

`items` 内最低字段：

- `symbol`
- `name`
- `asset_type`
- `market`
- `exchange`
- `tags`
- `status`
- `source`
- `disclaimer`

### GET `/api/assets/{symbol}/overview`

用途：返回标的轻量概览，包含价格样本、数据来源、质量状态、风险标签和下一步研究动作。

最低返回字段：

- `symbol`
- `name`
- `asset_type`
- `market`
- `latest_price`
- `change_pct`
- `data_time`
- `source`
- `quality_status`
- `risk_level`
- `risk_tags`
- `suggested_next_steps`
- `disclaimer`

要求：数据不足时 `latest_price` 和 `change_pct` 可以为空，必须返回 `fallback_notice`，不得用其他标的样本伪装为当前代码行情。

### GET `/api/ideas/trending`

用途：返回今日热点体检榜。

最低返回字段：

- `items`
- `disclaimer`

`items` 内最低字段：

- `id`
- `title`
- `idea_type`
- `heat_score`
- `risk_score`
- `teaser`

### POST `/api/content/share-card`

用途：基于体检结果生成平台化分享文案。

请求字段：

- `diagnosis_id`（可选，优先查内存缓存）
- `platform`（默认 `xiaohongshu`）
- `diagnosis`（可选，缓存丢失时直接传入完整体检结果兜底）

最低返回字段：

- `titles`
- `body`
- `short_video_script`
- `disclaimer`

`short_video_script` 内最低字段：

- `hook`
- `body`
- `ending`

## 保留但降级 API

以下接口保留用于兼容与降级流程，不作为首页主链路：

- `POST /api/strategies/compile`
- `POST /api/backtests`
- `POST /api/simulations`
- `GET /api/leaderboards`

## 错误和合规要求

- 错误必须返回明确 message 或 detail。
- 虚拟回放必须在 `replay_type` 字段标注 `demo_virtual_sample`。
- 用户输入保留原文；含禁词时附加 `warning`，不替换原文。
- 系统输出不允许返回投资建议、目标价、买卖指令、收益承诺、自动下单或跟单暗示。
