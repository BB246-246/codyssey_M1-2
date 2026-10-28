from fastapi import APIRouter, status

from schemas.data import DataCreate, DataOut, DataUpdate, SummaryOut
from services import data_service

router = APIRouter(prefix="/api/data", tags=["data"])


# /summary를 /{id}보다 먼저 선언해야 "summary"가 id로 잡히지 않는다
@router.get("/summary", response_model=SummaryOut, summary="데이터 요약 (프롬프트 주입용)")
def get_summary():
    return data_service.get_summary()


@router.get("", response_model=list[DataOut], summary="데이터 목록 조회 (date 오름차순)")
def list_data():
    return data_service.list_data()


@router.post("", response_model=DataOut, status_code=status.HTTP_201_CREATED, summary="데이터 추가")
def create_data(body: DataCreate):
    return data_service.create_data(body.model_dump())


@router.put("/{data_id}", response_model=DataOut, summary="데이터 수정")
def update_data(data_id: str, body: DataUpdate):
    return data_service.update_data(data_id, body.model_dump())


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT, summary="데이터 삭제")
def delete_data(data_id: str):
    data_service.delete_data(data_id)
