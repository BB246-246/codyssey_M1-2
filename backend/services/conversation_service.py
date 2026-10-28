from datetime import datetime, timezone

from firebase_admin import firestore

from core import config
from core.errors import NotFoundError
from core.firebase import get_db

TITLE_MAX = 30


def _col():
    return get_db().collection(config.CONVERSATIONS_COLLECTION)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_title(messages: list[dict]) -> str:
    first_user = next((m["content"] for m in messages if m["role"] == "user"), "새 대화")
    first_user = first_user.replace("\n", " ").strip()
    return first_user[:TITLE_MAX] + ("…" if len(first_user) > TITLE_MAX else "")


def _fill_ts(messages: list[dict]) -> list[dict]:
    now = now_iso()
    return [{**m, "ts": m.get("ts") or now} for m in messages]


def _summary(doc_id: str, d: dict) -> dict:
    return {
        "id": doc_id,
        "title": d.get("title", ""),
        "message_count": len(d.get("messages", [])),
        "created_at": d.get("created_at", ""),
        "updated_at": d.get("updated_at", ""),
    }


def create_conversation(messages: list[dict], title: str | None = None) -> dict:
    messages = _fill_ts(messages)
    now = now_iso()
    data = {
        "title": title or _make_title(messages),
        "messages": messages,
        "created_at": now,
        "updated_at": now,
    }
    _, ref = _col().add(data)
    return {**_summary(ref.id, data), "messages": messages}


def list_conversations() -> list[dict]:
    query = _col().order_by("updated_at", direction=firestore.Query.DESCENDING)
    return [_summary(doc.id, doc.to_dict()) for doc in query.stream()]


def get_conversation(conv_id: str) -> dict:
    doc = _col().document(conv_id).get()
    if not doc.exists:
        raise NotFoundError(f"id={conv_id} 대화를 찾을 수 없습니다.")
    d = doc.to_dict()
    return {**_summary(doc.id, d), "messages": d.get("messages", [])}


def append_messages(conv_id: str, messages: list[dict]) -> None:
    ref = _col().document(conv_id)
    if not ref.get().exists:
        raise NotFoundError(f"id={conv_id} 대화를 찾을 수 없습니다.")
    ref.update({
        "messages": firestore.ArrayUnion(_fill_ts(messages)),
        "updated_at": now_iso(),
    })


def delete_conversation(conv_id: str) -> None:
    ref = _col().document(conv_id)
    if not ref.get().exists:
        raise NotFoundError(f"id={conv_id} 대화를 찾을 수 없습니다.")
    ref.delete()
