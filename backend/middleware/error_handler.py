"""
에러 처리 미들웨어 모듈

FastAPI 애플리케이션에서 발생하는 예외를 일관된 형식으로 처리합니다.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from ..exceptions import LLMNightRunError, ValidationError

# 로거 설정
logger = logging.getLogger(__name__)


async def llm_night_run_exception_handler(request: Request, exc: LLMNightRunError):
    """
    LLMNightRun 사용자 정의 예외 처리 미들웨어
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 예외
        
    Returns:
        JSONResponse: 형식화된 에러 응답
    """
    # 로깅 처리
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        f"API 오류 발생: {exc.message}",
        exc_info=True,
        extra={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # 응답 반환
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def validation_exception_handler(request: Request, exc: PydanticValidationError):
    """
    Pydantic 유효성 검사 예외 처리 미들웨어
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 예외
        
    Returns:
        JSONResponse: 형식화된 에러 응답
    """
    # 사용자 정의 ValidationError로 변환
    validation_error = ValidationError(
        message="요청 데이터 유효성 검사 오류", 
        detail=[{"loc": err["loc"], "msg": err["msg"]} for err in exc.errors()]
    )
    
    # 로깅 처리
    logger.warning(
        f"유효성 검사 오류: {validation_error.message}",
        extra={
            "status_code": validation_error.status_code,
            "error_code": validation_error.error_code,
            "path": request.url.path,
            "method": request.method,
            "errors": validation_error.detail
        }
    )
    
    # 응답 반환
    return JSONResponse(
        status_code=validation_error.status_code,
        content=validation_error.to_dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    일반 예외 처리 미들웨어
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 예외
        
    Returns:
        JSONResponse: 형식화된 에러 응답
    """
    # 예기치 않은 오류 처리
    logger.error(
        f"예기치 않은 오류 발생: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # 응답 반환
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "internal_server_error",
            "message": "서버 내부 오류가 발생했습니다",
            "detail": str(exc) if str(exc) else None
        }
    )
