from itertools import count

from app.models import WatchlistCreate, WatchlistRecord, WatchlistResponse
from app.services.sample_data import ASSET_NAMES
from app.services.safety import compliance_note


_ids = count(1)
_items: list[WatchlistRecord] = [
    WatchlistRecord(
        id=0,
        symbol="510300",
        name=ASSET_NAMES["510300"],
        note="观察宽基ETF回撤、成交量和风险卡变化。",
        source="seed",
        status="observing",
        added_at="2026-06-07T09:00:00+08:00",
        compliance_note=compliance_note(),
    )
]


def create_watchlist_item(payload: WatchlistCreate) -> WatchlistRecord:
    record = WatchlistRecord(
        id=next(_ids),
        symbol=payload.symbol,
        name=ASSET_NAMES.get(payload.symbol, "观察标的"),
        note=payload.note,
        source=payload.source,
        status="observing",
        added_at="2026-06-07T09:30:00+08:00",
        compliance_note=compliance_note(),
    )
    _items.append(record)
    return record


def list_watchlist() -> WatchlistResponse:
    return WatchlistResponse(items=list(_items))
