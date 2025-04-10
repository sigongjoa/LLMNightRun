"""
LLMNightRun API 메인 애플리케이션 모듈 (etc 폴더용 백업)
"""

import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# 내부 모듈 임포트
from backend.config import settings
from backend.logger import setup_logging, get_logger, LogContext

# 로깅 설정
logger = get_logger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"{settings.app_name} API 서버 시작 (etc 백업 버전)")
    
    # 로깅 설정
    setup_logging(settings.get_log_level())

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"{settings.app_name} API 서버 종료")

# 메인 엔드포인트
@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": f"{settings.app_name} API에 오신 것을 환영합니다! (etc 백업 버전)",
        "version": settings.app_version,
        "environment": settings.env.value
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """시스템 헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.env.value,
        "timestamp": datetime.utcnow().isoformat()
    }

# 직접 실행 시
if __name__ == "__main__":
    logger.info(f"{settings.app_name} 서버 실행 준비 (etc 백업 버전)")
    
    uvicorn.run(
        "main_fix:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.logging.level.lower()
    )