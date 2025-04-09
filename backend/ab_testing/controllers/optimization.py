"""
A/B 테스트 최적화 컨트롤러

프롬프트, 파라미터 최적화 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import asyncio
import traceback

from backend.logger import get_logger
from backend.ab_testing import models, schemas
from backend.ab_testing.controllers.optimization_prompt import optimize_prompt
from backend.ab_testing.controllers.optimization_parameter import optimize_parameters
from backend.ab_testing.controllers.optimization_model import optimize_model
from backend.ab_testing.controllers.optimization_utils import (
    save_optimization_result, 
    calculate_improvement,
    get_optimization_results
)

# 로거 설정
logger = get_logger(__name__)


async def optimize_experiment_set_background(
    db: Session, 
    set_id: int, 
    optimization_request: schemas.OptimizationRequest, 
    task_id: str
) -> None:
    """실험 세트 최적화를 백그라운드로 실행합니다."""
    logger.info(f"최적화 시작: set_id={set_id}, target={optimization_request.optimization_target}")
    
    try:
        # 실험 세트 조회
        experiment_set = db.query(models.ExperimentSet).filter(models.ExperimentSet.id == set_id).first()
        if not experiment_set:
            logger.error(f"최적화 실패: ID {set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
            return
        
        # 최적화 대상에 따라 최적화 실행
        target = optimization_request.optimization_target
        if target == "prompt":
            await optimize_prompt(db, experiment_set, optimization_request, task_id)
        elif target == "parameters":
            await optimize_parameters(db, experiment_set, optimization_request, task_id)
        elif target == "model":
            await optimize_model(db, experiment_set, optimization_request, task_id)
        else:
            logger.error(f"지원되지 않는 최적화 대상: {target}")
            # 최적화 실패 상태 저장
            save_optimization_result(db, experiment_set.id, task_id, target, None, None, 0.0, 0, 
                                    {"error": f"지원되지 않는 최적화 대상: {target}"}, "failed")
    
    except Exception as e:
        logger.error(f"최적화 과정에서 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        # 최적화 실패 상태 저장
        save_optimization_result(db, set_id, task_id, optimization_request.optimization_target, 
                               None, None, 0.0, 0, {"error": str(e)}, "failed")


async def run_consistency_test_background(
    db: Session, 
    experiment_id: int, 
    iterations: int, 
    test_id: str
) -> None:
    """실험 일관성 테스트를 백그라운드로 실행합니다."""
    logger.info(f"일관성 테스트 시작: experiment_id={experiment_id}, iterations={iterations}")
    
    try:
        from backend.ab_testing.controllers.consistency_test import run_consistency_test
        await run_consistency_test(db, experiment_id, iterations, test_id)
    except Exception as e:
        logger.error(f"일관성 테스트 과정에서 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())


async def get_consistency_test_results(
    db: Session, 
    experiment_id: int, 
    test_id: str
) -> Optional[Dict[str, Any]]:
    """일관성 테스트 결과를 조회합니다."""
    try:
        from backend.ab_testing.controllers.consistency_test import get_test_results
        return await get_test_results(db, experiment_id, test_id)
    except Exception as e:
        logger.error(f"일관성 테스트 결과 조회 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return None
