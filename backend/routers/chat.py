from typing import Annotated

from fastapi import APIRouter, Body

from schemas.chat import ChatRequest, ChatResponse
from services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Swagger 기본 예시는 conversation_id에 "string"을 채워 404가 나므로 예시를 직접 지정
CHAT_EXAMPLES = {
    "new": {
        "summary": "새 대화 시작",
        "value": {"message": "요즘 마라탕 인기가 어때?"},
    },
    "continue": {
        "summary": "기존 대화 이어가기",
        "description": "conversation_id에 이전 응답의 conversation_id를 넣는다.",
        "value": {"message": "그럼 가장 인기 많았던 때는?", "conversation_id": "<이전 응답의 id>"},
    },
}


@router.post("", response_model=ChatResponse, summary="데이터 요약 기반 AI 대화 (자동 저장)")
def chat(body: Annotated[ChatRequest, Body(openapi_examples=CHAT_EXAMPLES)]):
    return chat_service.chat(body.message, body.conversation_id)
