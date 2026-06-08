from datetime import datetime, timezone
from itertools import count

from app.models import JournalCreate, JournalRecord


_ids = count(1)
_records: list[JournalRecord] = []


def create_journal(payload: JournalCreate) -> JournalRecord:
    record = JournalRecord(
        id=next(_ids),
        created_at=datetime.now(timezone.utc).isoformat(),
        symbol=payload.symbol,
        observation=payload.observation,
        action=payload.action,
        outcome=payload.outcome,
        reflection_prompt="这次记录里，哪些判断来自规则证据，哪些来自主观情绪？",
    )
    _records.append(record)
    return record


def list_journal() -> list[JournalRecord]:
    return list(_records)
