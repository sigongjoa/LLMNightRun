from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, BackgroundTasks
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models import (
    CodebaseIndexingSettings, CodebaseIndexingRun, CodeEmbedding,
    IndexingSettingsUpdate, TriggerIndexingRequest, IndexingRunResponse,
    CodeSearchQuery, EmbeddingSearchResult, IndexingStatus
)
from backend.indexing_manager import get_indexing_manager

router = APIRouter(prefix="/codebases/{codebase_id}/indexing", tags=["indexing"])

@router.get("/settings")
async def get_indexing_settings(
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스의 인덱싱 설정을 조회합니다."""
    try:
        indexing_manager = get_indexing_manager()
        settings = await indexing_manager.initialize_indexing_settings(codebase_id)
        
        return {
            "is_enabled": settings.is_enabled,
            "frequency": settings.frequency.value,
            "excluded_patterns": settings.excluded_patterns,
            "priority_patterns": settings.priority_patterns,
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "include_comments": settings.include_comments,
            "max_files_per_run": settings.max_files_per_run,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/settings")
async def update_indexing_settings(
    settings: IndexingSettingsUpdate,
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스의 인덱싱 설정을 업데이트합니다."""
    try:
        indexing_manager = get_indexing_manager()
        updated_settings = await indexing_manager.update_indexing_settings(
            codebase_id,
            settings.dict(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "인덱싱 설정이 업데이트되었습니다",
            "settings": {
                "is_enabled": updated_settings.is_enabled,
                "frequency": updated_settings.frequency.value,
                "excluded_patterns": updated_settings.excluded_patterns,
                "priority_patterns": updated_settings.priority_patterns,
                "embedding_model": updated_settings.embedding_model,
                "chunk_size": updated_settings.chunk_size,
                "chunk_overlap": updated_settings.chunk_overlap,
                "include_comments": updated_settings.include_comments,
                "max_files_per_run": updated_settings.max_files_per_run,
                "updated_at": updated_settings.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_indexing_status(
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스의 인덱싱 상태를 조회합니다."""
    try:
        indexing_manager = get_indexing_manager()
        status = await indexing_manager.get_indexing_status(codebase_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger", response_model=IndexingRunResponse)
async def trigger_indexing(
    request: TriggerIndexingRequest,
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스 인덱싱을 트리거합니다."""
    try:
        if request.codebase_id != codebase_id:
            raise HTTPException(status_code=400, detail="경로의 코드베이스 ID와 요청 본문의 ID가 일치하지 않습니다")
        
        indexing_manager = get_indexing_manager()
        result = await indexing_manager.trigger_indexing(
            codebase_id,
            is_full_index=request.is_full_index,
            priority_files=request.priority_files,
            triggered_by="manual"
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return {
            "run_id": result["run_id"],
            "status": IndexingStatus.PENDING,
            "message": result["message"],
            "start_time": None
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_code(
    query: CodeSearchQuery,
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스에서 코드를 검색합니다."""
    try:
        if query.codebase_id != codebase_id:
            raise HTTPException(status_code=400, detail="경로의 코드베이스 ID와 요청 본문의 ID가 일치하지 않습니다")
        
        indexing_manager = get_indexing_manager()
        results = await indexing_manager.search_code(
            codebase_id,
            query.query,
            limit=query.limit,
            threshold=query.threshold or 0.5,
            file_patterns=query.file_patterns,
            exclude_patterns=query.exclude_patterns
        )
        
        return {
            "query": query.query,
            "result_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis")
async def analyze_codebase_structure(
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """코드베이스 구조를 분석합니다."""
    try:
        indexing_manager = get_indexing_manager()
        analysis = await indexing_manager.analyze_codebase_structure(codebase_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def clean_up_embeddings(
    codebase_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """임베딩을 정리합니다 (삭제된 파일의 임베딩 제거 등)."""
    try:
        indexing_manager = get_indexing_manager()
        result = await indexing_manager.clean_up_embeddings(codebase_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 스케줄러 엔드포인트
@router.post("/schedule/{frequency}")
async def schedule_indexing(
    frequency: str = Path(..., regex="^(hourly|daily|weekly)$"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """모든 코드베이스에 대한 인덱싱을 예약합니다."""
    try:
        indexing_manager = get_indexing_manager()
        
        # 백그라운드 작업으로 처리
        if background_tasks:
            background_tasks.add_task(indexing_manager.schedule_indexing, frequency)
            return {
                "success": True,
                "message": f"{frequency} 인덱싱 작업이 백그라운드에서 시작되었습니다"
            }
        else:
            result = await indexing_manager.schedule_indexing(frequency)
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))