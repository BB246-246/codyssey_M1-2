"""시계열 데이터 -> 요약 정보 계산 (DB와 무관한 순수 함수)."""
from collections import defaultdict
from statistics import mean

# 최근 12개월 평균이 직전 12개월 대비 이 비율 이상 변하면 상승/하락으로 본다
TREND_THRESHOLD_PCT = 5.0


def _pct_change(new: float, old: float) -> float | None:
    if old == 0:
        return None
    return (new - old) / old * 100


def _trend_label(records: list[dict]) -> tuple[str, float | None, float | None]:
    values = [r["value"] for r in records]
    if len(values) < 24:
        return "판단 불가 (데이터 24개월 미만)", None, None

    recent = mean(values[-12:])
    prev = mean(values[-24:-12])
    change = _pct_change(recent, prev)
    if change is None:
        return "상승 (직전 12개월 관심도 0)", round(recent, 1), round(prev, 1)

    if change >= TREND_THRESHOLD_PCT:
        label = "상승"
    elif change <= -TREND_THRESHOLD_PCT:
        label = "하락"
    else:
        label = "유지"

    # 단기 흐름(최근 3개월 vs 직전 3개월)도 같이 보여준다
    short = _pct_change(mean(values[-3:]), mean(values[-6:-3]))
    short_text = f", 최근 3개월 {short:+.1f}%" if short is not None else ""
    return (
        f"{label} (최근 12개월 평균 {recent:.1f}, 직전 12개월 대비 {change:+.1f}%{short_text})",
        round(recent, 1),
        round(prev, 1),
    )


def _yoy(records: list[dict]) -> str | None:
    latest = records[-1]
    year, month = latest["date"].split("-")
    target = f"{int(year) - 1}-{month}"
    prev = next((r for r in records if r["date"] == target), None)
    if prev is None:
        return None
    change = _pct_change(latest["value"], prev["value"])
    if change is None:
        return f"{target} {prev['value']} -> {latest['date']} {latest['value']}"
    return f"{target} {prev['value']} -> {latest['date']} {latest['value']} ({change:+.1f}%)"


def _peak_season(records: list[dict]) -> str:
    # 관심도가 낮던 초기 구간이 왜곡하지 않도록 최근 5년(60개월)만 사용
    by_month = defaultdict(list)
    for r in records[-60:]:
        by_month[r["date"][5:7]].append(r["value"])
    avg = {m: mean(v) for m, v in by_month.items()}
    top = sorted(avg.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return ", ".join(f"{int(m)}월({v:.1f})" for m, v in top) + " (최근 5년 월별 평균 기준)"


def compute_summary(records: list[dict]) -> dict:
    """records: [{"date": "YYYY-MM", "value": int, ...}, ...]"""
    if not records:
        return {"period": "-", "count": 0, "metrics": None, "trend": "데이터 없음"}

    records = sorted(records, key=lambda r: r["date"])
    values = [r["value"] for r in records]
    max_r = max(records, key=lambda r: r["value"])
    min_r = min(records, key=lambda r: r["value"])
    trend, recent_avg, prev_avg = _trend_label(records)

    yearly = defaultdict(list)
    for r in records:
        yearly[r["date"][:4]].append(r["value"])

    return {
        "period": f"{records[0]['date']} ~ {records[-1]['date']}",
        "count": len(records),
        "metrics": {
            "average": round(mean(values), 1),
            "max": max_r["value"],
            "max_date": max_r["date"],
            "min": min_r["value"],
            "min_date": min_r["date"],
            "latest": records[-1]["value"],
            "latest_date": records[-1]["date"],
            "recent_12m_average": recent_avg,
            "prev_12m_average": prev_avg,
            "yoy_change": _yoy(records),
        },
        "trend": trend,
        "peak_season": _peak_season(records),
        "yearly_average": {y: round(mean(v), 1) for y, v in sorted(yearly.items())},
        "recent_values": [{"date": r["date"], "value": r["value"]} for r in records[-12:]],
    }
