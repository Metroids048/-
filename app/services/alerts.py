from itertools import count

from app.models import AlertCreate, AlertRecord
from app.services.safety import compliance_note


_ids = count(1)
_alerts: list[AlertRecord] = []


def create_alert(payload: AlertCreate) -> AlertRecord:
    alert = AlertRecord(
        id=next(_ids),
        symbol=payload.symbol,
        trigger=payload.trigger,
        channel=payload.channel,
        status="active",
        compliance_note=compliance_note(),
    )
    _alerts.append(alert)
    return alert


def list_alerts() -> list[AlertRecord]:
    return list(_alerts)
