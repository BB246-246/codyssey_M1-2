from datetime import datetime, timezone

from core import config
from core.errors import ConflictError, NotFoundError
from core.firebase import get_db
from services.summary_service import compute_summary


def _col():
    return get_db().collection(config.DATA_COLLECTION)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_dict(doc) -> dict:
    d = doc.to_dict()
    return {"id": doc.id, "date": d["date"], "value": d["value"], "memo": d.get("memo", "")}


def _ensure_unique_date(date: str, exclude_id: str | None = None) -> None:
    for doc in _col().where("date", "==", date).limit(2).stream():
        if doc.id != exclude_id:
            raise ConflictError(f"{date} 데이터가 이미 존재합니다.")


def list_data() -> list[dict]:
    return [_to_dict(doc) for doc in _col().order_by("date").stream()]


def create_data(payload: dict) -> dict:
    _ensure_unique_date(payload["date"])
    now = _now()
    _, ref = _col().add({**payload, "created_at": now, "updated_at": now})
    return {"id": ref.id, **payload}


def update_data(data_id: str, payload: dict) -> dict:
    ref = _col().document(data_id)
    if not ref.get().exists:
        raise NotFoundError(f"id={data_id} 데이터를 찾을 수 없습니다.")
    _ensure_unique_date(payload["date"], exclude_id=data_id)
    ref.update({**payload, "updated_at": _now()})
    return {"id": data_id, **payload}


def delete_data(data_id: str) -> None:
    ref = _col().document(data_id)
    if not ref.get().exists:
        raise NotFoundError(f"id={data_id} 데이터를 찾을 수 없습니다.")
    ref.delete()


def get_summary() -> dict:
    return compute_summary(list_data())
