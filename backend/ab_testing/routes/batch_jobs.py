"""
A/B 테스트 배치 작업 라우터

배치 작업 관련 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.connection import get_db
from backend.logger import get_logger
from backend.ab_testing import schemas
from backend.ab_testing import controllers

# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/batch-jobs",
    tags=["AB Testing Batch Jobs"]
)


@router.get("/", response_model=List[schemas.BatchJobStatus])
async def get_batch_jobs(
    status: Optional[str] = Query(None, title="작업 상태"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """배치 작업 목록 조회"""
    logger.info(f"배치 작업 목록 조회: status={status}, limit={limit}")
    return await controllers.get_batch_jobs(db, status, limit)


@router.get("/{job_id}", response_model=schemas.BatchJobStatus)
async def get_batch_job(
    job_id: str = Path(..., title="작업 ID"),
    db: Session = Depends(get_db)
):
    """배치 작업 상태 조회"""
    logger.info(f"배치 작업 상태 조회: job_id={job_id}")
    job = await controllers.get_batch_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"ID {job_id}에 해당하는 배치 작업을 찾을 수 없습니다")
    return job


@router.delete("/{job_id}", response_model=schemas.DeleteResponse)
async def cancel_batch_job(
    job_id: str = Path(..., title="작업 ID"),
    db: Session = Depends(get_db)
):
    """배치 작업 취소"""
    logger.info(f"배치 작업 취소: job_id={job_id}")
    result = await controllers.cancel_batch_job(db, job_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result
