"""
LLMNightRun API 메인 애플리케이션 모듈

FastAPI 애플리케이션의 진입점입니다.
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from backend.config import settings
from backend.logger import setup_logging
from backend.exceptions import LLMNightRunError, LLMError
from backend.database.connection import create_tables
from backend.api import question, response, code, agent, indexing, export, auto_debug


# 로깅 설정
logger = setup_logging()

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="LLMNightRun API",
    description="멀티 LLM 통합 자동화 플랫폼 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 오리진 허용, 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 예외 핸들러
@app.exception_handler(LLMNightRunError)
async def llm_night_run_exception_handler(request: Request, exc: LLMNightRunError):
    """사용자 정의 예외 처리"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.exception_handler(LLMError)
async def llm_exception_handler(request: Request, exc: LLMError):
    """LLM 관련 예외 처리"""
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

# 메인 엔드포인트
@app.get("/")
async def root():
    """루트 경로"""
    return {"message": "LLMNightRun API에 오신 것을 환영합니다!"}

# 헬스 체크 엔드포인트
@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    시스템 헬스 체크 엔드포인트.
    쿠버네티스, 도커 또는 기타 모니터링 도구에서 사용할 수 있습니다.
    """
    # 현재 버전 정보
    version = "0.1.0"
    
    return {
        "status": "healthy",
        "version": version,
        "timestamp": datetime.utcnow().isoformat()
    }

# 라우터 등록
app.include_router(question.router)
app.include_router(response.router)
app.include_router(code.router)
app.include_router(agent.router)
app.include_router(indexing.router)
app.include_router(export.router)
app.include_router(auto_debug.router)

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("LLMNightRun API 서버 시작")
    
    # 데이터베이스 테이블 생성
    create_tables()

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("LLMNightRun API 서버 종료")


# 직접 실행 시
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )