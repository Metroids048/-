# 开发前就绪检查表

## 1. 产品就绪

- 产品定位已固定为“AI量化投研 + 虚拟模拟盘”。
- 首发市场已固定为A股/ETF。
- 模拟盘是核心付费价值，投研解释是辅助层。
- V1不做实盘、不接券商、不跟单。
- P0/P1/P2功能优先级已明确。

## 2. 合规就绪

- 已有禁止表达清单。
- 已有标准免责声明。
- 榜单名称已规避“赚钱榜/跟买榜”。
- 付费权益不包含实时买卖信号。
- 当前虚拟持仓和成交采用盘后或延迟展示。
- 高风险用户问题有规则回复。

## 3. 数据就绪

- P0数据源：AKShare、efinance、qstock。
- P1数据源：Tushare Pro。
- 已定义MarketDataProvider、FundDataProvider、NewsProvider。
- 已定义数据质量状态。
- 已定义数据异常降级规则。
- 已考虑交易日历、停牌、涨跌停、复权、T+1。
- 已扩展P0数据源到BaoStock、巨潮资讯、交易所/监管公开信息。
- 已定义AnnouncementProvider、FinancialReportProvider、IndustryProvider、ResearchProvider、RegulatoryProvider。
- 已定义数据源注册表、授权口径、版权/robots检查、多源冲突规则。
- 已定义财报、公告、行业、监管、新闻摘要的来源追溯字段。

## 4. 量化引擎就绪

- StrategySpec已定义。
- 回测和模拟共用同一份策略规则。
- 已定义手续费、滑点、最小交易单位。
- 已定义模拟撮合规则。
- 已定义策略评分公式。
- 已定义V1策略模板。

## 5. 技术架构就绪

- 前端：Next.js/React。
- 后端：FastAPI。
- 数据库：PostgreSQL + pgvector。
- 异步任务：Redis + RQ/Celery。
- 回测：vectorbt优先。
- 数据源：AKShare/efinance/qstock起步。
- AI：LLM网关，禁止直接参与交易计算。
- AI问答：Qwen3 8B/14B优先，轻量Qwen降级，DeepSeek-R1-Distill-Qwen后置用于复杂推理。
- RAG：Qwen3-Embedding或BGE-M3，Qwen3-Reranker或BGE Reranker。
- 模型服务：MVP可用Ollama/llama.cpp，有GPU后迁移vLLM/SGLang。
- 所有AI回答必须有引用检查、合规过滤和问题日志。

## 6. API就绪

核心接口已定义：

- `POST /api/strategies/compile`
- `POST /api/backtests`
- `POST /api/simulations`
- `GET /api/simulations/{id}`
- `GET /api/leaderboards`
- `GET /api/assets/{symbol}/risk-card`
- `GET /api/market/summary`
- `POST /api/knowledge/query`
- `POST /api/compliance/check`
- `POST /api/ai/ask`
- `GET /api/data/sources`
- `GET /api/assets/{symbol}/financials`
- `GET /api/assets/{symbol}/announcements`
- `GET /api/news/search`

## 7. 测试就绪

必须提前准备测试数据：

- 一个ETF趋势策略样本。
- 一个回撤分批策略样本。
- 一个网格策略样本。
- 一段含停牌/缺失/异常数据的样本。
- 一段能触发T+1约束的样本。
- 一组违规AI输出样本。
- 一组高风险AI问答样本：现在能买吗、推荐股票、跟哪个策略买、目标价多少。
- 一组带引用AI问答样本：解释回撤、解释财报、解释公告、解释数据冲突。
- 一组多源冲突样本：财报字段冲突、公告发布时间冲突、行情缺失。
- 一组版权状态样本：public_linkable、internal_only、licensed_displayable、unknown_rights。

必须通过：

- 回测可重复。
- 模拟账户计算正确。
- 数据异常不硬生成结论。
- 合规过滤有效。
- 榜单不展示荐股化文案。
- AI问答无引用不输出确定结论。
- 高风险问答必须拒答并引导到风险卡、回测或模拟盘。
- 财报、公告、新闻摘要必须显示来源和发布时间。

## 8. 运营验证就绪

- 已规划10个首批策略卡。
- 已规划4周验证路线。
- 已规划内测价格。
- 已规划核心指标。
- 已规划停止信号。

## 9. 开发前仍需人工确认

这些事项不阻塞MVP开发，但正式上线前建议确认：

- 是否购买Tushare Pro或其他稳定数据源。
- 是否需要法律专业人士审查付费页和免责声明。
- 是否先做网站还是小程序/公众号入口。
- 是否接入支付。
- 是否用真实用户手机号登录，还是先用邮箱/邀请码内测。
