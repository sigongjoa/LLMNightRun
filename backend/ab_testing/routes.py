"""
A/B 테스트 라우터

FastAPI 라우터 정의 및 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from backend.database.connection import get_db
from backend.logger import get_logger
from . import schemas
from . import controllers


# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/ab-testing",
    tags=["AB Testing"]
)


# 실험 세트 관리 엔드포인트
@router.post("/experiment-sets/", response_model=schemas.ExperimentSetDB)
async def create_experiment_set(
    experiment_set: schemas.ExperimentSetCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """새 실험 세트 생성"""
    logger.info(f"실험 세트 생성 요청: {experiment_set.name}")
    return await controllers.create_experiment_set(db, experiment_set)


@router.get("/experiment-sets/", response_model=List[schemas.ExperimentSetDB])
async def get_experiment_sets(
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """실험 세트 목록 조회"""
    logger.info(f"실험 세트 목록 조회: skip={skip}, limit={limit}, active_only={active_only}")
    return await controllers.get_experiment_sets(db, skip, limit, active_only)


@router.get("/experiment-sets/{set_id}", response_model=schemas.ExperimentSetDetailResponse)
async def get_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 상세 조회"""
    logger.info(f"실험 세트 상세 조회: id={set_id}")
    experiment_set = await controllers.get_experiment_set(db, set_id)
    if not experiment_set:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
    return experiment_set


@router.put("/experiment-sets/{set_id}", response_model=schemas.ExperimentSetDB)
async def update_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    experiment_set: schemas.ExperimentSetBase = None,
    db: Session = Depends(get_db)
):
    """실험 세트 업데이트"""
    logger.info(f"실험 세트 업데이트: id={set_id}")
    updated_set = await controllers.update_experiment_set(db, set_id, experiment_set)
    if not updated_set:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
    return updated_set


@router.delete("/experiment-sets/{set_id}", response_model=schemas.DeleteResponse)
async def delete_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 삭제"""
    logger.info(f"실험 세트 삭제: id={set_id}")
    result = await controllers.delete_experiment_set(db, set_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# 실험 관리 엔드포인트
@router.post("/experiment-sets/{set_id}/experiments", response_model=schemas.ExperimentDB)
async def add_experiment(
    set_id: int = Path(..., title="실험 세트 ID"),
    experiment: schemas.ExperimentCreate = None,
    db: Session = Depends(get_db)
):
    """실험 세트에 새 실험 추가"""
    logger.info(f"실험 추가: set_id={set_id}, experiment={experiment.name}")
    return await controllers.add_experiment(db, set_id, experiment)


@router.put("/experiments/{experiment_id}", response_model=schemas.ExperimentDB)
async def update_experiment(
    experiment_id: int = Path(..., title="실험 ID"),
    experiment: schemas.ExperimentBase = None,
    db: Session = Depends(get_db)
):
    """실험 업데이트"""
    logger.info(f"실험 업데이트: id={experiment_id}")
    updated_experiment = await controllers.update_experiment(db, experiment_id, experiment)
    if not updated_experiment:
        raise HTTPException(status_code=404, detail=f"ID {experiment_id}에 해당하는 실험을 찾을 수 없습니다")
    return updated_experiment


@router.delete("/experiments/{experiment_id}", response_model=schemas.DeleteResponse)
async def delete_experiment(
    experiment_id: int = Path(..., title="실험 ID"),
    db: Session = Depends(get_db)
):
    """실험 삭제"""
    logger.info(f"실험 삭제: id={experiment_id}")
    result = await controllers.delete_experiment(db, experiment_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# 실험 실행 엔드포인트
@router.post("/experiment-sets/{set_id}/run", response_model=schemas.RunResponse)
async def run_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    run_config: schemas.RunExperimentSet = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """실험 세트 실행"""
    logger.info(f"실험 세트 실행: id={set_id}")
    
    # 기본 설정
    if run_config is None:
        run_config = schemas.RunExperimentSet()
    
    # 백그라운드 작업으로 실험 실행
    run_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.run_experiment_set_background,
        db, set_id, run_id, run_config
    )
    
    return {
        "experiment_set_id": set_id,
        "run_id": run_id,
        "status": "started",
        "message": "실험 세트 실행이 시작되었습니다",
        "started_at": datetime.utcnow()
    }


@router.get("/experiment-sets/{set_id}/status", response_model=schemas.StatusResponse)
async def get_experiment_set_status(
    set_id: int = Path(..., title="실험 세트 ID"),
    run_id: Optional[str] = Query(None, title="실행 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 실행 상태 조회"""
    logger.info(f"실험 세트 상태 조회: id={set_id}, run_id={run_id}")
    status = await controllers.get_experiment_set_status(db, set_id, run_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
    return status


# 결과 및 평가 엔드포인트
@router.get("/experiment-sets/{set_id}/results", response_model=schemas.ResultsResponse)
async def get_experiment_set_results(
    set_id: int = Path(..., title="실험 세트 ID"),
    run_id: Optional[str] = Query(None, title="실행 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 결과 조회"""
    logger.info(f"실험 세트 결과 조회: id={set_id}, run_id={run_id}")
    results = await controllers.get_experiment_set_results(db, set_id, run_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트 결과를 찾을 수 없습니다")
    return results


@router.post("/experiment-sets/{set_id}/evaluate", response_model=dict)
async def evaluate_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    evaluation_config: Optional[schemas.EvaluationConfig] = None,
    background_tasks: BackgroundTasks = None,
    run_id: Optional[str] = Query(None, title="실행 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 결과 평가"""
    logger.info(f"실험 세트 평가: id={set_id}, run_id={run_id}")
    
    # 백그라운드 작업으로 평가 실행
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.evaluate_experiment_set_background,
        db, set_id, run_id, evaluation_config, task_id
    )
    
    return {
        "experiment_set_id": set_id,
        "task_id": task_id,
        "status": "started",
        "message": "실험 세트 평가가 시작되었습니다",
        "started_at": datetime.utcnow()
    }


@router.get("/experiment-sets/{set_id}/evaluations", response_model=dict)
async def get_experiment_set_evaluations(
    set_id: int = Path(..., title="실험 세트 ID"),
    run_id: Optional[str] = Query(None, title="실행 ID"),
    db: Session = Depends(get_db)
):
    """실험 세트 평가 결과 조회"""
    logger.info(f"실험 세트 평가 결과 조회: id={set_id}, run_id={run_id}")
    evaluations = await controllers.get_experiment_set_evaluations(db, set_id, run_id)
    if not evaluations:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트 평가 결과를 찾을 수 없습니다")
    return evaluations


# 보고서 및 내보내기 엔드포인트
@router.get("/experiment-sets/{set_id}/report", response_model=schemas.ReportResponse)
async def generate_report(
    set_id: int = Path(..., title="실험 세트 ID"),
    format: str = Query("html", title="보고서 형식", regex="^(html|pdf|json)$"),
    run_id: Optional[str] = Query(None, title="실행 ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """실험 세트 보고서 생성"""
    logger.info(f"실험 세트 보고서 생성: id={set_id}, format={format}, run_id={run_id}")
    
    # 백그라운드 작업으로 보고서 생성
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.generate_report_background,
        db, set_id, format, run_id, task_id
    )
    
    return {
        "experiment_set_id": set_id,
        "report_url": f"/ab-testing/reports/{task_id}.{format}",
        "report_type": format,
        "generated_at": datetime.utcnow()
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str = Path(..., title="보고서 ID"),
    db: Session = Depends(get_db)
):
    """보고서 파일 다운로드"""
    logger.info(f"보고서 다운로드: id={report_id}")
    
    # 파일 경로 확인
    file_path = await controllers.get_report_path(report_id)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"ID {report_id}에 해당하는 보고서를 찾을 수 없습니다")
    
    return FileResponse(
        path=file_path,
        filename=f"report_{report_id}.{file_path.split('.')[-1]}",
        media_type="application/octet-stream"
    )


@router.get("/experiment-sets/{set_id}/export", response_model=schemas.ExportResponse)
async def export_experiment_set(
    set_id: int = Path(..., title="실험 세트 ID"),
    format: str = Query("json", title="내보내기 형식", regex="^(json|csv|excel)$"),
    run_id: Optional[str] = Query(None, title="실행 ID"),
    include_results: bool = Query(True, title="결과 포함 여부"),
    include_evaluations: bool = Query(True, title="평가 포함 여부"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """실험 세트 내보내기"""
    logger.info(f"실험 세트 내보내기: id={set_id}, format={format}, run_id={run_id}")
    
    # 백그라운드 작업으로 내보내기
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.export_experiment_set_background,
        db, set_id, format, run_id, include_results, include_evaluations, task_id
    )
    
    return {
        "experiment_set_id": set_id,
        "file_url": f"/ab-testing/exports/{task_id}.{format}",
        "format": format,
        "size_bytes": 0,  # 실제 크기는 백그라운드 작업에서 계산
        "generated_at": datetime.utcnow()
    }


@router.get("/exports/{export_id}")
async def get_export(
    export_id: str = Path(..., title="내보내기 ID"),
    db: Session = Depends(get_db)
):
    """내보내기 파일 다운로드"""
    logger.info(f"내보내기 다운로드: id={export_id}")
    
    # 파일 경로 확인
    file_path = await controllers.get_export_path(export_id)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"ID {export_id}에 해당하는 내보내기 파일을 찾을 수 없습니다")
    
    return FileResponse(
        path=file_path,
        filename=f"ab_test_export_{export_id}.{file_path.split('.')[-1]}",
        media_type="application/octet-stream"
    )
