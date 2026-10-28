from typing import Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)
    ts: Optional[str] = Field(None, description="ISO 8601 시각 (생략 시 서버에서 채움)")


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    messages: list[Message] = Field(..., min_length=1)


class ConversationSummary(BaseModel):
    """목록 조회용. messages는 포함하지 않는다 (상세는 GET /api/conversations/{id})."""
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationOut(ConversationSummary):
    messages: list[Message]
