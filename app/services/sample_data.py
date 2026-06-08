from app.models import AnnouncementItem, DataSourceStatus, FinancialSnapshot, SourceRef


SAMPLE_BARS = {
    "510300": [
        ("2026-05-20", 3.82),
        ("2026-05-21", 3.86),
        ("2026-05-22", 3.91),
        ("2026-05-23", 3.88),
        ("2026-05-24", 3.95),
        ("2026-05-27", 4.01),
        ("2026-05-28", 3.98),
        ("2026-05-29", 4.06),
        ("2026-06-03", 4.11),
        ("2026-06-04", 4.08),
        ("2026-06-05", 4.13),
    ],
    "159915": [
        ("2026-05-20", 1.78),
        ("2026-05-21", 1.83),
        ("2026-05-22", 1.89),
        ("2026-05-23", 1.84),
        ("2026-05-24", 1.91),
        ("2026-05-27", 1.96),
        ("2026-05-28", 1.92),
        ("2026-05-29", 1.98),
        ("2026-06-03", 2.05),
        ("2026-06-04", 2.01),
        ("2026-06-05", 2.08),
    ],
    "512880": [
        ("2026-05-20", 0.96),
        ("2026-05-21", 0.97),
        ("2026-05-22", 0.98),
        ("2026-05-23", 0.98),
        ("2026-05-24", 0.99),
        ("2026-05-27", 1.00),
        ("2026-05-28", 0.99),
        ("2026-05-29", 1.01),
        ("2026-06-03", 1.02),
        ("2026-06-04", 1.01),
        ("2026-06-05", 1.03),
    ],
    "518880": [
        ("2026-05-20", 5.12),
        ("2026-05-21", 5.14),
        ("2026-05-22", 5.19),
        ("2026-05-23", 5.18),
        ("2026-05-24", 5.21),
        ("2026-05-27", 5.28),
        ("2026-05-28", 5.24),
        ("2026-05-29", 5.29),
        ("2026-06-03", 5.33),
        ("2026-06-04", 5.31),
        ("2026-06-05", 5.36),
    ],
}


ASSET_NAMES = {
    "510300": "沪深300ETF",
    "159915": "创业板ETF",
    "512880": "证券ETF",
    "518880": "黄金ETF",
    "600000": "浦发银行",
}


ASSET_META = {
    "510300": {
        "name": "沪深300ETF",
        "asset_type": "ETF",
        "market": "CN_A",
        "exchange": "SH",
        "currency": "CNY",
        "tags": ["宽基", "ETF", "沪深300"],
        "summary": "跟踪沪深300指数的宽基ETF，适合放在指数、估值、回撤和成交量框架里观察。",
    },
    "159915": {
        "name": "创业板ETF",
        "asset_type": "ETF",
        "market": "CN_A",
        "exchange": "SZ",
        "currency": "CNY",
        "tags": ["成长", "ETF", "创业板"],
        "summary": "成长风格弹性更高，风险卡应优先解释波动、行业集中和回撤承受能力。",
    },
    "512880": {
        "name": "证券ETF",
        "asset_type": "ETF",
        "market": "CN_A",
        "exchange": "SH",
        "currency": "CNY",
        "tags": ["行业主题", "ETF", "证券"],
        "summary": "行业主题集中度较高，适合和市场情绪、成交量、板块轮动一起观察。",
    },
    "518880": {
        "name": "黄金ETF",
        "asset_type": "ETF",
        "market": "CN_A",
        "exchange": "SH",
        "currency": "CNY",
        "tags": ["商品", "ETF", "避险"],
        "summary": "更多用于组合波动对冲观察，需要结合外部宏观扰动理解风险。",
    },
    "600000": {
        "name": "浦发银行",
        "asset_type": "STOCK",
        "market": "CN_A",
        "exchange": "SH",
        "currency": "CNY",
        "tags": ["银行", "A股", "财报"],
        "summary": "A股个股样本，适合进入财务、公告、K线和风险事件的投研解释链路。",
    },
}


def source_ref(source_name: str = "内置样本数据") -> SourceRef:
    return SourceRef(
        source_name=source_name,
        source_url=None,
        fetched_at="2026-06-07T09:00:00+08:00",
        data_time="2026-06-05",
        quality_status="ok",
        rights_status="internal_sample",
    )


def get_source_statuses() -> list[DataSourceStatus]:
    return [
        DataSourceStatus(
            source_name="内置样本数据",
            tier="P0_sample",
            domains=["stock_bars", "fund", "index", "industry", "financials", "announcements"],
            status="ok",
            last_synced_at="2026-06-07T09:00:00+08:00",
            rights_status="internal_sample",
            display_policy="仅用于MVP演示和测试，不代表真实行情。",
        ),
        DataSourceStatus(
            source_name="AKShare",
            tier="P0_free",
            domains=["stock_bars", "fund", "index", "industry"],
            status="not_configured",
            last_synced_at=None,
            rights_status="public_reference",
            display_policy="后续接入时展示来源和更新时间。",
        ),
        DataSourceStatus(
            source_name="efinance",
            tier="P0_free",
            domains=["stock", "fund", "bond"],
            status="not_configured",
            last_synced_at=None,
            rights_status="public_reference",
            display_policy="作为免费行情备用源。",
        ),
        DataSourceStatus(
            source_name="qstock",
            tier="P0_free",
            domains=["stock", "fund", "visualization"],
            status="not_configured",
            last_synced_at=None,
            rights_status="public_reference",
            display_policy="作为投研数据补充源。",
        ),
        DataSourceStatus(
            source_name="BaoStock",
            tier="P0_free",
            domains=["stock_bars", "index", "financials"],
            status="not_configured",
            last_synced_at=None,
            rights_status="public_reference",
            display_policy="用于A股行情和财务字段交叉校验。",
        ),
        DataSourceStatus(
            source_name="Tushare Pro",
            tier="P1_stable",
            domains=["stock", "fund", "financials", "announcements", "news"],
            status="not_configured",
            last_synced_at=None,
            rights_status="licensed_required",
            display_policy="按授权范围展示。",
        ),
        DataSourceStatus(
            source_name="巨潮资讯/交易所公告",
            tier="P0_public",
            domains=["announcements", "regulatory"],
            status="not_configured",
            last_synced_at=None,
            rights_status="public_linkable",
            display_policy="只展示标题、摘要、链接和发布时间。",
        ),
    ]


def get_financial_snapshot(symbol: str) -> FinancialSnapshot:
    return FinancialSnapshot(
        symbol=symbol,
        market="CN_A",
        latest_period="2026Q1",
        quality_status="ok",
        source=source_ref("内置财报样本"),
        metrics={
            "revenue_yoy": 0.041,
            "net_profit_yoy": -0.018,
            "roe": 0.087,
            "gross_margin": 0.322,
            "debt_ratio": 0.614,
            "operating_cash_flow": 1280000000,
        },
        explanation_boundary="财务数据仅作为风险背景和样本演示，不构成投资建议。",
    )


def get_announcements(symbol: str) -> list[AnnouncementItem]:
    return [
        AnnouncementItem(
            announcement_id=f"ann_{symbol}_001",
            title="2026年第一季度报告",
            announcement_type="periodic_report",
            published_at="2026-04-28T20:00:00+08:00",
            source_name="巨潮资讯样本",
            source_url="https://www.cninfo.com.cn/",
            summary="机器摘要：公司披露一季度收入、利润和现金流数据，需结合财务指标页查看。",
            risk_tags=["periodic_report", "financial_disclosure"],
            rights_status="public_linkable",
        ),
        AnnouncementItem(
            announcement_id=f"ann_{symbol}_002",
            title="关于风险提示事项的公告",
            announcement_type="risk_notice",
            published_at="2026-05-16T19:30:00+08:00",
            source_name="交易所公告样本",
            source_url="https://www.sse.com.cn/",
            summary="机器摘要：该事项仅作为风险背景进入策略复盘，不直接形成交易结论。",
            risk_tags=["risk_notice", "event_background"],
            rights_status="public_linkable",
        ),
    ]
