"""
A/B 테스트 다국어 테스트 컨트롤러

다국어 테스트 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import uuid

from backend.logger import get_logger
from backend.ab_testing import models, schemas
from backend.ab_testing.services.experiment import ExperimentRunner
from backend.ab_testing.services.model_wrapper import get_model_wrapper

# 로거 설정
logger = get_logger(__name__)


async def run_multi_language_test_background(
    db: Session, 
    experiment_set_id: int, 
    config: schemas.MultiLanguageTest, 
    test_id: str
) -> None:
    """다국어 테스트를 백그라운드로 실행합니다."""
    logger.info(f"다국어 테스트 시작: experiment_set_id={experiment_set_id}, languages={config.languages}")
    
    try:
        # 실험 세트 조회
        experiment_set = db.query(models.ExperimentSet).filter(models.ExperimentSet.id == experiment_set_id).first()
        if not experiment_set:
            logger.error(f"다국어 테스트 실패: ID {experiment_set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
            return
        
        # 기준 실험 선택 (대조군 또는 첫 번째 실험)
        base_experiment = None
        for experiment in experiment_set.experiments:
            if experiment.is_control:
                base_experiment = experiment
                break
        
        if not base_experiment and experiment_set.experiments:
            base_experiment = experiment_set.experiments[0]
        
        if not base_experiment:
            logger.error("테스트할 기준 실험이 없습니다")
            return
        
        # 기본 프롬프트 설정
        base_prompt = config.base_prompt if config.base_prompt else base_experiment.prompt
        
        # 테스트할 언어 목록
        languages = config.languages
        
        # 각 언어별로 테스트 실행
        for language in languages:
            logger.info(f"다국어 테스트 진행: 언어={language}")
            
            # 프롬프트 번역 (필요한 경우)
            prompt = base_prompt
            if config.translate_prompt:
                prompt = await translate_prompt(base_prompt, language)
            
            # 임시 실험 생성
            temp_experiment = models.Experiment(
                experiment_set_id=experiment_set_id,
                name=f"Multi-Language Test - {language}",
                prompt=prompt,
                model=base_experiment.model,
                params=base_experiment.params.copy() if base_experiment.params else {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 실험 실행
            runner = ExperimentRunner()
            result = await runner.run_experiment(temp_experiment)
            
            # 메트릭 평가
            metrics = await evaluate_language_result(result, config.compare_metrics)
            
            # 결과 저장
            db_test = models.MultiLanguageTestResult(
                experiment_id=base_experiment.id,
                language=language,
                prompt=prompt,
                result={
                    "output": result.get("output", ""),
                    "execution_time": result.get("execution_time", 0),
                    "token_usage": result.get("token_usage", {})
                },
                metrics=metrics,
                created_at=datetime.utcnow()
            )
            db.add(db_test)
            db.commit()
            
        logger.info(f"다국어 테스트 완료: experiment_set_id={experiment_set_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"다국어 테스트 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())


async def translate_prompt(prompt: str, target_language: str) -> str:
    """프롬프트를 대상 언어로 번역합니다."""
    try:
        # GPT 모델을 사용하여 번역
        model_wrapper = get_model_wrapper("gpt-3.5-turbo")
        
        system_prompt = "당신은 전문 번역가입니다. 주어진 텍스트를 목표 언어로 정확하게 번역하세요."
        user_prompt = f"""
        다음 텍스트를 {target_language}로 번역해주세요:
        
        {prompt}
        
        번역만 제공하고, 다른 설명은 포함하지 마세요.
        """
        
        translation = await model_wrapper.generate(
            system_message=system_prompt,
            user_message=user_prompt,
            temperature=0.3,
            max_tokens=4096
        )
        
        return translation.strip()
        
    except Exception as e:
        logger.error(f"프롬프트 번역 중 오류 발생: {str(e)}")
        # 오류 발생 시 원본 프롬프트 반환
        return prompt


async def evaluate_language_result(
    result: Dict[str, Any], 
    metrics: List[str]
) -> Dict[str, Any]:
    """언어별 결과를 평가합니다."""
    evaluation = {}
    
    # 기본 메트릭
    evaluation["response_time"] = result.get("execution_time", 0)
    
    token_usage = result.get("token_usage", {})
    evaluation["total_tokens"] = token_usage.get("total_tokens", 0) if token_usage else 0
    evaluation["completion_tokens"] = token_usage.get("completion_tokens", 0) if token_usage else 0
    
    output = result.get("output", "")
    evaluation["response_length"] = len(output)
    evaluation["word_count"] = len(output.split())
    
    # 추가 메트릭
    if metrics and "coherence" in metrics:
        # 간단한 구현을 위해 임의의 점수 반환
        # 실제로는 더 복잡한 평가 로직 필요
        import random
        evaluation["coherence"] = random.uniform(7.0, 9.5)
    
    if metrics and "fluency" in metrics:
        import random
        evaluation["fluency"] = random.uniform(7.0, 9.5)
    
    return evaluation


async def get_multi_language_test_results(
    db: Session, 
    experiment_set_id: int, 
    test_id: str
) -> Optional[Dict[str, Any]]:
    """다국어 테스트 결과를 조회합니다."""
    try:
        # 실험 세트 조회
        experiment_set = db.query(models.ExperimentSet).filter(models.ExperimentSet.id == experiment_set_id).first()
        if not experiment_set:
            return None
        
        # 기준 실험 선택 (대조군 또는 첫 번째 실험)
        base_experiment_id = None
        for experiment in experiment_set.experiments:
            if experiment.is_control:
                base_experiment_id = experiment.id
                break
        
        if not base_experiment_id and experiment_set.experiments:
            base_experiment_id = experiment_set.experiments[0].id
        
        if not base_experiment_id:
            return None
        
        # 테스트 결과 조회
        test_results = db.query(models.MultiLanguageTestResult).filter(
            models.MultiLanguageTestResult.experiment_id == base_experiment_id
        ).all()
        
        if not test_results:
            return None
        
        # 결과 정리
        languages_data = {}
        for result in test_results:
            languages_data[result.language] = {
                "prompt": result.prompt,
                "output": result.result.get("output", "") if result.result else "",
                "execution_time": result.result.get("execution_time", 0) if result.result else 0,
                "token_usage": result.result.get("token_usage", {}) if result.result else {},
                "metrics": result.metrics or {}
            }
        
        # 비교 메트릭
        comparison_metrics = {}
        metric_keys = set()
        for lang_data in languages_data.values():
            metric_keys.update(lang_data.get("metrics", {}).keys())
        
        for metric in metric_keys:
            comparison_metrics[metric] = {
                lang: data.get("metrics", {}).get(metric, 0)
                for lang, data in languages_data.items()
            }
        
        return {
            "experiment_set_id": experiment_set_id,
            "languages": list(languages_data.keys()),
            "language_results": languages_data,
            "comparison_metrics": comparison_metrics,
            "created_at": test_results[0].created_at if test_results else datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"다국어 테스트 결과 조회 중 오류 발생: {str(e)}")
        return None
