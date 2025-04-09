"""
A/B 테스트 프롬프트 최적화 컨트롤러

프롬프트 최적화 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import traceback

from backend.logger import get_logger
from backend.ab_testing import models, schemas
from backend.ab_testing.services.experiment import ExperimentRunner
from backend.ab_testing.services.model_wrapper import get_model_wrapper
from backend.ab_testing.controllers.optimization_utils import (
    save_optimization_result, 
    calculate_improvement,
    evaluate_result
)

# 로거 설정
logger = get_logger(__name__)


async def optimize_prompt(
    db: Session, 
    experiment_set: models.ExperimentSet, 
    optimization_request: schemas.OptimizationRequest, 
    task_id: str
) -> None:
    """프롬프트 최적화를 수행합니다."""
    logger.info(f"프롬프트 최적화 시작: experiment_set_id={experiment_set.id}")
    
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
        save_optimization_result(db, experiment_set.id, task_id, "prompt", None, None, 0.0, 0, 
                               {"error": "최적화할 기준 실험이 없습니다"}, "failed")
        return
    
    # 원본 프롬프트 저장
    original_prompt = base_experiment.prompt
    
    # 최적화 대상 지표
    target_metric = optimization_request.target_metric
    
    # 최적화 실행 기록
    history = []
    current_best_prompt = original_prompt
    current_best_score = -float('inf')
    
    # LLM 기반 프롬프트 최적화 과정
    try:
        # 프롬프트 최적화를 위한 LLM 모델 선택
        model_name = "gpt-4"  # 고급 모델 사용 (프롬프트 최적화에 유리)
        model_wrapper = get_model_wrapper(model_name)
        
        # 최적화 반복
        for iteration in range(optimization_request.max_iterations):
            logger.info(f"프롬프트 최적화 반복 {iteration+1}/{optimization_request.max_iterations}")
            
            # 최적화 프롬프트 생성
            optimization_system_prompt = f"""
            당신은 LLM 프롬프트 최적화 전문가입니다. 주어진 원본 프롬프트를 개선하여 {target_metric} 지표를 향상시키는 것이 목표입니다.
            프롬프트를 개선할 때는 다음 사항을 고려하세요:
            1. 명확성: 지시사항을 명확하게 합니다.
            2. 구체성: 필요한 세부 정보를 포함합니다.
            3. 구조화: 논리적 순서로 정보를 제시합니다.
            4. 맥락: 필요한 배경 정보를 제공합니다.
            
            이전 시도의 결과를 참고하여 더 나은 프롬프트를 제안하세요.
            """
            
            # 이전 결과 포함
            optimization_user_prompt = f"""
            원본 프롬프트:
            {original_prompt}
            
            최적화 목표: {target_metric} 점수 향상
            
            이전 시도 결과:
            """
            
            for idx, entry in enumerate(history):
                optimization_user_prompt += f"""
                시도 {idx+1}:
                프롬프트: {entry['prompt']}
                {target_metric} 점수: {entry['score']}
                """
            
            optimization_user_prompt += """
            위 정보를 바탕으로 더 나은 프롬프트를 제안해주세요. 모든 필수 정보를 유지하면서, 원본보다 목표 지표를 향상시킬 수 있는 프롬프트를 작성하세요.
            최적화된 프롬프트만 제공하고, 다른 설명은 포함하지 마세요.
            """
            
            # LLM에 최적화 요청
            response = await model_wrapper.generate(
                system_message=optimization_system_prompt,
                user_message=optimization_user_prompt,
                temperature=0.7,
                max_tokens=4096
            )
            
            # 최적화된 프롬프트 추출
            optimized_prompt = response.strip()
            
            # 최적화된 프롬프트 평가
            # 임시 실험 생성
            temp_experiment = models.Experiment(
                experiment_set_id=experiment_set.id,
                name=f"Prompt Optimization {iteration+1}",
                prompt=optimized_prompt,
                model=base_experiment.model,
                params=base_experiment.params.copy() if base_experiment.params else {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 실험 실행
            runner = ExperimentRunner()
            result = await runner.run_experiment(temp_experiment)
            
            # 평가
            evaluation_result = await evaluate_result(
                db, 
                result, 
                target_metric, 
                experiment_set.id
            )
            
            # 결과 기록
            score = evaluation_result.get('score', 0.0)
            history.append({
                'iteration': iteration + 1,
                'prompt': optimized_prompt,
                'score': score,
                'evaluation': evaluation_result
            })
            
            # 최고 점수 업데이트
            if score > current_best_score:
                current_best_score = score
                current_best_prompt = optimized_prompt
                
                # 최적화 결과 중간 저장
                save_optimization_result(
                    db, 
                    experiment_set.id, 
                    task_id, 
                    "prompt", 
                    original_prompt, 
                    current_best_prompt, 
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
            "prompt", 
            original_prompt, 
            current_best_prompt, 
            improvement, 
            optimization_request.max_iterations, 
            {"history": history}, 
            "completed"
        )
        
        logger.info(f"프롬프트 최적화 완료: experiment_set_id={experiment_set.id}, improvement={improvement}%")
        
    except Exception as e:
        logger.error(f"프롬프트 최적화 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        
        save_optimization_result(
            db, 
            experiment_set.id, 
            task_id, 
            "prompt", 
            original_prompt, 
            current_best_prompt if current_best_score > -float('inf') else None, 
            0.0, 
            len(history), 
            {"history": history, "error": str(e)}, 
            "failed"
        )


async def evaluate_optimized_prompt(
    db: Session, 
    result: Dict[str, Any], 
    metric: str, 
    experiment_set_id: int
) -> Dict[str, Any]:
    """최적화된 프롬프트를 평가합니다."""
    return await evaluate_result(db, result, metric, experiment_set_id)
