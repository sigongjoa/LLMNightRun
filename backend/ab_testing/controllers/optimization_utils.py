"""
A/B 테스트 최적화 유틸리티 함수

최적화 과정에서 사용되는 공통 유틸리티 함수를 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union
from datetime import datetime

from backend.logger import get_logger
from backend.ab_testing import models

# 로거 설정
logger = get_logger(__name__)


def save_optimization_result(
    db: Session,
    experiment_set_id: int,
    optimization_id: str,
    target: str,
    original_value: Optional[Any],
    optimized_value: Optional[Any],
    improvement: float,
    iterations: int,
    history: Dict[str, Any],
    status: str
) -> models.PromptOptimization:
    """최적화 결과를 데이터베이스에 저장합니다."""
    try:
        # 기존 결과 조회
        existing_result = db.query(models.PromptOptimization).filter(
            models.PromptOptimization.experiment_set_id == experiment_set_id,
            models.PromptOptimization.optimization_id == optimization_id
        ).first()
        
        if existing_result:
            # 기존 결과 업데이트
            existing_result.optimized_prompt = optimized_value if target == "prompt" else existing_result.optimized_prompt
            existing_result.improvement = improvement
            existing_result.iterations = iterations
            existing_result.history = history
            existing_result.status = status
            existing_result.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_result)
            return existing_result
        else:
            # 새 결과 생성
            original_value_str = str(original_value) if original_value is not None else None
            optimized_value_str = str(optimized_value) if optimized_value is not None else None
            
            new_result = models.PromptOptimization(
                experiment_set_id=experiment_set_id,
                optimization_id=optimization_id,
                target_metric=target,
                original_prompt=original_value_str if target == "prompt" else None,
                optimized_prompt=optimized_value_str if target == "prompt" else None,
                improvement=improvement,
                iterations=iterations,
                history=history,
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_result)
            db.commit()
            db.refresh(new_result)
            return new_result
            
    except Exception as e:
        db.rollback()
        logger.error(f"최적화 결과 저장 중 오류 발생: {str(e)}")
        raise


def calculate_improvement(baseline_score: float, optimized_score: float) -> float:
    """최적화 성능 향상도를 계산합니다."""
    if baseline_score == 0:
        return 100.0 if optimized_score > 0 else 0.0
    
    return ((optimized_score - baseline_score) / abs(baseline_score)) * 100.0


async def get_optimization_results(
    db: Session, 
    experiment_set_id: int, 
    task_id: str
) -> Optional[Dict[str, Any]]:
    """최적화 결과를 조회합니다."""
    try:
        optimization = db.query(models.PromptOptimization).filter(
            models.PromptOptimization.experiment_set_id == experiment_set_id,
            models.PromptOptimization.optimization_id == task_id
        ).first()
        
        if not optimization:
            return None
        
        result = {
            "target": optimization.target_metric,
            "original_value": optimization.original_prompt,
            "optimized_value": optimization.optimized_prompt,
            "improvement": optimization.improvement,
            "iterations": optimization.iterations,
            "history": optimization.history,
            "status": optimization.status,
            "created_at": optimization.created_at,
            "updated_at": optimization.updated_at
        }
        
        return result
        
    except Exception as e:
        logger.error(f"최적화 결과 조회 중 오류 발생: {str(e)}")
        return None


async def evaluate_result(
    db: Session, 
    result: Dict[str, Any], 
    metric: str, 
    experiment_set_id: int
) -> Dict[str, Any]:
    """실험 결과를 평가합니다."""
    # TODO: 실제 평가 로직 구현
    # 간단한 구현을 위해 임의의 점수 반환
    
    if metric == "response_time":
        score = result.get("execution_time", 0)
        score = 10.0 - min(score, 10.0)  # 응답 시간이 빠를수록 높은 점수
    elif metric == "token_usage":
        token_usage = result.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 0) or 0
        score = 10.0 - min(total_tokens / 1000, 10.0)  # 토큰 사용량이 적을수록 높은 점수
    elif metric == "cost":
        token_usage = result.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 0) or 0
        score = 10.0 - min(total_tokens / 1000, 10.0)  # 비용이 적을수록 높은 점수
    else:
        # 기본적으로 임의의 점수 반환
        import random
        score = random.uniform(7.0, 9.5)
    
    return {
        "metric": metric,
        "score": score,
        "details": {
            "raw_output": result.get("output", ""),
            "execution_time": result.get("execution_time", 0),
            "token_usage": result.get("token_usage", {})
        }
    }
