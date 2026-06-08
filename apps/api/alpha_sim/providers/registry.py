from dataclasses import dataclass

from apps.api.alpha_sim.providers.contracts import (
    Announcements,
    DailyBars,
    FinancialSnapshot,
    SourceMeta,
    SourceStatus,
)


def _source(source_name: str, rights_status: str = "public_reference", source_url: str | None = None) -> SourceMeta:
    return SourceMeta(
        source_name=source_name,
        source_url=source_url,
        fetched_at="2026-06-07T09:00:00+08:00",
        data_time="2026-06-05",
        rights_status=rights_status,
    )


class MarketDataProvider:
    def daily_bars(self, symbol: str) -> DailyBars:
        closes = {
            "510300": [3.82, 3.86, 3.91, 3.88, 3.95, 4.01, 3.98, 4.06, 4.11, 4.08, 4.13],
            "159915": [1.78, 1.83, 1.89, 1.84, 1.91, 1.96, 1.92, 1.98, 2.05, 2.01, 2.08],
            "512880": [0.96, 0.97, 0.98, 0.98, 0.99, 1.0, 0.99, 1.01, 1.02, 1.01, 1.03],
        }.get(symbol, [3.82, 3.86, 3.91, 3.88, 3.95, 4.01, 3.98, 4.06, 4.11, 4.08, 4.13])
        dates = [
            "2026-05-20",
            "2026-05-21",
            "2026-05-22",
            "2026-05-23",
            "2026-05-24",
            "2026-05-27",
            "2026-05-28",
            "2026-05-29",
            "2026-06-03",
            "2026-06-04",
            "2026-06-05",
        ]
        bars = [
            {
                "date": date,
                "open": close,
                "high": round(close * 1.01, 4),
                "low": round(close * 0.99, 4),
                "close": close,
                "volume": 1000000 + index * 25000,
            }
            for index, (date, close) in enumerate(zip(dates, closes))
        ]
        return DailyBars(symbol=symbol, market="CN_A_ETF", bars=bars, quality_status="ok", source=_source("AKShare"))

    def trading_calendar(self, month: str) -> dict[str, str | list[str]]:
        return {
            "market": "CN_A",
            "month": month,
            "quality_status": "ok",
            "trading_days": ["2026-06-03", "2026-06-04", "2026-06-05"],
            "source_name": "交易所公开日历样本",
        }


class PublicInformationProvider:
    def financial_snapshot(self, symbol: str) -> FinancialSnapshot:
        return FinancialSnapshot(
            symbol=symbol,
            latest_period="2026Q1",
            quality_status="ok",
            metrics={
                "revenue_yoy": 0.041,
                "net_profit_yoy": -0.018,
                "roe": 0.087,
                "debt_ratio": 0.614,
                "operating_cash_flow": 1280000000,
            },
            source=_source("BaoStock", source_url="https://baostock.com/"),
        )

    def announcements(self, symbol: str) -> Announcements:
        return Announcements(
            symbol=symbol,
            items=[
                {
                    "announcement_id": f"ann_{symbol}_001",
                    "title": "2026年第一季度报告",
                    "announcement_type": "periodic_report",
                    "published_at": "2026-04-28T20:00:00+08:00",
                    "source_name": "巨潮资讯样本",
                    "source_url": "https://www.cninfo.com.cn/",
                    "summary": "机器摘要：公司披露一季度收入、利润和现金流数据，需结合财务指标页查看。",
                    "risk_tags": ["periodic_report", "financial_disclosure"],
                }
            ],
        )

    def regulatory_items(self) -> list[dict[str, str]]:
        return [
            {
                "item_id": "reg_no_advice_001",
                "title": "非投资建议与虚拟模拟边界",
                "source_name": "监管公开信息样本",
                "source_url": "https://www.csrc.gov.cn/",
                "summary": "产品只展示虚拟模拟表现，不提供买卖建议、目标价、跟单或自动下单。",
            }
        ]


@dataclass
class DataProviderRegistry:
    market: MarketDataProvider
    public_info: PublicInformationProvider

    def statuses(self) -> list[SourceStatus]:
        return [
            SourceStatus(
                source_name="AKShare",
                tier="P0_free",
                domains=["stock_bars", "fund", "index", "industry"],
                quality_status="ok",
                last_synced_at="2026-06-07T09:00:00+08:00",
                rights_status="public_reference",
                display_policy="展示来源、更新时间和质量状态。",
            ),
            SourceStatus(
                source_name="efinance",
                tier="P0_free",
                domains=["stock", "fund", "bond"],
                quality_status="not_configured",
                rights_status="public_reference",
                display_policy="免费行情备用源，接入后展示来源和更新时间。",
            ),
            SourceStatus(
                source_name="qstock",
                tier="P0_free",
                domains=["stock", "fund", "visualization"],
                quality_status="not_configured",
                rights_status="public_reference",
                display_policy="投研数据补充源，接入后展示字段口径。",
            ),
            SourceStatus(
                source_name="BaoStock",
                tier="P0_free",
                domains=["stock_bars", "index", "financials"],
                quality_status="ok",
                last_synced_at="2026-06-07T09:00:00+08:00",
                rights_status="public_reference",
                display_policy="用于A股行情和财务字段交叉校验。",
            ),
            SourceStatus(
                source_name="巨潮资讯/交易所公告",
                tier="P0_public",
                domains=["announcements", "regulatory"],
                quality_status="ok",
                last_synced_at="2026-06-07T09:00:00+08:00",
                rights_status="public_linkable",
                display_policy="只展示标题、机器摘要、链接和发布时间。",
            ),
            SourceStatus(
                source_name="监管公开信息",
                tier="P0_public",
                domains=["compliance", "regulatory"],
                quality_status="ok",
                last_synced_at="2026-06-07T09:00:00+08:00",
                rights_status="public_linkable",
                display_policy="用于合规词库和知识库引用。",
            ),
            SourceStatus(
                source_name="Tushare Pro",
                tier="P1_stable",
                domains=["stock", "fund", "financials", "announcements", "news"],
                quality_status="not_configured",
                rights_status="licensed_required",
                display_policy="验证付费和留存后按授权范围接入。",
            ),
        ]


def build_default_registry() -> DataProviderRegistry:
    return DataProviderRegistry(market=MarketDataProvider(), public_info=PublicInformationProvider())
