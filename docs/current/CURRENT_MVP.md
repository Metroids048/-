# CURRENT_MVP.md

## 当前产品

AI投资想法体检器

## 当前目标

先做流量，不做付费。让用户输入一个投资想法，立即生成一张可分享的想法体检卡。

## P0 功能

1. 投资想法输入
2. 想法类型识别
3. 虚拟样本回放（`replay_type: demo_virtual_sample`）
4. 风险反例
5. 小白提醒
6. 今日热点体检榜
7. 分享内容生成

## P0 API

- `GET /api/content/home`
- `POST /api/ideas/diagnose`
- `GET /api/ideas/trending`
- `POST /api/content/share-card`

## P0.5 补充能力

- `POST /api/ideas/diagnose` 支持可选 `symbol`，用于把代码作为体检上下文。
- `GET /api/assets/search?q=` 和 `GET /api/assets/{symbol}/overview` 作为二级研究上下文 API 保留。
- 首页仍以体检卡、热点榜和分享内容为主，不直接展示完整行情、策略工厂、回测、模拟盘或榜单。

## 保留但降级

- `POST /api/strategies/compile`
- `POST /api/backtests`
- `POST /api/simulations`
- `GET /api/leaderboards`

## 不做

- 真实交易
- 买卖建议
- 目标价
- 跟单
- 收益承诺
- 7天观察作为主卖点
- 完整 Next.js 前端

## 成功标准

1. 用户 10 秒内知道这是投资想法体检工具。
2. 用户输入一句想法后能产出体检卡。
3. 结果页能看到虚拟样本回放、风险反例和小白提醒。
4. 虚拟回放必须标注 `replay_type: demo_virtual_sample`。
5. 结果页可生成分享标题和短视频脚本。
6. 所有对外文案明确“不构成投资建议”。
