import json

import firebase_admin
from firebase_admin import credentials, firestore

from core import config
from core.errors import ServiceUnavailableError

_db = None


def _load_credentials() -> credentials.Certificate:
    if config.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            info = json.loads(config.FIREBASE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as e:
            raise ServiceUnavailableError("FIREBASE_SERVICE_ACCOUNT_JSON 형식이 올바르지 않습니다.") from e
        return credentials.Certificate(info)
    if config.FIREBASE_SERVICE_ACCOUNT_PATH:
        return credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_PATH)
    raise ServiceUnavailableError("Firebase 서비스 계정 환경 변수가 설정되지 않았습니다.")


def get_db():
    """Firestore 클라이언트를 처음 사용할 때 초기화한다.

    앱 시작 시점이 아닌 첫 요청 시점에 초기화하므로, 키가 없어도 /docs는 열린다.
    """
    global _db
    if _db is None:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(_load_credentials())
        _db = firestore.client()
    return _db
