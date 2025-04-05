"""
인덱싱 API 라우터 모듈

코드베이스 인덱싱 관련 엔드포인트를 정의합니다.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from ..database.connection import get_db
from ..database.operations.indexing import (
    get_indexing_settings, create_or_update_indexing_settings,
    get_indexing_runs, create_indexing_run, update_indexing_run, 
    get_codebase_embeddings_stats
)
from ..models.indexing import (
    CodebaseIndexingSettings, IndexingSettingsUpdate, 
    TriggerIndexingRequest, IndexingRunResponse, 
    CodeSearchQuery
)
from ..services.indexing_service import IndexingService

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/codebases",
    tags=["indexing"],
    responses={404: {"description": "코드베이스를 찾을 수 없음"}},
)


@router.get("/{codebase_id}/indexing/settings", response_model=CodebaseIndexingSettings)
async def get_codebase_indexing_settings(
    codebase_id: int, 
    db: Session = Depends(get_db)
):
    """
    코드베이스의 인덱싱 설정을 조회합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        db: 데이터베이스 세션
        
    Returns:
        인덱싱 설정 정보
        
    Raises:
        HTTPException: 코드베이스가 없거나 설정이 없는 경우
    """
    try:
        settings = get_indexing_settings(db, codebase_id)
        if not settings:
            raise HTTPException(
                status_code=404, 
                detail=f"코드베이스 ID {codebase_id}의 인덱싱 설정을 찾을 수 없습니다"
            )
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인덱싱 설정 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인덱싱 설정 조회 실패: {str(e)}")


@router.patch("/{codebase_id}/indexing/settings")
async def update_codebase_indexing_settings(
    codebase_id: int, 
    settings: IndexingSettingsUpdate, 
    db: Session = Depends(get_db)
):
    """
    코드베이스의 인덱싱 설정을 업데이트합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        settings: 업데이트할 설정 정보
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 설정 정보
        
    Raises:
        HTTPException: 코드베이스가 없거나 설정 업데이트에 실패한 경우
    """
    try:
        updated_settings = create_or_update_indexing_settings(db, codebase_id, settings.dict(exclude_unset=True))
        
        return {
            "success": True,
            "message": "인덱싱 설정이 업데이트되었습니다",
            "settings": updated_settings
        }
    except Exception as e:
        logger.error(f"인덱싱 설정 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인덱싱 설정 업데이트 실패: {str(e)}")


@router.get("/{codebase_id}/indexing/status")
async def get_codebase_indexing_status(
    codebase_id: int, 
    db: Session = Depends(get_db)
):
    """
    코드베이스의 인덱싱 상태를 조회합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        db: 데이터베이스 세션
        
    Returns:
        인덱싱 상태 정보
        
    Raises:
        HTTPException: 코드베이스가 없거나 상태 조회에 실패한 경우
    """
    try:
        # 인덱싱 서비스 초기화
        indexing_service = IndexingService(db)
        
        # 통계 조회
        stats = await indexing_service.get_stats(codebase_id)
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인덱싱 상태 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인덱싱 상태 조회 실패: {str(e)}")


@router.post("/{codebase_id}/indexing/trigger", response_model=IndexingRunResponse)
async def trigger_indexing(
    codebase_id: int, 
    request: TriggerIndexingRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    코드베이스 인덱싱을 트리거합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        request: 인덱싱 요청 정보
        background_tasks: 백그라운드 태스크 객체
        db: 데이터베이스 세션
        
    Returns:
        인덱싱 실행 정보
        
    Raises:
        HTTPException: 코드베이스가 없거나 인덱싱 트리거에 실패한 경우
    """
    try:
        # 인덱싱 설정 확인
        settings = get_indexing_settings(db, codebase_id)
        if not settings:
            raise HTTPException(
                status_code=404, 
                detail=f"코드베이스 ID {codebase_id}의 인덱싱 설정을 찾을 수 없습니다"
            )
        
        # 이미 실행 중인 인덱싱이 있는지 확인
        active_runs = get_indexing_runs(db, codebase_id, status="in_progress")
        if active_runs:
            raise HTTPException(
                status_code=400, 
                detail=f"이미 인덱싱이 실행 중입니다 (실행 ID: {active_runs[0].id})"
            )
        
        # 인덱싱 실행 생성
        run = create_indexing_run(
            db,
            codebase_id=codebase_id,
            is_full_index=request.is_full_index,
            triggered_by="manual"
        )
        
        # 백그라운드에서 인덱싱 처리
        indexing_service = IndexingService(db)
        background_tasks.add_task(
            indexing_service.process_indexing_run,
            run_id=run.id,
            is_full_index=request.is_full_index
        )
        
        return {
            "run_id": run.id,
            "status": run.status,
            "message": "인덱싱이 시작되었습니다.",
            "start_time": run.start_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인덱싱 트리거 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인덱싱 트리거 실패: {str(e)}")


@router.post("/{codebase_id}/indexing/search")
async def search_code(
    codebase_id: int, 
    query: CodeSearchQuery, 
    db: Session = Depends(get_db)
):
    """
    코드베이스에서 코드를 검색합니다.
    
    Args:
        codebase_id: 코드베이스 ID
        query: 검색 쿼리 정보
        db: 데이터베이스 세션
        
    Returns:
        검색 결과
        
    Raises:
        HTTPException: 코드베이스가 없거나 검색에 실패한 경우
    """
    try:
        # 인덱싱 서비스 초기화
        indexing_service = IndexingService(db)
        
        # 검색 실행
        results = await indexing_service.search_similar_code(
            query=query.query,
            limit=query.limit,
            threshold=query.threshold or 0.7,
            codebase_id=codebase_id,
            file_patterns=query.file_patterns
        )
        
        return {
            "query": query.query,
            "result_count": len(results),
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 검색 실패: {str(e)}")