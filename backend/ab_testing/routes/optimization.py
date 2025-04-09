"""
A/B 테스트 최적화 라우터

프롬프트, 파라미터 최적화 관련 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from backend.database.connection import get_db
from backend.logger import get_logger
from backend.ab_testing import schemas
from backend.ab_testing import controllers

# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/optimization",
    tags=["AB Testing Optimization"]
)


@router.post("/experiment-sets/{set_id}/optimize", response_model=dict)
async def optimize_experiment_set(
    set_id: int,
    optimization_request: schemas.OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """실험 세트 최적화"""
    logger.info(f"실험 세트 최적화: id={set_id}, target={optimization_request.optimization_target}")
    
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.optimize_experiment_set_background,
        db, set_id, optimization_request, task_id
    )
    
    return {
        "experiment_set_id": set_id,
        "task_id": task_id,
        "status": "started",
        "message": f"{optimization_request.optimization_target} 최적화가 시작되었습니다",
        "started_at": datetime.utcnow()
    }


@router.get("/experiment-sets/{set_id}/results/{task_id}", response_model=schemas.OptimizationResult)
async def get_optimization_results(
    set_id: int,
    task_id: str,
    db: Session = Depends(get_db)
):
    """최적화 결과 조회"""
    logger.info(f"최적화 결과 조회: set_id={set_id}, task_id={task_id}")
    result = await controllers.get_optimization_results(db, set_id, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="해당하는 최적화 결과를 찾을 수 없습니다")
    return result


@router.post("/experiments/{experiment_id}/consistency-test", response_model=dict)
async def run_consistency_test(
    experiment_id: int,
    background_tasks: BackgroundTasks,
    iterations: int = Query(5, ge=3, le=20, title="반복 횟수"),
    db: Session = Depends(get_db)
):
    """실험 일관성 테스트 실행"""
    logger.info(f"일관성 테스트 실행: experiment_id={experiment_id}, iterations={iterations}")
    
    test_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.run_consistency_test_background,
        db, experiment_id, iterations, test_id
    )
    
    return {
        "experiment_id": experiment_id,
        "test_id": test_id,
        "status": "started",
        "message": f"일관성 테스트가 시작되었습니다 (반복 횟수: {iterations})",
        "started_at": datetime.utcnow()
    }


@router.get("/experiments/{experiment_id}/consistency-results/{test_id}", response_model=schemas.ConsistencyTestResult)
async def get_consistency_test_results(
    experiment_id: int,
    test_id: str,
    db: Session = Depends(get_db)
):
    """일관성 테스트 결과 조회"""
    logger.info(f"일관성 테스트 결과 조회: experiment_id={experiment_id}, test_id={test_id}")
    result = await controllers.get_consistency_test_results(db, experiment_id, test_id)
    if not result:
        raise HTTPException(status_code=404, detail="해당하는 일관성 테스트 결과를 찾을 수 없습니다")
    return result
