import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core import config
from core.errors import AppError
from routers import chat, conversations, data

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="마라탕 트렌드 AI 비서 API",
    description="구글 트렌드 '마라탕' 월별 검색 관심도 데이터를 기반으로 대화하는 AI 비서",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # 내부 오류 내용(키, 스택 등)이 응답으로 새지 않도록 로그에만 남긴다
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "서버 내부 오류가 발생했습니다."})


app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/", tags=["health"])
def root():
    return {"message": "마라탕 트렌드 AI 비서 API", "docs": "/docs"}


@app.get("/health", tags=["health"], summary="헬스 체크 (콜드스타트 깨우기용)")
def health():
    return {"status": "ok"}
