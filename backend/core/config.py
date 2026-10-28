import os

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# 비워두면 Anthropic 공식 API, 과정 프록시를 쓰면 그 주소
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "") or None
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "500"))

# 둘 중 하나만 설정하면 된다. 배포 환경(Render)에서는 JSON 문자열 방식을 권장.
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")

ALLOWED_ORIGINS = _split_csv(
    os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
)

# 채팅 시 AI에 함께 보낼 이전 메시지 개수 (토큰 절약)
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "10"))

DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"
