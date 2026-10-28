import json

import anthropic

from core import config
from core.errors import ServiceUnavailableError, UpstreamError
from services import conversation_service, data_service

SYSTEM_PROMPT_TEMPLATE = """당신은 '마라탕' 검색 트렌드 데이터를 분석해 주는 데이터 분석 비서입니다.
데이터는 구글 트렌드(대한민국)의 월별 검색 관심도이며, 0~100 사이의 상대 지수입니다.
(100 = 기간 중 검색량이 가장 많았던 달, 실제 검색 횟수가 아님)

[사용자 데이터 요약]
- 데이터 기간: {period}
- 총 레코드: {count}개
- 주요 지표: {metrics}
- 최근 트렌드: {trend}
- 관심도가 높은 달: {peak_season}
- 연도별 평균: {yearly_average}
- 최근 12개월 값: {recent_values}

규칙:
- 위 데이터를 근거로 구체적인 숫자를 들어 한국어로 간결하게 답변하세요.
- 데이터에 없는 내용(실제 매출, 원인 등)은 추측임을 밝히세요.
- 데이터와 무관한 질문에는 짧게 답하고 데이터 관련 질문을 유도하세요."""


def build_system_prompt(summary: dict) -> str:
    """컨텍스트 주입: /api/data/summary 결과를 시스템 프롬프트에 끼워 넣는다."""
    def dump(v):
        return json.dumps(v, ensure_ascii=False)

    return SYSTEM_PROMPT_TEMPLATE.format(
        period=summary.get("period", "-"),
        count=summary.get("count", 0),
        metrics=dump(summary.get("metrics")),
        trend=summary.get("trend", "-"),
        peak_season=summary.get("peak_season", "-"),
        yearly_average=dump(summary.get("yearly_average", {})),
        recent_values=dump(summary.get("recent_values", [])),
    )


def _ask_claude(system: str, messages: list[dict]) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ServiceUnavailableError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    client = anthropic.Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
        base_url=config.ANTHROPIC_BASE_URL,
        timeout=30,
    )
    try:
        res = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.ANTHROPIC_MAX_TOKENS,
            system=system,
            messages=messages,
        )
    except anthropic.AuthenticationError as e:
        raise ServiceUnavailableError("ANTHROPIC_API_KEY가 올바르지 않습니다.") from e
    except anthropic.NotFoundError as e:
        raise ServiceUnavailableError(f"모델 '{config.ANTHROPIC_MODEL}'을 찾을 수 없습니다.") from e
    except anthropic.RateLimitError as e:
        raise UpstreamError("AI 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.") from e
    except anthropic.APIStatusError as e:
        raise UpstreamError(f"AI 응답 생성에 실패했습니다 (status {e.status_code}).") from e
    except anthropic.APIConnectionError as e:
        raise UpstreamError("AI 서버에 연결하지 못했습니다.") from e

    if res.stop_reason == "refusal":
        return "죄송해요, 이 요청에는 답변할 수 없어요. 데이터에 관한 다른 질문을 해 주세요."
    text = "".join(b.text for b in res.content if b.type == "text").strip()
    if res.stop_reason == "max_tokens":
        text += "\n\n(답변이 길어 일부가 잘렸어요.)"
    return text


def chat(message: str, conversation_id: str | None = None) -> dict:
    # 1) 데이터 요약 조회
    summary = data_service.get_summary()

    # 2) 요약을 시스템 프롬프트에 삽입 (+ 이어지는 대화면 최근 히스토리 포함)
    history = []
    if conversation_id:
        conv = conversation_service.get_conversation(conversation_id)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in conv["messages"][-config.CHAT_HISTORY_LIMIT:]
        ]
    # Claude API는 system을 messages가 아닌 별도 파라미터로 받는다
    system = build_system_prompt(summary)
    messages = [*history, {"role": "user", "content": message}]

    # 3) Claude 호출
    reply = _ask_claude(system, messages)

    # 4) 대화 자동 저장
    new_messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    if conversation_id:
        conversation_service.append_messages(conversation_id, new_messages)
    else:
        conversation_id = conversation_service.create_conversation(new_messages)["id"]

    return {"conversation_id": conversation_id, "reply": reply}
