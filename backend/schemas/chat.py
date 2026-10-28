from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, examples=["요즘 마라탕 인기가 어때?"])
    conversation_id: Optional[str] = Field(None, description="이어서 대화할 경우 기존 대화 id")

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("메시지가 비어 있습니다.")
        return v

    @field_validator("conversation_id")
    @classmethod
    def blank_to_none(cls, v: Optional[str]) -> Optional[str]:
        # 빈 문자열은 "새 대화"로 취급
        return v.strip() or None if v else None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
