"""
A/B 테스트 평가 컨트롤러

실험 결과 평가 관련 비즈니스 로직을 구현합니다.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.logger import get_logger
from backend.database.connection import SessionLocal as DBSession
from . import models, schemas
from .config import ab_testing_settings
from .services.evaluator import Evaluator

# 로거 설정
logger = get_logger(__name__)


async def evaluate_experiment_set_background(
    db: Session, 
    experiment_set_id: int, 
    run_id: Optional[str], 
    evaluation_config: Optional[schemas.EvaluationConfig],
    task_id: str
):
    """백그라운드에서 실험 세트 결과를 평가합니다."""
    logger.info(f"실험 세트 평가 시작: id={experiment_set_id}, run_id={run_id}, task_id={task_id}")
    
    try:
        # 세션 복제 (백그라운드 작업용)
        db_copy = DBSession(bind=db.get_bind())
        
        # 평가자 생성
        evaluator = Evaluator(db_copy)
        
        # 평가 설정
        metrics = evaluation_config.metrics if evaluation_config and evaluation_config.metrics else ab_testing_settings.default_metrics
        weights = evaluation_config.weights if evaluation_config and evaluation_config.weights else ab_testing_settings.default_weights
        
        # 평가 실행
        await evaluator.evaluate_experiment_set(
            experiment_set_id,
            run_id=run_id,
            metrics=metrics,
            weights=weights,
            llm_evaluator=evaluation_config.llm_evaluator if evaluation_config else None,
            llm_evaluator_params=evaluation_config.llm_evaluator_params if evaluation_config else None,
            reference_text=evaluation_config.reference_text if evaluation_config else None
        )
        
        logger.info(f"실험 세트 평가 완료: id={experiment_set_id}, run_id={run_id}, task_id={task_id}")
        
    except Exception as e:
        logger.error(f"실험 세트 평가 실패: id={experiment_set_id}, run_id={run_id}, task_id={task_id}, error={str(e)}")
    finally:
        if 'db_copy' in locals():
            db_copy.close()


async def get_experiment_set_evaluations(
    db: Session, experiment_set_id: int, run_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """실험 세트 평가 결과를 조회합니다."""
    # 실험 세트 조회
    db_experiment_set = db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()
    
    if not db_experiment_set:
        return None
    
    # 평가 가중치 조회
    weights = db.query(models.EvaluationWeight).filter(
        models.EvaluationWeight.experiment_set_id == experiment_set_id
    ).all()
    
    weights_dict = {w.metric_name: w.weight for w in weights}
    
    # 실험 결과 ID를 조회하는 서브쿼리 생성
    result_ids_subquery = select([models.ExperimentResult.id]).join(
        models.Experiment,
        models.ExperimentResult.experiment_id == models.Experiment.id
    ).filter(
        models.Experiment.experiment_set_id == experiment_set_id
    )
    
    if run_id:
        result_ids_subquery = result_ids_subquery.filter(models.ExperimentResult.run_id == run_id)
    
    # 평가 결과 조회
    evaluations = db.query(models.Evaluation).filter(
        models.Evaluation.result_id.in_(result_ids_subquery)
    ).all()
    
    # 메트릭별 통계
    metrics = {}
    for evaluation in evaluations:
        if evaluation.metric_name not in metrics:
            metrics[evaluation.metric_name] = {
                "scores": [],
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "weight": weights_dict.get(evaluation.metric_name, 1.0 / len(set(e.metric_name for e in evaluations)) if evaluations else 0)
            }
        
        if evaluation.score is not None:
            metrics[evaluation.metric_name]["scores"].append(evaluation.score)
    
    # 통계 계산
    for metric_name, data in metrics.items():
        scores = data["scores"]
        if scores:
            data["avg_score"] = sum(scores) / len(scores)
            data["min_score"] = min(scores)
            data["max_score"] = max(scores)
    
    # 실험별 평가 결과 집계
    experiment_evaluations = {}
    for experiment in db.query(models.Experiment).filter(models.Experiment.experiment_set_id == experiment_set_id).all():
        # 실험 결과 조회
        results_query = db.query(models.ExperimentResult).filter(
            models.ExperimentResult.experiment_id == experiment.id
        )
        
        if run_id:
            results_query = results_query.filter(models.ExperimentResult.run_id == run_id)
        
        results = results_query.all()
        
        # 결과가 없으면 건너뛰기
        if not results:
            continue
        
        # 실험별 평가 결과 집계
        experiment_metrics = {}
        for result in results:
            result_evaluations = db.query(models.Evaluation).filter(
                models.Evaluation.result_id == result.id
            ).all()
            
            for evaluation in result_evaluations:
                if evaluation.metric_name not in experiment_metrics:
                    experiment_metrics[evaluation.metric_name] = []
                
                if evaluation.score is not None:
                    experiment_metrics[evaluation.metric_name].append(evaluation.score)
        
        # 평균 점수 계산
        avg_scores = {}
        for metric_name, scores in experiment_metrics.items():
            if scores:
                avg_scores[metric_name] = sum(scores) / len(scores)
        
        # 가중 점수 계산
        weighted_score = None
        if avg_scores:
            weighted_score = sum(avg_scores[metric] * weights_dict.get(metric, 1.0 / len(avg_scores)) for metric in avg_scores.keys())
        
        # 결과 저장
        experiment_evaluations[experiment.id] = {
            "name": experiment.name,
            "model": experiment.model,
            "metrics": avg_scores,
            "weighted_score": weighted_score
        }
    
    # 순위 계산
    if experiment_evaluations:
        sorted_experiments = sorted(
            experiment_evaluations.items(),
            key=lambda x: x[1]["weighted_score"] if x[1]["weighted_score"] is not None else float('-inf'),
            reverse=True
        )
        
        for i, (exp_id, data) in enumerate(sorted_experiments):
            experiment_evaluations[exp_id]["rank"] = i + 1
    
    return {
        "experiment_set_id": experiment_set_id,
        "name": db_experiment_set.name,
        "metrics": metrics,
        "experiment_evaluations": experiment_evaluations,
        "run_id": run_id
    }
