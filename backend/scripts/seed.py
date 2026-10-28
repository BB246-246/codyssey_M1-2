"""정리된 CSV(data/maratang_monthly.csv)를 Firestore `data` 컬렉션에 업로드한다.

사용법 (backend 폴더에서):
    python -m scripts.seed           # 이미 있는 date는 건너뜀 (여러 번 실행해도 안전)
    python -m scripts.seed --reset   # data 컬렉션을 비우고 다시 업로드
"""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from core import config
from core.firebase import get_db
from schemas.data import DataCreate

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "maratang_monthly.csv"
BATCH_SIZE = 400  # Firestore 배치 한도 500 미만


def load_rows() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        # Pydantic 스키마로 한 번 더 검증해서 잘못된 행이 DB에 들어가지 않게 한다
        return [DataCreate(**{**r, "value": int(r["value"])}).model_dump() for r in csv.DictReader(f)]


def main(reset: bool) -> None:
    col = get_db().collection(config.DATA_COLLECTION)

    if reset:
        deleted = 0
        for doc in col.stream():
            doc.reference.delete()
            deleted += 1
        print(f"기존 문서 {deleted}개 삭제")

    existing = {doc.to_dict().get("date") for doc in col.stream()}
    rows = [r for r in load_rows() if r["date"] not in existing]

    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    for i in range(0, len(rows), BATCH_SIZE):
        batch = db.batch()
        for r in rows[i:i + BATCH_SIZE]:
            batch.set(col.document(), {**r, "created_at": now, "updated_at": now})
        batch.commit()

    print(f"업로드 {len(rows)}개, 건너뜀 {len(existing)}개")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="기존 data 컬렉션 삭제 후 업로드")
    main(parser.parse_args().reset)
