"""
LLMNightRun API 메인 애플리케이션 모듈

FastAPI 애플리케이션의 진입점으로, 모든 API 라우터를 등록하고 서버를 실행합니다.
"""

import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# 내부 모듈 임포트
from backend.config import settings
from backend.logger import setup_logging, get_logger, LogContext
from backend.exceptions import LLMNightRunError, LLMError
from backend.database.connection import create_tables
from backend.core.service_locator import setup_services

# API 라우터 임포트 - 기능별 그룹화
# 핵심 기능
from backend.api import question, response, code
# 에이전트 및 도구
from backend.api import agent, github
# 데이터 관리
from backend.api import indexing, export, docs_manager
# 시스템 및 디버깅
from backend.api import auto_debug, local_llm, mcp_status, model_installer, ai_environment
# 메모리 관리
from backend.api.memory.router import router as memory_router

# v2 API 라우터 임포트
from backend.api.v2 import llm as llm_v2

# MCP 관련 라우터 임포트
from backend.mcp import router as mcp_router
from backend.mcp import websocket_router as mcp_ws_router
from backend.mcp import api_router as mcp_api_router
from backend.mcp.chat_websocket import router as mcp_chat_ws_router

# 로깅 설정
logger = get_logger(__name__)

# 애플리케이션 메타데이터
tags_metadata = [
    {
        "name": "core",
        "description": "질문/응답 및 코드 생성 핵심 기능",
    },
    {
        "name": "agent",
        "description": "자동화 에이전트 및 도구 관련 기능",
    },
    {
        "name": "data",
        "description": "데이터 관리 및 인덱싱 기능",
    },
    {
        "name": "system",
        "description": "시스템 상태 및 디버깅 기능",
    },
    {
        "name": "monitoring",
        "description": "시스템 모니터링 및 상태 확인 엔드포인트",
    },
    {
        "name": "api_v2",
        "description": "리팩토링된 API v2 엔드포인트",
    },
    {
        "name": "memory",
        "description": "LLM 메모리 관리 및 벡터 DB 연동 기능",
    },
    {
        "name": "model-installer",
        "description": "GitHub 모델 자동 설치 및 관리 기능",
    },
    {
        "name": "ai-environment",
        "description": "AI 환경설정 및 모델 관리 기능",
    },
]

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
    openapi_tags=tags_metadata,
    root_path=settings.root_path
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# 전역 예외 핸들러 등록
from backend.middleware import (
    llm_night_run_exception_handler, 
    validation_exception_handler,
    general_exception_handler
)
from pydantic import ValidationError as PydanticValidationError

# 사용자 정의 예외 핸들러 등록
app.add_exception_handler(LLMNightRunError, llm_night_run_exception_handler)
app.add_exception_handler(PydanticValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 커스텀 OpenAPI 스키마 설정
from backend.utils.openapi import custom_openapi
app.openapi = lambda: custom_openapi(app)

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

# 라우터 등록 - 기능별 그룹화
def register_routers():
    """모든 라우터를 등록하는 헬퍼 함수"""
    # 핵심 기능 (Core)
    core_routers = [
        (question.router, "core"),
        (response.router, "core"),
        (code.router, "core"),
    ]
    
    # 에이전트 및 도구 (Agent)
    agent_routers = [
        (agent.router, "agent"),
        (github.router, "agent"),
    ]
    
    # 데이터 관리 (Data)
    data_routers = [
        (indexing.router, "data"),
        (export.router, "data"),
        (docs_manager.router, "data"),
    ]
    
    # 시스템 및 디버깅 (System)
    system_routers = [
        (auto_debug.router, "system"),
        (local_llm.router, "system"),
        (mcp_status.router, "system"),
        (model_installer.router, "model-installer"),
        (ai_environment.router, "system"),
    ]
    
    # v2 API 라우터
    v2_routers = [
        (llm_v2.router, "api_v2"),
    ]
    
    # MCP 관련 라우터
    mcp_routers = [
        (mcp_router, None),
        (mcp_ws_router, None),
        (mcp_api_router, None),
        (mcp_chat_ws_router, None),
    ]
    
    # 모든 라우터 목록
    all_routers = core_routers + agent_routers + data_routers + system_routers + v2_routers + mcp_routers
    
    # 라우터 등록
    for router, tag in all_routers:
        if tag:
            router.tags = [tag] + (router.tags or [])
        app.include_router(router)
    
    # 개별 처리가 필요한 메모리 라우터 추가
    try:
        # 메모리 라우터 태그 설정 및 추가
        if not hasattr(memory_router, 'tags'):
            memory_router.tags = []
        memory_router.tags.append("memory")
        app.include_router(memory_router)
        logger.info("메모리 라우터 등록 완료")
    except Exception as e:
        logger.error(f"메모리 라우터 등록 실패: {str(e)}")
    
    logger.info(f"총 {len(all_routers) + 1}개 라우터 등록 완료")

# 라우터 등록 실행
register_routers()

# 애플리케이션 초기화 및 리소스 설정
async def initialize_app():
    """애플리케이션 초기화 및 리소스 설정"""
    try:
        # 로깅 설정
        setup_logging(settings.get_log_level())
        
        # 데이터베이스 테이블 생성
        create_tables()
        
        # 서비스 초기화 및 등록
        setup_services()
        logger.info("서비스 초기화 및 등록 완료")
        
        # 기타 초기화 작업
        # ...
        
        # 초기화 완료 로그
        env_name = settings.env.value.upper()
        logger.info(
            f"애플리케이션 초기화 완료 - 환경: {env_name}", 
            extra={"environment": env_name}
        )
        
        return True
    except Exception as e:
        logger.error(f"애플리케이션 초기화 실패: {str(e)}", exc_info=True)
        raise


# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    with LogContext(event="startup"):
        logger.info(f"{settings.app_name} API 서버 시작")
        
        # 애플리케이션 초기화
        await initialize_app()
        
        # 개발 환경에서는 API 문서 자동 생성
        if settings.is_development():
            from backend.utils.openapi import export_openapi_schema, create_api_documentation
            try:
                export_openapi_schema(app)
                create_api_documentation(app)
                logger.info("API 문서 자동 생성 완료")
            except Exception as e:
                logger.warning(f"API 문서 생성 중 오류 발생: {str(e)}", exc_info=True)


# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    with LogContext(event="shutdown"):
        logger.info(f"{settings.app_name} API 서버 종료")


# 애플리케이션 버전 및 상태 정보
def get_app_info() -> dict:
    """애플리케이션 버전 및 상태 정보 반환"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "environment": settings.env.value
    }


# 메인 엔드포인트
@app.get("/", tags=["monitoring"])
async def root():
    """루트 경로"""
    app_info = get_app_info()
    return {
        "message": f"{app_info['name']} API에 오신 것을 환영합니다!",
        "app": app_info
    }


# 헬스 체크 엔드포인트
@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    시스템 헬스 체크 엔드포인트.
    쿠버네티스, 도커 또는 기타 모니터링 도구에서 사용할 수 있습니다.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.env.value,
        "timestamp": datetime.utcnow().isoformat()
    }


# 직접 실행 시
if __name__ == "__main__":
    with LogContext(mode="standalone"):
        logger.info(f"{settings.app_name} 서버 실행 준비")
        
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.logging.level.lower()
        )