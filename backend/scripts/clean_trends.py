"""구글 트렌드 원본 CSV를 (date, value, memo) 형태로 정리한다.

사용법:
    python scripts/clean_trends.py ../time_series_KR_20160101-0000_20261028-1021.csv

- date: "2015-12-01" -> "2015-12" (월 단위)
- value: "<1" 같은 문자열은 0으로 처리
- memo: 최고점/최저점 등 기본 메모를 자동으로 붙인다
"""
import csv
import sys
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "maratang_monthly.csv"


def parse_value(raw: str) -> int:
    raw = raw.strip()
    if raw.startswith("<"):
        return 0
    return int(raw)


def main(src: str) -> None:
    rows = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) < 2:
            raise SystemExit(f"예상과 다른 헤더입니다: {header}")
        for line in reader:
            if len(line) < 2 or not line[0].strip():
                continue
            date = line[0].strip()[:7]  # YYYY-MM
            rows.append({"date": date, "value": parse_value(line[1]), "memo": ""})

    rows.sort(key=lambda r: r["date"])
    peak = max(rows, key=lambda r: r["value"])
    peak["memo"] = "검색 관심도 최고점 (100)"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "value", "memo"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)}개 행 저장 -> {OUT_PATH}")
    print(f"기간: {rows[0]['date']} ~ {rows[-1]['date']}, 최고점: {peak['date']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("사용법: python scripts/clean_trends.py <원본 CSV 경로>")
    main(sys.argv[1])
