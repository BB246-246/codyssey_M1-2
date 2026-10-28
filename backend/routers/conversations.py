from fastapi import APIRouter, status

from schemas.conversation import ConversationCreate, ConversationOut, ConversationSummary
from services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED, summary="대화 저장")
def create_conversation(body: ConversationCreate):
    messages = [m.model_dump() for m in body.messages]
    return conversation_service.create_conversation(messages, body.title)


@router.get("", response_model=list[ConversationSummary], summary="대화 목록 조회 (messages 미포함, 최신순)")
def list_conversations():
    return conversation_service.list_conversations()


@router.get("/{conv_id}", response_model=ConversationOut, summary="특정 대화 전체 messages 조회")
def get_conversation(conv_id: str):
    return conversation_service.get_conversation(conv_id)


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT, summary="대화 삭제")
def delete_conversation(conv_id: str):
    conversation_service.delete_conversation(conv_id)
