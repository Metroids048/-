from pydantic import BaseModel


class SourceMeta(BaseModel):
    source_name: str
    source_url: str | None = None
    fetched_at: str
    data_time: str | None = None
    rights_status: str


class SourceStatus(BaseModel):
    source_name: str
    tier: str
    domains: list[str]
    quality_status: str
    last_synced_at: str | None = None
    rights_status: str
    display_policy: str


class DailyBars(BaseModel):
    symbol: str
    market: str
    bars: list[dict[str, float | str | int]]
    quality_status: str
    source: SourceMeta


class FinancialSnapshot(BaseModel):
    symbol: str
    latest_period: str
    quality_status: str
    metrics: dict[str, float | int]
    source: SourceMeta


class Announcements(BaseModel):
    symbol: str
    items: list[dict[str, str | list[str]]]
