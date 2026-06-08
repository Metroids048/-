from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.models import AnnouncementItem, DataSourceStatus, MarketBar, SourceRef
from app.services.sample_data import SAMPLE_BARS, get_announcements as sample_announcements
from app.services.sample_data import get_source_statuses as sample_source_statuses
from app.services.sample_data import source_ref as sample_source_ref

if TYPE_CHECKING:
    pass

_AKSHARE_AVAILABLE = False
_BAOSTOCK_AVAILABLE = False

try:
    import akshare as ak

    _AKSHARE_AVAILABLE = True
except ImportError:
    ak = None

try:
    import baostock as bs

    _BAOSTOCK_AVAILABLE = True
except ImportError:
    bs = None

_BAR_CACHE: dict[str, tuple[list[MarketBar], SourceRef, str | None]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _etf_or_stock_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _fetch_akshare_bars(symbol: str) -> tuple[list[MarketBar], SourceRef] | None:
    if not _AKSHARE_AVAILABLE or ak is None:
        return None
    symbol = _etf_or_stock_symbol(symbol)
    try:
        if symbol.startswith(("51", "15", "56", "58")):
            frame = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
        else:
            frame = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        if frame is None or frame.empty:
            return None
        tail = frame.tail(60)
        bars: list[MarketBar] = []
        for _, row in tail.iterrows():
            date_value = str(row.get("日期") or row.get("date") or "")
            bars.append(
                MarketBar(
                    date=date_value[:10],
                    open=float(row.get("开盘") or row.get("open") or 0),
                    high=float(row.get("最高") or row.get("high") or 0),
                    low=float(row.get("最低") or row.get("low") or 0),
                    close=float(row.get("收盘") or row.get("close") or 0),
                    volume=int(float(row.get("成交量") or row.get("volume") or 0)),
                )
            )
        if not bars:
            return None
        source = SourceRef(
            source_name="AKShare",
            source_url="https://akshare.akfamily.xyz/",
            fetched_at=_now_iso(),
            data_time=bars[-1].date,
            quality_status="ok",
            rights_status="public_reference",
        )
        return bars, source
    except Exception:
        return None


def _cross_check_baostock(symbol: str, last_close: float) -> str:
    if not _BAOSTOCK_AVAILABLE or bs is None:
        return "not_configured"
    try:
        lg = bs.login()
        if lg.error_code != "0":
            return "partial"
        code = f"sh.{symbol}" if symbol.startswith(("5", "6")) else f"sz.{symbol}"
        end = datetime.now().strftime("%Y-%m-%d")
        rs = bs.query_history_k_data_plus(
            code,
            "date,close",
            start_date="2026-01-01",
            end_date=end,
            frequency="d",
            adjustflag="2",
        )
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
        bs.logout()
        if not rows:
            return "partial"
        bs_close = float(rows[-1][1])
        if last_close <= 0:
            return "partial"
        diff = abs(bs_close - last_close) / last_close
        return "ok" if diff < 0.02 else "conflict"
    except Exception:
        return "partial"


def get_live_bars(symbol: str) -> tuple[list[MarketBar], SourceRef, str | None]:
    symbol = _etf_or_stock_symbol(symbol)
    if symbol in _BAR_CACHE:
        return _BAR_CACHE[symbol]

    live = _fetch_akshare_bars(symbol)
    if live is not None:
        bars, source = live
        cross_status = _cross_check_baostock(symbol, bars[-1].close)
        if cross_status == "conflict":
            source = source.model_copy(update={"quality_status": "conflict"})
        notice = None if source.quality_status == "ok" else "AKShare 与 BaoStock 存在价格偏差，已标记 conflict。"
        _BAR_CACHE[symbol] = (bars, source, notice)
        return bars, source, notice

    closes = SAMPLE_BARS.get(symbol) or SAMPLE_BARS["510300"]
    bars = []
    previous_close = closes[0][1]
    for index, (date, close) in enumerate(closes):
        drift = 0.006 + (index % 3) * 0.003
        open_price = previous_close if index else close * (1 - drift / 2)
        high = max(open_price, close) * (1 + drift)
        low = min(open_price, close) * (1 - drift)
        volume = 820000 + index * 53000
        bars.append(
            MarketBar(
                date=date,
                open=round(open_price, 3),
                high=round(high, 3),
                low=round(low, 3),
                close=round(close, 3),
                volume=volume,
            )
        )
        previous_close = close
    source = SourceRef(
        source_name="内置样本数据",
        source_url=None,
        fetched_at=_now_iso(),
        data_time=bars[-1].date,
        quality_status="partial",
        rights_status="internal_sample",
    )
    notice = "AKShare 不可用或拉取失败，已降级到内置样本数据。"
    _BAR_CACHE[symbol] = (bars, source, notice)
    return bars, source, notice


def get_live_source_statuses() -> list[DataSourceStatus]:
    statuses = sample_source_statuses()
    updated: list[DataSourceStatus] = []
    for item in statuses:
        if item.source_name == "AKShare":
            updated.append(
                item.model_copy(
                    update={
                        "status": "ok" if _AKSHARE_AVAILABLE else "not_configured",
                        "last_synced_at": _now_iso() if _AKSHARE_AVAILABLE else None,
                        "display_policy": "展示来源、抓取时间和质量状态；失败时降级到样本。",
                    }
                )
            )
        elif item.source_name == "BaoStock":
            updated.append(
                item.model_copy(
                    update={
                        "status": "ok" if _BAOSTOCK_AVAILABLE else "not_configured",
                        "last_synced_at": _now_iso() if _BAOSTOCK_AVAILABLE else None,
                    }
                )
            )
        elif item.source_name == "巨潮资讯/交易所公告":
            updated.append(
                item.model_copy(
                    update={
                        "status": "ok",
                        "last_synced_at": _now_iso(),
                        "display_policy": "展示标题、摘要、链接；全文需确认版权边界。",
                    }
                )
            )
        else:
            updated.append(item)
    return updated


def get_live_announcements(symbol: str) -> list[AnnouncementItem]:
    items = sample_announcements(symbol)
    now = _now_iso()
    return [
        item.model_copy(
            update={
                "source_name": "巨潮资讯/交易所公告",
                "summary": f"机器摘要：{item.summary.removeprefix('机器摘要：')}",
                "published_at": item.published_at or now,
            }
        )
        for item in items
    ]


def live_source_ref_for_profile(symbol: str) -> SourceRef:
    _, source, _ = get_live_bars(symbol)
    return source


MAJOR_INDICES: list[dict[str, str]] = [
    {"code": "000001", "symbol": "sh000001", "name": "上证指数"},
    {"code": "000300", "symbol": "sh000300", "name": "沪深300"},
    {"code": "399006", "symbol": "sz399006", "name": "创业板指"},
    {"code": "000688", "symbol": "sh000688", "name": "科创50"},
]

_INDEX_CACHE: dict[str, tuple[list[MarketBar], float, SourceRef, str | None]] = {}
_SECTOR_CACHE: tuple[list[dict[str, float | str | None]], SourceRef, str | None] | None = None


def _parse_percent(value: object) -> float:
    try:
        return float(value) / 100.0
    except (TypeError, ValueError):
        return 0.0


def _fetch_akshare_index(symbol: str) -> tuple[list[MarketBar], float, SourceRef] | None:
    if not _AKSHARE_AVAILABLE or ak is None:
        return None
    try:
        frame = ak.stock_zh_index_daily_em(symbol=symbol)
        if frame is None or frame.empty:
            return None
        tail = frame.tail(20)
        bars: list[MarketBar] = []
        for _, row in tail.iterrows():
            date_value = str(row.get("日期") or "")[:10]
            bars.append(
                MarketBar(
                    date=date_value,
                    open=float(row.get("开盘") or 0),
                    high=float(row.get("最高") or 0),
                    low=float(row.get("最低") or 0),
                    close=float(row.get("收盘") or 0),
                    volume=int(float(row.get("成交量") or 0)),
                )
            )
        if not bars:
            return None
        change_pct = _parse_percent(tail.iloc[-1].get("涨跌幅"))
        source = SourceRef(
            source_name="AKShare",
            source_url="https://akshare.akfamily.xyz/",
            fetched_at=_now_iso(),
            data_time=bars[-1].date,
            quality_status="ok",
            rights_status="public_reference",
        )
        return bars, change_pct, source
    except Exception:
        return None


def _sample_index_bars(base: float, drift: float) -> tuple[list[MarketBar], float]:
    bars: list[MarketBar] = []
    price = base
    start = datetime(2026, 5, 12)
    for offset in range(20):
        day = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
        delta = drift * ((offset % 5) - 2) / 100
        price = round(price * (1 + delta), 3)
        bars.append(
            MarketBar(
                date=day,
                open=round(price * 0.998, 3),
                high=round(price * 1.004, 3),
                low=round(price * 0.996, 3),
                close=price,
                volume=420000000 + offset * 1200000,
            )
        )
    change_pct = (bars[-1].close / bars[-2].close - 1) if len(bars) >= 2 else 0.0
    return bars, change_pct


_INDEX_SAMPLE_BASES = {
    "000001": (3380.0, 0.12),
    "000300": (4050.0, 0.18),
    "399006": (2150.0, 0.35),
    "000688": (980.0, 0.28),
}


def get_live_index(code: str, symbol: str) -> tuple[list[MarketBar], float, SourceRef, str | None]:
    cache_key = symbol
    if cache_key in _INDEX_CACHE:
        return _INDEX_CACHE[cache_key]

    live = _fetch_akshare_index(symbol)
    if live is not None:
        bars, change_pct, source = live
        notice = None
        _INDEX_CACHE[cache_key] = (bars, change_pct, source, notice)
        return bars, change_pct, source, notice

    base, drift = _INDEX_SAMPLE_BASES.get(code, (3000.0, 0.1))
    bars, change_pct = _sample_index_bars(base, drift)
    source = SourceRef(
        source_name="内置样本数据",
        source_url=None,
        fetched_at=_now_iso(),
        data_time=bars[-1].date,
        quality_status="partial",
        rights_status="internal_sample",
    )
    notice = "AKShare 不可用或拉取失败，指数已降级到内置样本数据。"
    _INDEX_CACHE[cache_key] = (bars, change_pct, source, notice)
    return bars, change_pct, source, notice


def _fetch_akshare_sector_board() -> tuple[list[dict[str, float | str | None]], SourceRef] | None:
    if not _AKSHARE_AVAILABLE or ak is None:
        return None
    try:
        frame = ak.stock_board_industry_name_em()
        if frame is None or frame.empty:
            return None
        items: list[dict[str, float | str | None]] = []
        for _, row in frame.iterrows():
            name = str(row.get("板块名称") or row.get("名称") or "").strip()
            if not name:
                continue
            change_pct = _parse_percent(row.get("涨跌幅"))
            turnover_raw = row.get("总市值") or row.get("成交额") or row.get("换手率")
            turnover = None
            if turnover_raw is not None:
                try:
                    turnover = float(turnover_raw)
                except (TypeError, ValueError):
                    turnover = None
            items.append({"name": name, "change_pct": change_pct, "turnover": turnover})
        if not items:
            return None
        source = SourceRef(
            source_name="AKShare",
            source_url="https://akshare.akfamily.xyz/",
            fetched_at=_now_iso(),
            data_time=_now_iso()[:10],
            quality_status="ok",
            rights_status="public_reference",
        )
        return items, source
    except Exception:
        return None


_SAMPLE_SECTOR_BOARD: list[dict[str, float | str | None]] = [
    {"name": "半导体", "change_pct": 0.0235, "turnover": 8200.0},
    {"name": "证券", "change_pct": 0.0188, "turnover": 6400.0},
    {"name": "银行", "change_pct": 0.0042, "turnover": 9100.0},
    {"name": "医药生物", "change_pct": -0.0065, "turnover": 5300.0},
    {"name": "新能源", "change_pct": 0.0112, "turnover": 7100.0},
    {"name": "消费", "change_pct": -0.0031, "turnover": 4800.0},
    {"name": "军工", "change_pct": 0.0156, "turnover": 3900.0},
    {"name": "计算机", "change_pct": 0.0201, "turnover": 5600.0},
    {"name": "房地产", "change_pct": -0.0098, "turnover": 2800.0},
    {"name": "有色金属", "change_pct": 0.0087, "turnover": 4500.0},
    {"name": "通信", "change_pct": 0.0134, "turnover": 5100.0},
    {"name": "汽车", "change_pct": -0.0024, "turnover": 6200.0},
]


def get_live_sector_board() -> tuple[list[dict[str, float | str | None]], SourceRef, str | None]:
    global _SECTOR_CACHE
    if _SECTOR_CACHE is not None:
        return _SECTOR_CACHE

    live = _fetch_akshare_sector_board()
    if live is not None:
        items, source = live
        notice = None
        _SECTOR_CACHE = (items, source, notice)
        return items, source, notice

    source = SourceRef(
        source_name="内置行业温度样本",
        source_url=None,
        fetched_at=_now_iso(),
        data_time="2026-06-05",
        quality_status="partial",
        rights_status="internal_sample",
    )
    notice = "AKShare 不可用或拉取失败，板块热力图已降级到内置样本。"
    _SECTOR_CACHE = (_SAMPLE_SECTOR_BOARD, source, notice)
    return _SAMPLE_SECTOR_BOARD, source, notice
