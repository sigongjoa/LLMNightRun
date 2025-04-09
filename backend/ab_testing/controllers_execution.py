"""
A/B 테스트 실행 컨트롤러

실험 실행 관련 비즈니스 로직을 구현합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.logger import get_logger
from backend.database.connection import SessionLocal as DBSession
from . import models, schemas
from .config import ab_testing_settings
from .services.experiment import ExperimentRunner
from .services.evaluator import Evaluator

# 로거 설정
logger = get_logger(__name__)


async def run_experiment_set_background(
    db: Session, experiment_set_id: int, run_id: str, run_config: schemas.RunExperimentSet
):
    """백그라운드에서 실험 세트를 실행합니다."""
    logger.info(f"실험 세트 실행 시작: id={experiment_set_id}, run_id={run_id}")
    
    try:
        # 세션 복제 (백그라운드 작업용)
        db_copy = DBSession(bind=db.get_bind())
        
        # 실험 러너 생성
        runner = ExperimentRunner(db_copy)
        
        # 설정에 run_id 추가
        config_dict = run_config.dict() if run_config else {}
        config_dict["run_id"] = run_id
        
        # 실험 세트 실행
        await runner.run_experiment_set(experiment_set_id, config_dict)
        
        # 평가 설정이 있으면 자동 평가 실행
        if run_config and run_config.evaluation_config:
            evaluator = Evaluator(db_copy)
            await evaluator.evaluate_experiment_set(
                experiment_set_id, 
                run_id=run_id,
                metrics=run_config.evaluation_config.metrics,
                weights=run_config.evaluation_config.weights
            )
        
        logger.info(f"실험 세트 실행 완료: id={experiment_set_id}, run_id={run_id}")
        
    except Exception as e:
        logger.error(f"실험 세트 실행 실패: id={experiment_set_id}, run_id={run_id}, error={str(e)}")
        # 오류 상태 업데이트 코드 추가 필요
    finally:
        if 'db_copy' in locals():
            db_copy.close()


async def get_experiment_set_status(
    db: Session, experiment_set_id: int, run_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """실험 세트의 실행 상태를 조회합니다."""
    # 실험 세트 조회
    db_experiment_set = db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()
    
    if not db_experiment_set:
        return None
    
    # 쿼리 기본 설정
    results_query = db.query(models.ExperimentResult).join(
        models.Experiment, 
        models.ExperimentResult.experiment_id == models.Experiment.id
    ).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    )
    
    # run_id가 지정된 경우 필터링
    if run_id:
        results_query = results_query.filter(models.ExperimentResult.run_id == run_id)
    
    # 실험 결과 상태 집계
    results = results_query.all()
    total_experiments = db.query(models.Experiment).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    ).count()
    
    # 상태별 카운트
    completed = sum(1 for r in results if r.status == "completed")
    running = sum(1 for r in results if r.status == "running")
    failed = sum(1 for r in results if r.status == "failed")
    pending = total_experiments - completed - running - failed
    
    # 전체 상태 결정
    status = "pending"
    if completed + failed == total_experiments:
        status = "completed"
    elif running > 0:
        status = "running"
    elif failed > 0 and failed == total_experiments:
        status = "failed"
    
    # 진행률 계산
    progress = (completed + failed) / total_experiments if total_experiments > 0 else 0
    
    # 시작 시간 계산
    started_at = min([r.created_at for r in results], default=None) if results else None
    
    # 예상 완료 시간 계산 (간단한 추정)
    estimated_completion = None
    if started_at and running > 0 and completed > 0:
        # 평균 실행 시간 계산
        avg_execution_time = sum(r.execution_time for r in results if r.status == "completed" and r.execution_time) / completed
        
        # 남은 시간 추정
        max_workers = 5  # 기본값
        if db_experiment_set.config and "max_workers" in db_experiment_set.config:
            max_workers = db_experiment_set.config["max_workers"]
            
        remaining_experiments = total_experiments - completed - failed
        remaining_time = avg_execution_time * remaining_experiments / max_workers
        
        # 예상 완료 시간
        estimated_completion = started_at + timedelta(seconds=remaining_time)
    
    return {
        "experiment_set_id": experiment_set_id,
        "name": db_experiment_set.name,
        "total_experiments": total_experiments,
        "completed": completed,
        "running": running,
        "failed": failed,
        "pending": pending,
        "status": status,
        "progress": progress,
        "started_at": started_at,
        "estimated_completion": estimated_completion
    }


async def schedule_experiment_set(
    db: Session, experiment_set_id: int, schedule: schemas.ScheduleExperimentSet
) -> Dict[str, Any]:
    """실험 세트의 실행을 스케줄링합니다."""
    logger.info(f"실험 세트 스케줄링: id={experiment_set_id}, schedule={schedule}")
    
    # 실험 세트 조회
    db_experiment_set = db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()
    
    if not db_experiment_set:
        raise ValueError(f"실험 세트를 찾을 수 없습니다: id={experiment_set_id}")
    
    # TODO: 실제 스케줄링 로직 구현
    # 현재는 더미 함수로, 스케줄링 시스템 구현 후 완성 필요
    
    # 스케줄 정보 반환
    return {
        "experiment_set_id": experiment_set_id,
        "scheduled_time": schedule.scheduled_time,
        "status": "scheduled"
    }


async def get_experiment_set_results(
    db: Session, experiment_set_id: int, run_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """실험 세트의 결과를 조회합니다."""
    # 실험 세트 조회
    db_experiment_set = db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()
    
    if not db_experiment_set:
        return None
    
    # 실험 목록 조회
    experiments = db.query(models.Experiment).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    ).all()
    
    # 결과 쿼리 기본 설정
    results_query = db.query(models.ExperimentResult).join(
        models.Experiment, 
        models.ExperimentResult.experiment_id == models.Experiment.id
    ).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    )
    
    # run_id가 지정된 경우 필터링
    if run_id:
        results_query = results_query.filter(models.ExperimentResult.run_id == run_id)
    
    # 평가 쿼리 기본 설정
    evaluations_query = db.query(models.Evaluation).join(
        models.ExperimentResult,
        models.Evaluation.result_id == models.ExperimentResult.id
    ).join(
        models.Experiment,
        models.ExperimentResult.experiment_id == models.Experiment.id
    ).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    )
    
    # run_id가 지정된 경우 필터링
    if run_id:
        evaluations_query = evaluations_query.join(
            models.ExperimentResult,
            models.Evaluation.result_id == models.ExperimentResult.id
        ).filter(
            models.ExperimentResult.run_id == run_id
        )
    
    # 결과 및 평가 데이터 로드
    results = results_query.all()
    evaluations = evaluations_query.all()
    
    # 실험별 요약 데이터 생성
    experiment_summaries = []
    for experiment in experiments:
        # 실험 결과 필터링
        experiment_results = [r for r in results if r.experiment_id == experiment.id]
        
        # 평균 실행 시간 계산
        completed_results = [r for r in experiment_results if r.status == "completed" and r.execution_time]
        avg_execution_time = sum(r.execution_time for r in completed_results) / len(completed_results) if completed_results else None
        
        # 평가 점수 집계
        avg_scores = {}
        for metric in set(e.metric_name for e in evaluations):
            metric_scores = [e.score for e in evaluations 
                             if e.result_id in [r.id for r in experiment_results] 
                             and e.metric_name == metric
                             and e.score is not None]
            if metric_scores:
                avg_scores[metric] = sum(metric_scores) / len(metric_scores)
        
        # 가중 점수 계산
        weighted_score = None
        if avg_scores:
            # 가중치 조회
            weights = {}
            for metric in avg_scores.keys():
                weight_record = db.query(models.EvaluationWeight).filter(
                    models.EvaluationWeight.experiment_set_id == experiment_set_id,
                    models.EvaluationWeight.metric_name == metric
                ).first()
                weights[metric] = weight_record.weight if weight_record else 1.0 / len(avg_scores)
            
            # 가중 점수 계산
            weighted_score = sum(avg_scores[metric] * weights[metric] for metric in avg_scores.keys())
        
        # 요약 데이터 추가
        experiment_summaries.append({
            "id": experiment.id,
            "name": experiment.name,
            "model": experiment.model,
            "avg_execution_time": avg_execution_time,
            "avg_scores": avg_scores,
            "weighted_score": weighted_score,
            "rank": None  # 순위는 나중에 계산
        })
    
    # 가중 점수 기준으로 순위 계산
    if experiment_summaries and all(s["weighted_score"] is not None for s in experiment_summaries):
        sorted_summaries = sorted(experiment_summaries, key=lambda x: x["weighted_score"], reverse=True)
        for i, summary in enumerate(sorted_summaries):
            summary["rank"] = i + 1
    
    # 최고 성능 실험 ID 찾기
    best_experiment_id = None
    if experiment_summaries:
        valid_summaries = [s for s in experiment_summaries if s["weighted_score"] is not None]
        if valid_summaries:
            best_experiment_id = max(valid_summaries, key=lambda x: x["weighted_score"])["id"]
    
    # 완료 시간 계산
    completed_at = max([r.created_at for r in results if r.status == "completed"], default=None) if results else None
    
    # 평가 메트릭 목록
    evaluation_metrics = list(set(e.metric_name for e in evaluations))
    
    return {
        "experiment_set_id": experiment_set_id,
        "name": db_experiment_set.name,
        "run_id": run_id,
        "completed_at": completed_at,
        "experiment_summaries": experiment_summaries,
        "best_experiment_id": best_experiment_id,
        "evaluation_metrics": evaluation_metrics
    }
