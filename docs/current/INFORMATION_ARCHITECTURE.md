# INFORMATION_ARCHITECTURE.md

## 首页目标

首页必须让新用户在 10 秒内理解：这是一个投资想法体检工具，不是荐股工具。

## 允许出现在首页的内容

1. Hero：产品定位 + 合规边界
2. Main CTA：生成想法体检卡
3. Idea Input Panel：投资想法输入
4. Diagnosis Card：想法类型 + 情绪标签 + 体检结论 + 虚拟样本 badge
5. Historical Replay：虚拟样本回放
6. Risk Examples：风险反例 + 小白提醒
7. Trending Ideas：今日热点体检榜
8. Content Generator：分享标题 / 正文 / 短视频脚本
9. Compliance Footer：合规声明

## 不允许堆在首页的内容

- 数据源详情
- 知识库详情
- 风险卡详情
- 市场解释详情
- Ask Alpha 完整问答
- 策略工厂、回测、模拟盘、榜单
- 商业化说明
- 多市场扩展说明

## 前端状态要求

- 每个异步区块必须有 loading 状态。
- 每个异步区块必须有 empty 状态。
- 每个异步区块必须有 error 状态。
- API 失败时显式报错，不允许静默 fallback 假数据。
- 移动端必须单列可读。

## 主要 DOM 区块

- `hero`
- `ideaInputPanel`
- `diagnosisCard`
- `historicalReplay`
- `riskExamples`
- `trendingIdeas`
- `contentGenerator`
- `complianceFooter`

## 必要 DOM id

- `ideaInput`
- `diagnoseIdea`
- `diagnosisCard`
- `ideaType`
- `emotionTag`
- `diagnosisSummary`
- `historicalReplay`
- `replayTypeBadge`
- `riskFlagList`
- `failureCaseList`
- `xiaobaiReminder`
- `trendingIdeaList`
- `contentGenerator`
- `generateShareContent`
- `shareTitleList`
- `shortVideoScript`
- `shareBody`
- `copyShareContent`
- `pageState`
