"""
A/B 테스트 배치 작업 컨트롤러

배치 작업 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

from backend.logger import get_logger
from backend.ab_testing import models, schemas

# 로거 설정
logger = get_logger(__name__)


async def get_batch_jobs(
    db: Session, 
    status: Optional[str] = None, 
    limit: int = 10
) -> List[schemas.BatchJobStatus]:
    """배치 작업 목록을 조회합니다."""
    query = db.query(models.BatchJob)
    
    if status:
        query = query.filter(models.BatchJob.status == status)
    
    batch_jobs = query.order_by(models.BatchJob.started_at.desc()).limit(limit).all()
    
    result = []
    for job in batch_jobs:
        # 완료 예상 시간 계산
        estimated_completion = None
        if job.started_at and job.status == "running" and job.items_total > 0 and job.items_processed > 0:
            elapsed_time = (datetime.utcnow() - job.started_at).total_seconds()
            time_per_item = elapsed_time / job.items_processed
            remaining_items = job.items_total - job.items_processed
            remaining_time = remaining_items * time_per_item
            
            estimated_completion = job.started_at + timedelta(seconds=remaining_time)
        
        # 진행률 계산
        progress = 0.0
        if job.items_total > 0:
            progress = min(1.0, job.items_processed / job.items_total)
        
        job_status = {
            "job_id": job.job_id,
            "status": job.status,
            "progress": progress,
            "started_at": job.started_at,
            "estimated_completion": estimated_completion,
            "items_total": job.items_total,
            "items_processed": job.items_processed,
            "items_failed": job.items_failed
        }
        
        result.append(job_status)
    
    return result


async def get_batch_job(db: Session, job_id: str) -> Optional[schemas.BatchJobStatus]:
    """배치 작업 상태를 조회합니다."""
    job = db.query(models.BatchJob).filter(models.BatchJob.job_id == job_id).first()
    
    if not job:
        return None
    
    # 완료 예상 시간 계산
    estimated_completion = None
    if job.started_at and job.status == "running" and job.items_total > 0 and job.items_processed > 0:
        elapsed_time = (datetime.utcnow() - job.started_at).total_seconds()
        time_per_item = elapsed_time / job.items_processed
        remaining_items = job.items_total - job.items_processed
        remaining_time = remaining_items * time_per_item
        
        estimated_completion = job.started_at + timedelta(seconds=remaining_time)
    
    # 진행률 계산
    progress = 0.0
    if job.items_total > 0:
        progress = min(1.0, job.items_processed / job.items_total)
    
    job_status = {
        "job_id": job.job_id,
        "status": job.status,
        "progress": progress,
        "started_at": job.started_at,
        "estimated_completion": estimated_completion,
        "items_total": job.items_total,
        "items_processed": job.items_processed,
        "items_failed": job.items_failed
    }
    
    return job_status


async def cancel_batch_job(db: Session, job_id: str) -> Dict[str, Any]:
    """배치 작업을 취소합니다."""
    job = db.query(models.BatchJob).filter(models.BatchJob.job_id == job_id).first()
    
    if not job:
        return {"success": False, "message": f"ID {job_id}에 해당하는 배치 작업을 찾을 수 없습니다"}
    
    # 이미 완료된 작업은 취소할 수 없음
    if job.status in ["completed", "failed"]:
        return {"success": False, "message": f"이미 {job.status} 상태인 작업은 취소할 수 없습니다"}
    
    # 작업 취소
    job.status = "canceled"
    job.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": f"배치 작업 '{job_id}'이(가) 취소되었습니다"}


async def create_batch_job(
    db: Session, 
    experiment_set_id: int, 
    job_id: str, 
    items_total: int, 
    config: Optional[Dict[str, Any]] = None
) -> models.BatchJob:
    """새 배치 작업을 생성합니다."""
    try:
        job = models.BatchJob(
            experiment_set_id=experiment_set_id,
            job_id=job_id,
            status="pending",
            config=config or {},
            items_total=items_total,
            items_processed=0,
            items_failed=0,
            started_at=datetime.utcnow()
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return job
        
    except Exception as e:
        db.rollback()
        logger.error(f"배치 작업 생성 중 오류 발생: {str(e)}")
        raise


async def update_batch_job_status(
    db: Session, 
    job_id: str, 
    status: str, 
    items_processed: Optional[int] = None, 
    items_failed: Optional[int] = None, 
    error: Optional[str] = None
) -> Optional[models.BatchJob]:
    """배치 작업 상태를 업데이트합니다."""
    try:
        job = db.query(models.BatchJob).filter(models.BatchJob.job_id == job_id).first()
        if not job:
            return None
        
        # 상태 업데이트
        job.status = status
        
        # 처리된 항목 수 업데이트
        if items_processed is not None:
            job.items_processed = items_processed
        
        # 실패한 항목 수 업데이트
        if items_failed is not None:
            job.items_failed = items_failed
        
        # 오류 메시지 업데이트
        if error:
            job.error = error
        
        # 완료 시간 업데이트
        if status in ["completed", "failed", "canceled"]:
            job.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(job)
        
        return job
        
    except Exception as e:
        db.rollback()
        logger.error(f"배치 작업 상태 업데이트 중 오류 발생: {str(e)}")
        return None


from datetime import timedelta
