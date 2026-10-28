from typing import Optional

from pydantic import BaseModel, Field, field_validator

# 월 단위 데이터이므로 YYYY-MM 형식만 허용
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class DataBase(BaseModel):
    date: str = Field(..., pattern=MONTH_PATTERN, description="월 (YYYY-MM)", examples=["2026-10"])
    value: int = Field(..., ge=0, le=100, description="구글 트렌드 검색 관심도 (0~100)", examples=[72])
    memo: str = Field("", max_length=200, description="메모 (선택)", examples=["가을 시즌"])

    @field_validator("memo")
    @classmethod
    def strip_memo(cls, v: str) -> str:
        return v.strip()


class DataCreate(DataBase):
    pass


class DataUpdate(DataBase):
    pass


class DataOut(DataBase):
    id: str


class Metrics(BaseModel):
    average: float
    max: int
    max_date: str
    min: int
    min_date: str
    latest: int
    latest_date: str
    recent_12m_average: Optional[float] = None
    prev_12m_average: Optional[float] = None
    yoy_change: Optional[str] = Field(None, description="최근 월의 전년 동월 대비 변화")


class SummaryOut(BaseModel):
    period: str
    count: int
    metrics: Optional[Metrics] = None
    trend: str
    peak_season: Optional[str] = Field(None, description="평균 관심도가 가장 높은 달")
    yearly_average: dict[str, float] = Field(default_factory=dict)
    recent_values: list[dict] = Field(default_factory=list, description="최근 12개월 값")
