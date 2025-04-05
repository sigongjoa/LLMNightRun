"""
자동 디버깅 API 라우터 모듈

코드 오류를 자동으로 분석하고 수정하는 API 엔드포인트를 정의합니다.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any

from ..database.connection import get_db
from ..models.enums import LLMType
from ..services.auto_debug_service import AutoDebugService

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "리소스를 찾을 수 없음"}},
)


@router.post("/analyze")
async def analyze_error(
    error_data: Dict[str, Any] = Body(...),
    llm_type: Optional[LLMType] = Query(LLMType.OPENAI_API, description="사용할 LLM 유형"),
    db: Session = Depends(get_db)
):
    """
    코드 오류를 분석하고 수정 방안을 제안합니다.
    
    요청 본문:
    ```json
    {
        "error_message": "오류 메시지",
        "traceback": "오류 트레이스백",
        "codebase_id": 1,
        "additional_context": "추가 컨텍스트 정보 (선택 사항)"
    }
    ```
    
    Args:
        error_data: 오류 정보
        llm_type: 사용할 LLM 유형
        db: 데이터베이스 세션
        
    Returns:
        분석 결과 및 수정 방안
    """
    try:
        # 필수 필드 확인
        if "error_message" not in error_data:
            raise HTTPException(status_code=400, detail="error_message는 필수 필드입니다")
        if "traceback" not in error_data:
            raise HTTPException(status_code=400, detail="traceback은 필수 필드입니다")
        if "codebase_id" not in error_data:
            raise HTTPException(status_code=400, detail="codebase_id는 필수 필드입니다")
        
        # 자동 디버깅 서비스 초기화
        auto_debug_service = AutoDebugService(db, llm_type)
        
        # 에러 분석
        result = await auto_debug_service.analyze_error(
            error_message=error_data["error_message"],
            traceback_text=error_data["traceback"],
            codebase_id=error_data["codebase_id"],
            additional_context=error_data.get("additional_context")
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에러 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에러 분석 실패: {str(e)}")


@router.post("/auto-fix")
async def auto_fix_error(
    error_data: Dict[str, Any] = Body(...),
    apply_fix: bool = Query(False, description="수정 사항 즉시 적용 여부"),
    llm_type: Optional[LLMType] = Query(LLMType.OPENAI_API, description="사용할 LLM 유형"),
    db: Session = Depends(get_db)
):
    """
    코드 오류를 분석하고 자동으로 수정합니다.
    
    요청 본문:
    ```json
    {
        "error_message": "오류 메시지",
        "traceback": "오류 트레이스백",
        "codebase_id": 1,
        "additional_context": "추가 컨텍스트 정보 (선택 사항)"
    }
    ```
    
    Args:
        error_data: 오류 정보
        apply_fix: 수정 사항 즉시 적용 여부
        llm_type: 사용할 LLM 유형
        db: 데이터베이스 세션
        
    Returns:
        수정 결과
    """
    try:
        # 필수 필드 확인
        if "error_message" not in error_data:
            raise HTTPException(status_code=400, detail="error_message는 필수 필드입니다")
        if "traceback" not in error_data:
            raise HTTPException(status_code=400, detail="traceback은 필수 필드입니다")
        if "codebase_id" not in error_data:
            raise HTTPException(status_code=400, detail="codebase_id는 필수 필드입니다")
        
        # 자동 디버깅 서비스 초기화
        auto_debug_service = AutoDebugService(db, llm_type)
        
        # 자동 수정
        result = await auto_debug_service.auto_fix_error(
            error_message=error_data["error_message"],
            traceback_text=error_data["traceback"],
            codebase_id=error_data["codebase_id"],
            apply_fix=apply_fix,
            additional_context=error_data.get("additional_context")
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 수정 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동 수정 실패: {str(e)}")


@router.post("/import-error")
async def debug_import_error(
    import_error_data: Dict[str, Any] = Body(...),
    llm_type: Optional[LLMType] = Query(LLMType.OPENAI_API, description="사용할 LLM 유형"),
    db: Session = Depends(get_db)
):
    """
    모듈 가져오기 오류를 디버깅합니다.
    
    요청 본문:
    ```json
    {
        "module_name": "가져오기 실패한 모듈 이름",
        "error_message": "오류 메시지",
        "codebase_id": 1
    }
    ```
    
    Args:
        import_error_data: 가져오기 오류 정보
        llm_type: 사용할 LLM 유형
        db: 데이터베이스 세션
        
    Returns:
        분석 결과 및 해결 방안
    """
    try:
        # 필수 필드 확인
        if "module_name" not in import_error_data:
            raise HTTPException(status_code=400, detail="module_name은 필수 필드입니다")
        if "error_message" not in import_error_data:
            raise HTTPException(status_code=400, detail="error_message는 필수 필드입니다")
        if "codebase_id" not in import_error_data:
            raise HTTPException(status_code=400, detail="codebase_id는 필수 필드입니다")
        
        # 자동 디버깅 서비스 초기화
        auto_debug_service = AutoDebugService(db, llm_type)
        
        # 가져오기 오류 디버깅
        result = await auto_debug_service.debug_import_error(
            module_name=import_error_data["module_name"],
            error_message=import_error_data["error_message"],
            codebase_id=import_error_data["codebase_id"]
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"가져오기 오류 디버깅 중 문제 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"가져오기 오류 디버깅 실패: {str(e)}")


@router.get("/verify-environment/{codebase_id}")
async def verify_environment(
    codebase_id: int,
    db: Session = Depends(get_db)
):
    """
    코드베이스의 환경 설정을 검증합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        db: 데이터베이스 세션
        
    Returns:
        환경 검증 결과
    """
    try:
        # 자동 디버깅 서비스 초기화
        auto_debug_service = AutoDebugService(db)
        
        # 환경 검증
        result = await auto_debug_service.verify_environment(codebase_id)
        
        return result
    except Exception as e:
        logger.error(f"환경 검증 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"환경 검증 실패: {str(e)}")