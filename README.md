# AI投资想法体检器

看到热点想买？先让 AI 体检一下。

## 当前定位

这是一个流量型财经内容工具，不是荐股工具、不是实盘交易工具、不是量化交易平台。

## 当前 P0 用户路径

输入投资想法
→ AI 识别想法类型
→ 生成虚拟样本回放
→ 生成风险反例
→ 生成小白提醒
→ 生成分享内容

## 启动方式

一条命令启动 API 与静态首页：

```powershell
Set-Location "c:\Users\Windows11\Desktop\量化项目"
py -3 -m pip install -r requirements.txt
py -3 -m uvicorn apps.api.alpha_sim.main:app --reload --port 8000
```

- 产品主页：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

## 当前维护范围

| 路径 | 作用 |
|------|------|
| `apps/api/alpha_sim/` | 统一 API（路由 + SQLite 持久化） |
| `app/static/` | **当前唯一 P0 用户入口**（FastAPI 根路径 `/` 提供） |
| `app/services/idea_diagnosis.py` | 想法体检服务 |
| `app/services/trending_ideas.py` | 热点体检榜 |
| `app/services/share_content.py` | 分享内容生成 |
| `app/services/compliance_guard.py` | 合规过滤 |
| `app/services/alpha_signal_adapter.py` | 本地 Alpha 概念转体检维度（后台） |

## 当前 P0 API

- `GET /api/content/home`
- `POST /api/ideas/diagnose`
- `GET /api/ideas/trending`
- `POST /api/content/share-card`

## 暂停范围（P1/P2，不参与当前 MVP）

- `apps/web` Next.js 完整前端
- 策略工厂、回测、模拟盘、7天观察
- 策略榜单、K线、研报
- 风险卡、Ask Alpha、知识库、数据源透明
- 真实交易、券商接入、商业化支付

以上能力可在后端保留为降级接口，但不得作为首页主体验。

## 测试

```powershell
py -3 -m pytest tests/ -q
```

## 合规边界

- 仅用于投资想法复盘、虚拟样本回放和内容生成
- 不接真实资金、不接券商、不自动下单、不提供跟单
- 不构成投资建议、不承诺收益、不输出买卖指令与目标价
