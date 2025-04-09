"""
A/B 테스트 모델 최적화 컨트롤러

모델 선택 최적화 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import traceback

from backend.logger import get_logger
from backend.ab_testing import models, schemas
from backend.ab_testing.services.experiment import ExperimentRunner
from backend.ab_testing.controllers.optimization_utils import (
    save_optimization_result, 
    calculate_improvement,
    evaluate_result
)

# 로거 설정
logger = get_logger(__name__)


async def optimize_model(
    db: Session, 
    experiment_set: models.ExperimentSet, 
    optimization_request: schemas.OptimizationRequest, 
    task_id: str
) -> None:
    """모델 선택 최적화를 수행합니다."""
    logger.info(f"모델 최적화 시작: experiment_set_id={experiment_set.id}")
    
    # 기준 실험 선택 (대조군 또는 첫 번째 실험)
    base_experiment = None
    for experiment in experiment_set.experiments:
        if experiment.is_control:
            base_experiment = experiment
            break
    
    if not base_experiment and experiment_set.experiments:
        base_experiment = experiment_set.experiments[0]
    
    if not base_experiment:
        logger.error("최적화할 기준 실험이 없습니다")
        save_optimization_result(db, experiment_set.id, task_id, "model", None, None, 0.0, 0, 
                               {"error": "최적화할 기준 실험이 없습니다"}, "failed")
        return
    
    # 원본 모델 저장
    original_model = base_experiment.model
    
    # 최적화 대상 지표
    target_metric = optimization_request.target_metric
    
    # 최적화 실행 기록
    history = []
    current_best_model = original_model
    current_best_score = -float('inf')
    
    # 테스트할 모델 목록
    test_models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "mistral-large"
    ]
    
    if original_model in test_models:
        test_models.remove(original_model)
    
    # 최대 반복 횟수 제한
    max_iterations = min(len(test_models), optimization_request.max_iterations)
    
    try:
        # 모델 최적화 실행
        for iteration in range(max_iterations):
            logger.info(f"모델 최적화 반복 {iteration+1}/{max_iterations}")
            
            # 테스트할 모델
            test_model = test_models[iteration]
            
            # 임시 실험 생성
            temp_experiment = models.Experiment(
                experiment_set_id=experiment_set.id,
                name=f"Model Optimization {iteration+1}",
                prompt=base_experiment.prompt,
                model=test_model,
                params=base_experiment.params.copy() if base_experiment.params else {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 실험 실행
            runner = ExperimentRunner()
            result = await runner.run_experiment(temp_experiment)
            
            # 평가
            evaluation_result = await evaluate_optimized_model(
                db, 
                result, 
                target_metric, 
                experiment_set.id
            )
            
            # 결과 기록
            score = evaluation_result.get('score', 0.0)
            history.append({
                'iteration': iteration + 1,
                'model': test_model,
                'score': score,
                'evaluation': evaluation_result
            })
            
            # 최고 점수 업데이트
            if score > current_best_score:
                current_best_score = score
                current_best_model = test_model
                
                # 최적화 결과 중간 저장
                save_optimization_result(
                    db, 
                    experiment_set.id, 
                    task_id, 
                    "model", 
                    original_model, 
                    current_best_model, 
                    (current_best_score / -float('inf')) * 100 if current_best_score > 0 else 0, 
                    iteration + 1, 
                    {"history": history}, 
                    "running"
                )
        
        # 최종 결과 저장
        improvement = calculate_improvement(0, current_best_score) if current_best_score > -float('inf') else 0
        
        save_optimization_result(
            db, 
            experiment_set.id, 
            task_id, 
            "model", 
            original_model, 
            current_best_model, 
            improvement, 
            max_iterations, 
            {"history": history}, 
            "completed"
        )
        
        logger.info(f"모델 최적화 완료: experiment_set_id={experiment_set.id}, improvement={improvement}%")
        
    except Exception as e:
        logger.error(f"모델 최적화 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        
        save_optimization_result(
            db, 
            experiment_set.id, 
            task_id, 
            "model", 
            original_model, 
            current_best_model if current_best_score > -float('inf') else None, 
            0.0, 
            len(history), 
            {"history": history, "error": str(e)}, 
            "failed"
        )


async def evaluate_optimized_model(
    db: Session, 
    result: Dict[str, Any], 
    metric: str, 
    experiment_set_id: int
) -> Dict[str, Any]:
    """최적화된 모델을 평가합니다."""
    return await evaluate_result(db, result, metric, experiment_set_id)
