"""
A/B 테스트 일관성 테스트 컨트롤러

실험 응답의 일관성 테스트 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import numpy as np
import uuid

from backend.logger import get_logger
from backend.ab_testing import models, schemas
from backend.ab_testing.services.experiment import ExperimentRunner

# 로거 설정
logger = get_logger(__name__)


async def run_consistency_test(
    db: Session, 
    experiment_id: int, 
    iterations: int, 
    test_id: str
) -> None:
    """실험 일관성 테스트를 실행합니다."""
    logger.info(f"일관성 테스트 시작: experiment_id={experiment_id}, iterations={iterations}")
    
    try:
        # 실험 조회
        experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
        if not experiment:
            logger.error(f"일관성 테스트 실패: ID {experiment_id}에 해당하는 실험을 찾을 수 없습니다")
            return
        
        # 결과 저장 배열
        results = []
        metrics = {}
        
        # 여러번 반복 실행
        runner = ExperimentRunner()
        for i in range(iterations):
            logger.info(f"일관성 테스트 반복 {i+1}/{iterations}")
            
            # 실험 실행
            result = await runner.run_experiment(experiment)
            
            # 결과 저장
            results.append(result)
            
            # 메트릭별로 값 수집
            for key, value in extract_metrics(result).items():
                if key not in metrics:
                    metrics[key] = []
                metrics[key].append(value)
        
        # 메트릭별 분산 계산
        variance_scores = {}
        for key, values in metrics.items():
            if len(values) >= 2:  # 분산 계산을 위해서는 최소 2개의 데이터가 필요함
                variance_scores[key] = calculate_variance(values)
        
        # 일관성 점수 계산
        consistency_rating = calculate_consistency_rating(variance_scores)
        
        # 이상치 개수 계산
        outliers_count = count_outliers(metrics)
        
        # 일관성 여부 판단
        is_consistent = consistency_rating >= 0.7  # 70% 이상이면 일관적
        
        # 결과 저장
        db_test = models.ConsistencyTest(
            experiment_id=experiment_id,
            test_id=test_id,
            iterations=iterations,
            variance_scores=variance_scores,
            consistency_rating=consistency_rating,
            outliers_count=outliers_count,
            is_consistent=is_consistent,
            created_at=datetime.utcnow()
        )
        db.add(db_test)
        db.commit()
        
        logger.info(f"일관성 테스트 완료: experiment_id={experiment_id}, consistency_rating={consistency_rating}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"일관성 테스트 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())


def extract_metrics(result: Dict[str, Any]) -> Dict[str, float]:
    """실험 결과에서 메트릭을 추출합니다."""
    metrics = {}
    
    # 토큰 사용량
    if "token_usage" in result:
        token_usage = result["token_usage"]
        if token_usage:
            metrics["total_tokens"] = token_usage.get("total_tokens", 0)
            metrics["prompt_tokens"] = token_usage.get("prompt_tokens", 0)
            metrics["completion_tokens"] = token_usage.get("completion_tokens", 0)
    
    # 응답 시간
    if "execution_time" in result:
        metrics["execution_time"] = result.get("execution_time", 0)
    
    # 응답 길이
    if "output" in result:
        metrics["response_length"] = len(result.get("output", ""))
        metrics["word_count"] = len(result.get("output", "").split())
    
    return metrics


def calculate_variance(values: List[float]) -> float:
    """값 목록의 정규화된 분산을 계산합니다."""
    if not values or len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    
    # 평균으로 정규화된 분산 (변동 계수)
    if mean != 0:
        normalized_variance = (variance ** 0.5) / abs(mean)  # 표준편차 / 평균 = 변동계수
    else:
        normalized_variance = 0.0
    
    return min(normalized_variance, 1.0)  # 0~1 사이 값으로 제한


def calculate_consistency_rating(variance_scores: Dict[str, float]) -> float:
    """분산 점수로부터 일관성 점수를 계산합니다."""
    if not variance_scores:
        return 0.0
    
    # 각 메트릭의 일관성 점수 계산 (분산이 낮을수록 일관성이 높음)
    consistency_scores = {key: 1.0 - value for key, value in variance_scores.items()}
    
    # 전체 일관성 점수 계산 (가중 평균)
    # 중요도에 따라 가중치 설정
    weights = {
        "total_tokens": 0.2,
        "prompt_tokens": 0.1,
        "completion_tokens": 0.2,
        "execution_time": 0.1,
        "response_length": 0.2,
        "word_count": 0.2
    }
    
    total_weight = 0
    weighted_sum = 0
    
    for key, score in consistency_scores.items():
        weight = weights.get(key, 0.1)
        weighted_sum += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_sum / total_weight


def count_outliers(metrics: Dict[str, List[float]]) -> int:
    """메트릭별 이상치 개수를 계산합니다."""
    total_outliers = 0
    
    for key, values in metrics.items():
        if len(values) < 4:  # 이상치 탐지를 위해 충분한 데이터가 필요함
            continue
        
        # IQR 방식으로 이상치 탐지
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [x for x in values if x < lower_bound or x > upper_bound]
        total_outliers += len(outliers)
    
    return total_outliers


async def get_test_results(
    db: Session, 
    experiment_id: int, 
    test_id: str
) -> Optional[Dict[str, Any]]:
    """일관성 테스트 결과를 조회합니다."""
    try:
        test = db.query(models.ConsistencyTest).filter(
            models.ConsistencyTest.experiment_id == experiment_id,
            models.ConsistencyTest.test_id == test_id
        ).first()
        
        if not test:
            return None
        
        result = {
            "experiment_id": test.experiment_id,
            "test_id": test.test_id,
            "iterations": test.iterations,
            "variance_scores": test.variance_scores,
            "consistency_rating": test.consistency_rating,
            "outliers_count": test.outliers_count,
            "is_consistent": test.is_consistent,
            "created_at": test.created_at
        }
        
        return result
        
    except Exception as e:
        logger.error(f"일관성 테스트 결과 조회 중 오류 발생: {str(e)}")
        return None
