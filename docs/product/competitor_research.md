# 竞品与开源调研

## 1. 结论

成熟产品的共同商业逻辑不是“AI告诉用户买什么”，而是卖以下能力：

- 研究环境：策略编辑、数据、Notebook、指标、模板。
- 回测能力：更长数据、更快速度、更多并发、更真实费用/滑点。
- 模拟/纸面交易：让策略在真实市场数据流中前向验证。
- 策略展示：榜单、评分、诊断、社区、周报。
- 自动化容量：机器人数量、提醒数量、策略数量、云节点数量。
- 数据和资讯整合：统一数据源、质量控制、可追溯引用。

因此本产品V1不应再强调“小白解释市场”，而应强调 **AI策略实验 + 回测 + 虚拟模拟 + 可复盘记录**。市场解释和知识库用于解释策略表现、增强信任和降低合规风险。

## 2. 竞品矩阵

| 产品/项目 | 定位 | 核心功能 | 付费抓手 | 模拟盘/前向验证 | 可借鉴点 | 不可照搬点 |
|---|---|---|---|---|---|---|
| QuantConnect/LEAN | 专业算法交易平台 | 研究、回测、优化、实盘、数据市场 | 云节点、研究资源、数据、实盘部署 | 支持回测和实盘，LEAN开源 | 统一策略引擎、回测和实盘一致、工程化严谨 | V1不要做实盘和多资产复杂引擎 |
| RiceQuant | 国内量化平台 | 在线策略、回测、实时模拟、信号推送 | 企业版、数据和平台能力 | 回测后可启动实时模拟 | 回测后进入模拟盘的产品链路 | 不要让信号推送变成荐股 |
| JoinQuant | 国内云端量化平台 | API、回测、模拟、研究 | 数据、平台、量化服务 | 文档区分回测/模拟专用API | A股规则、滑点、风险指标口径 | 不做专业开发者IDE作为V1重点 |
| BigQuant | AI量化平台 | 因子、策略、机器学习、研究平台 | 平台和数据能力 | 偏研究与策略开发 | AI量化叙事、因子研究流程 | V1不要做复杂ML建模主线 |
| TrendSpider | 市场分析和自动化工具 | 扫描、策略测试、机器人、提醒 | 机器人数量、提醒、数据、回测深度 | 偏自动化和提醒 | 用容量限制设计订阅层级 | 不接交易机器人/实盘 |
| TradingView | 图表和社区平台 | 图表、Pine、策略测试、纸面交易 | 数据、图表、提醒、脚本生态 | Paper Trading和策略测试 | 社区化策略、图表体验 | 回测过度乐观、脚本信号易被当跟单 |
| Composer | 自然语言/可视化策略构建 | 策略构建、回测、费用滑点估算、自动投资 | 策略构建和自动化 | 偏投资组合自动化 | 自然语言策略构建体验 | 不做真实自动投资 |
| Portfolio123 | 股票筛选和策略研究 | 筛选、因子、回测、组合 | 数据、筛选、研究能力 | 偏研究和组合回测 | 因子筛选和稳健性检查 | 产品门槛较高，不适合直接复制 |
| Collective2 | 策略市场 | 策略发布、模型账户、订阅、自动交易 | 策略经理计划、订阅市场 | 模型账户和策略记录 | 模型账户、策略记录、管理者工具 | V1不能做跟单/订阅信号/作者收费 |
| Numerai | 模型竞赛和信号市场 | 数据集、提交、评分、榜单、staking | staking和模型声誉 | 按轮次评分，非传统模拟盘 | 长周期评分、声誉、反过拟合 | 不照搬staking和加密激励 |
| Freqtrade | 开源交易机器人 | 策略、回测、dry-run、Web UI、机器学习优化 | 开源，自部署 | Dry-run强调先模拟 | dry-run、免责声明、配置化策略 | 加密交易和实盘机器人不适合A股V1 |
| NautilusTrader | 高性能交易引擎 | 事件驱动、回测、实盘、严格测试 | 开源/专业生态 | 支持事件驱动回测与实盘 | 事件驱动和测试严谨性 | 太重，不适合MVP核心 |
| Qlib | AI量化研究平台 | 数据、模型、回测、AI研究 | 开源/研究生态 | 偏研究评估 | AI量化研究流程、模型评估 | V1不要从ML模型起步 |
| OpenBB | 金融数据平台 | 多数据源、统一API、AI代理、研究终端 | Workspace、企业、数据集成 | 非模拟盘核心 | 统一数据适配层、AI可审计 | AGPL/商业授权需注意 |

## 3. 可借鉴功能

### 策略容量收费

来自 TrendSpider、QuantConnect、Collective2 等。V1应按策略数量、模拟账户数量、回测次数、历史数据长度做订阅分层，而不是卖“策略收益”。

### 回测后启动模拟

来自 RiceQuant。V1流程应固定为：

> 策略规则 -> 回测 -> 回测通过 -> 加入模拟盘。

不要允许AI直接把策略加入模拟盘，也不要让用户绕过回测。

### 费用、滑点、现实约束

来自 Composer、TradingView用户反馈、Portfolio123、RiceQuant。V1回测必须展示：

- 手续费。
- 滑点。
- 最小交易单位。
- T+1。
- 停牌和涨跌停处理。
- 样本区间。

### 前向验证重于回测

来自 TradingView和Numerai经验。产品文案要强调：

- 回测不是证据终点。
- 模拟盘持续表现才是核心。
- 榜单按运行天数和稳定性加权。

### 声誉和长跑榜

来自 Numerai/Collective2。V1可以做策略声誉，但不要做资金staking和跟单订阅。策略榜单应重视运行天数、回撤和稳定性，而不是单日收益。

## 4. 不可照搬点

- 不做Collective2式策略订阅和自动跟单。
- 不做QuantConnect式完整实盘交易栈。
- 不做TrendSpider式交易机器人。
- 不做Numerai式staking。
- 不做TradingView式实时脚本信号售卖。
- 不做Qlib式复杂机器学习研究作为V1主线。

## 5. 对本产品的落地建议

V1必须围绕一个核心闭环：

> 用户提交策略想法 -> AI生成规则 -> 回测 -> 模拟盘前向验证 -> 策略卡和榜单展示 -> 复盘和付费扩容。

优先做“可观察、可复盘、可持续运行”，不要急着做“高级AI预测”。成熟平台给出的信号很清楚：真正能收费的是平台资源和持续工作流，不是一次性观点。

## 6. 关键资料

- QuantConnect/LEAN：https://github.com/QuantConnect/Lean
- QuantConnect Algorithm Engine：https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine
- RiceQuant实时模拟交易：https://www.ricequant.com/doc/quant/pt.html
- RiceQuant回测：https://www.ricequant.com/doc/quant/backtest
- Freqtrade：https://github.com/freqtrade/freqtrade
- NautilusTrader：https://nautilustrader.io/open-source/
- Qlib：https://github.com/microsoft/qlib
- OpenBB：https://openbb.co/products/odp
- Numerai Docs：https://docs.numer.ai/tournament/learn
- Collective2：https://www.collective2.com/choose-plan
- Portfolio123：https://www.portfolio123.com/

