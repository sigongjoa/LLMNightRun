"""
A/B 테스트 평가 서비스

실험 결과를 평가하는 서비스 클래스를 정의합니다.
"""

from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
import json

from backend.logger import get_logger
from backend.ab_testing import models
from backend.ab_testing.config import ab_testing_settings
from backend.services.llm_service import LLMService

# 로거 설정
logger = get_logger(__name__)


class Evaluator:
    """실험 평가 서비스 클래스"""
    
    def __init__(self, db: Session):
        """초기화"""
        self.db = db
        self.llm_service = LLMService()
        
        # 지원하는 평가 지표 목록
        self.supported_metrics = {
            "relevance": self._evaluate_relevance,
            "coherence": self._evaluate_coherence,
            "factuality": self._evaluate_factuality,
            "response_time": self._evaluate_response_time,
            "token_usage": self._evaluate_token_usage,
            "token_efficiency": self._evaluate_token_efficiency,
            "cost": self._evaluate_cost,
        }
    
    async def evaluate_experiment_set(
        self, experiment_set_id: int, metrics: List[str] = None, weights: Dict[str, float] = None,
        run_id: Optional[str] = None, reference_text: Optional[str] = None,
        llm_evaluator: Optional[str] = None, llm_evaluator_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """실험 세트의 모든 결과를 평가합니다."""
        # 기본값 설정
        metrics = metrics or ["relevance", "coherence", "response_time", "token_efficiency"]
        weights = weights or {}
        llm_evaluator = llm_evaluator or ab_testing_settings.default_evaluator_model
        llm_evaluator_params = llm_evaluator_params or {}
        
        # 실험 결과 쿼리
        results_query = self.db.query(models.ExperimentResult).join(
            models.Experiment, 
            models.ExperimentResult.experiment_id == models.Experiment.id
        ).filter(
            models.Experiment.experiment_set_id == experiment_set_id,
            models.ExperimentResult.status == "completed"
        )
        
        # run_id가 지정된 경우 필터링
        if run_id:
            results_query = results_query.filter(models.ExperimentResult.run_id == run_id)
        
        # 결과 로드
        results = results_query.all()
        if not results:
            logger.warning(f"평가할 결과 없음: experiment_set_id={experiment_set_id}")
            return {"success": False, "message": "No completed results to evaluate"}
        
        # 실험 정보 로드
        experiments = {}
        for result in results:
            if result.experiment_id not in experiments:
                experiments[result.experiment_id] = self.db.query(models.Experiment).filter(
                    models.Experiment.id == result.experiment_id
                ).first()
        
        # 평가 실행
        evaluation_results = []
        for result in results:
            experiment = experiments[result.experiment_id]
            
            for metric in metrics:
                # 기존 평가가 있는지 확인
                existing_eval = self.db.query(models.Evaluation).filter(
                    models.Evaluation.result_id == result.id,
                    models.Evaluation.metric_name == metric
                ).first()
                
                if existing_eval:
                    evaluation_results.append(existing_eval)
                    continue
                
                # 평가 실행
                try:
                    if metric in self.supported_metrics:
                        # 내장 평가 함수 사용
                        score, details = self.supported_metrics[metric](
                            result, experiment, reference_text
                        )
                    else:
                        # LLM 기반 평가 사용
                        score, details = await self._evaluate_with_llm(
                            result, experiment, metric, reference_text,
                            llm_evaluator, llm_evaluator_params
                        )
                    
                    # 평가 결과 저장
                    evaluation = models.Evaluation(
                        result_id=result.id,
                        metric_name=metric,
                        score=score,
                        details=details,
                        evaluator=llm_evaluator if metric not in self.supported_metrics else "system"
                    )
                    self.db.add(evaluation)
                    self.db.commit()
                    self.db.refresh(evaluation)
                    
                    evaluation_results.append(evaluation)
                    
                except Exception as e:
                    logger.error(f"평가 실패: result_id={result.id}, metric={metric}, error={str(e)}")
        
        # 가중치 저장 (있는 경우)
        if weights:
            for metric, weight in weights.items():
                # 기존 가중치가 있는지 확인
                existing_weight = self.db.query(models.EvaluationWeight).filter(
                    models.EvaluationWeight.experiment_set_id == experiment_set_id,
                    models.EvaluationWeight.metric_name == metric
                ).first()
                
                if existing_weight:
                    # 업데이트
                    existing_weight.weight = weight
                else:
                    # 새로 생성
                    weight_record = models.EvaluationWeight(
                        experiment_set_id=experiment_set_id,
                        metric_name=metric,
                        weight=weight
                    )
                    self.db.add(weight_record)
                
            self.db.commit()
        
        return {
            "success": True,
            "evaluations_count": len(evaluation_results),
            "metrics": list(set(e.metric_name for e in evaluation_results))
        }
    
    def _evaluate_relevance(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """결과의 관련성을 평가합니다."""
        # 간단한 구현: 출력 길이 기반
        if not result.output:
            return 0.0, {"error": "Empty output"}
        
        # 단어 수 기반 간단한 평가
        word_count = len(result.output.split())
        score = min(1.0, word_count / 100)  # 100단어 이상이면 만점
        
        return score, {"word_count": word_count}
    
    def _evaluate_coherence(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """결과의 일관성을 평가합니다."""
        # 간단한 구현: 문장 수 기반
        if not result.output:
            return 0.0, {"error": "Empty output"}
        
        # 문장 수 기반 간단한 평가
        sentences = [s.strip() for s in result.output.split('.') if s.strip()]
        sentence_count = len(sentences)
        
        # 평균 문장 길이
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, sentence_count)
        
        # 일관성 점수 (평균 문장 길이가 5-20 단어일 때 최고점)
        coherence_score = 0.0
        if avg_sentence_length >= 5 and avg_sentence_length <= 20:
            coherence_score = 1.0
        elif avg_sentence_length < 5:
            coherence_score = avg_sentence_length / 5
        else:  # avg_sentence_length > 20
            coherence_score = max(0, 1 - (avg_sentence_length - 20) / 20)
        
        return coherence_score, {
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length
        }
    
    def _evaluate_factuality(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """결과의 사실성을 평가합니다."""
        # 사실성 평가는 참조 텍스트가 필요함
        if not reference_text:
            return 0.5, {"warning": "Reference text required for factuality evaluation"}
        
        # 실제 구현에서는 참조 텍스트와 출력을 비교하는 로직이 필요함
        # 여기서는 간단히 0.7을 반환
        return 0.7, {"note": "Simple placeholder score"}
    
    def _evaluate_response_time(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """응답 시간을 평가합니다."""
        if not result.execution_time:
            return 0.0, {"error": "No execution time data"}
        
        # 응답 시간이 5초 이내면 만점, 30초 이상이면 0점
        time_score = max(0, 1 - (result.execution_time - 5) / 25)
        
        return time_score, {"execution_time": result.execution_time}
    
    def _evaluate_token_usage(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """토큰 사용량을 평가합니다."""
        if not result.token_usage:
            return 0.0, {"error": "No token usage data"}
        
        # 총 토큰 수
        total_tokens = sum(result.token_usage.values())
        
        # 토큰 수가 적을수록 높은 점수 (1000 토큰 이하면 만점, 5000 토큰 이상이면 0점)
        token_score = max(0, 1 - (total_tokens - 1000) / 4000)
        
        return token_score, {
            "total_tokens": total_tokens,
            "token_details": result.token_usage
        }
    
    def _evaluate_token_efficiency(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """토큰 효율성을 평가합니다."""
        if not result.token_usage or "completion" not in result.token_usage:
            return 0.0, {"error": "No token usage data for completion"}
        
        if not result.output:
            return 0.0, {"error": "Empty output"}
        
        # 출력 문자 수당 토큰 비율
        chars = len(result.output)
        tokens = result.token_usage.get("completion", 0)
        
        if tokens == 0:
            return 0.0, {"error": "Zero completion tokens"}
        
        chars_per_token = chars / tokens
        
        # 문자/토큰 비율이 4 이상이면 만점, 1 이하면 0점
        efficiency_score = min(1.0, max(0, (chars_per_token - 1) / 3))
        
        return efficiency_score, {
            "chars": chars,
            "tokens": tokens,
            "chars_per_token": chars_per_token
        }
    
    def _evaluate_cost(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        reference_text: Optional[str] = None
    ) -> tuple[float, Dict[str, Any]]:
        """비용을 평가합니다."""
        # 비용이 계산되어 있지 않으면 계산
        if not result.cost and result.token_usage and experiment.model in ab_testing_settings.model_costs:
            cost_per_token = ab_testing_settings.model_costs[experiment.model]
            total_tokens = sum(result.token_usage.values())
            result.cost = total_tokens * cost_per_token
            self.db.commit()
        
        if not result.cost:
            return 0.0, {"error": "No cost data"}
        
        # 비용이 낮을수록 높은 점수 (0.01 달러 이하면 만점, 0.1 달러 이상이면 0점)
        cost_score = max(0, 1 - (result.cost - 0.01) / 0.09)
        
        return cost_score, {"cost": result.cost}
    
    async def _evaluate_with_llm(
        self, result: models.ExperimentResult, experiment: models.Experiment,
        metric: str, reference_text: Optional[str] = None,
        llm_evaluator: str = None, llm_evaluator_params: Dict[str, Any] = None
    ) -> tuple[float, Dict[str, Any]]:
        """LLM을 사용하여 평가합니다."""
        llm_evaluator = llm_evaluator or ab_testing_settings.default_evaluator_model
        llm_evaluator_params = llm_evaluator_params or {}
        
        # 평가 프롬프트 생성
        prompt = f"""
        당신은 텍스트 품질을 평가하는 전문가입니다. 아래의 텍스트를 '{metric}' 측면에서 0.0부터 1.0 사이의 점수로 평가해주세요.
        
        평가 기준: {metric}
        
        프롬프트: {experiment.prompt}
        
        응답: {result.output}
        """
        
        if reference_text:
            prompt += f"\n\n참조 텍스트: {reference_text}"
        
        prompt += "\n\n점수(0.0-1.0)와 평가 이유를 JSON 형식으로 제공해주세요. 예: {\"score\": 0.8, \"reasoning\": \"이유...\"}"
        
        # LLM 호출
        llm_response = self.llm_service.call_model(
            model=llm_evaluator,
            prompt=prompt,
            params=llm_evaluator_params
        )
        
        # 응답 파싱
        response_text = llm_response.get("output", "")
        
        try:
            # JSON 추출 시도
            json_str = response_text
            if "{" in response_text and "}" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
            
            evaluation_data = json.loads(json_str)
            score = float(evaluation_data.get("score", 0.5))
            
            # 점수 범위 보정
            score = max(0.0, min(1.0, score))
            
            details = {
                "reasoning": evaluation_data.get("reasoning", ""),
                "llm_response": response_text
            }
            
            return score, details
            
        except Exception as e:
            logger.error(f"LLM 평가 응답 파싱 오류: {str(e)}, response={response_text}")
            
            # 파싱 실패시 기본값 반환
            return 0.5, {"error": f"Failed to parse LLM response: {str(e)}", "raw_response": response_text}
