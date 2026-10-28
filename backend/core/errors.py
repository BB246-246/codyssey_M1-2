"""서비스 계층에서 쓰는 예외. main.py의 핸들러가 HTTP 응답으로 변환한다."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ServiceUnavailableError(AppError):
    status_code = 503


class UpstreamError(AppError):
    status_code = 502
