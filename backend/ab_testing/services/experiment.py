"""
A/B 테스트 실험 러너 서비스

실험을 실제로 실행하고 결과를 저장하는 서비스 클래스를 정의합니다.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from backend.logger import get_logger
from backend.ab_testing import models
from backend.ab_testing.config import ab_testing_settings
from backend.services.llm_service import LLMService

# 로거 설정
logger = get_logger(__name__)


class ExperimentRunner:
    """실험 실행 서비스 클래스"""
    
    def __init__(self, db: Session):
        """초기화"""
        self.db = db
        self.llm_service = LLMService()
    
    async def run_experiment_set(
        self, experiment_set_id: int, config: Dict[str, Any] = None
    ) -> List[models.ExperimentResult]:
        """실험 세트의 모든 실험을 실행합니다."""
        config = config or {}
        run_id = config.get("run_id", datetime.utcnow().strftime("%Y%m%d%H%M%S"))
        parallel = config.get("parallel", True)
        max_workers = config.get("max_workers", 5)
        timeout = config.get("timeout", 300)
        
        # 실험 세트 조회
        db_experiment_set = self.db.query(models.ExperimentSet).filter(
            models.ExperimentSet.id == experiment_set_id
        ).first()
        
        if not db_experiment_set:
            logger.error(f"실험 세트를 찾을 수 없음: id={experiment_set_id}")
            return []
        
        # 실험 목록 조회
        experiments = self.db.query(models.Experiment).filter(
            models.Experiment.experiment_set_id == experiment_set_id
        ).all()
        
        if not experiments:
            logger.warning(f"실험이 없음: experiment_set_id={experiment_set_id}")
            return []
        
        # 실행 방식 결정
        results = []
        if parallel:
            # 병렬 실행
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_experiment = {
                    executor.submit(self._run_experiment, experiment, run_id, timeout): experiment
                    for experiment in experiments
                }
                
                for future in as_completed(future_to_experiment):
                    experiment = future_to_experiment[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"실험 실행 오류: id={experiment.id}, error={str(e)}")
                        # 오류 결과 생성
                        error_result = models.ExperimentResult(
                            experiment_id=experiment.id,
                            status="failed",
                            error=str(e),
                            run_id=run_id
                        )
                        self.db.add(error_result)
                        self.db.commit()
                        results.append(error_result)
        else:
            # 순차 실행
            for experiment in experiments:
                try:
                    result = self._run_experiment(experiment, run_id, timeout)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"실험 실행 오류: id={experiment.id}, error={str(e)}")
                    # 오류 결과 생성
                    error_result = models.ExperimentResult(
                        experiment_id=experiment.id,
                        status="failed",
                        error=str(e),
                        run_id=run_id
                    )
                    self.db.add(error_result)
                    self.db.commit()
                    results.append(error_result)
        
        return results
    
    def _run_experiment(
        self, experiment: models.Experiment, run_id: str, timeout: int
    ) -> Optional[models.ExperimentResult]:
        """단일 실험을 실행합니다."""
        # 이미 실행 중이거나 완료된 결과가 있는지 확인
        existing_result = self.db.query(models.ExperimentResult).filter(
            models.ExperimentResult.experiment_id == experiment.id,
            models.ExperimentResult.run_id == run_id
        ).first()
        
        if existing_result and existing_result.status in ["completed", "running"]:
            logger.info(f"이미 실행 중이거나 완료된 실험: id={experiment.id}, run_id={run_id}")
            return existing_result
        
        # 실행 중 상태로 결과 생성
        result = models.ExperimentResult(
            experiment_id=experiment.id,
            status="running",
            run_id=run_id
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        try:
            # 시작 시간 기록
            start_time = time.time()
            
            # LLM 호출
            llm_response = self.llm_service.call_model(
                model=experiment.model,
                prompt=experiment.prompt,
                params=experiment.params,
                timeout=timeout
            )
            
            # 실행 시간 계산
            execution_time = time.time() - start_time
            
            # 결과 업데이트
            result.output = llm_response.get("output", "")
            result.raw_response = llm_response
            result.execution_time = execution_time
            result.token_usage = llm_response.get("token_usage", {})
            result.status = "completed"
            
            # 토큰 기반 비용 추정
            if "token_usage" in llm_response and experiment.model in ab_testing_settings.model_costs:
                cost_per_token = ab_testing_settings.model_costs[experiment.model]
                total_tokens = sum(llm_response["token_usage"].values())
                result.cost = total_tokens * cost_per_token
            
            # 변경사항 저장
            self.db.commit()
            self.db.refresh(result)
            
            logger.info(f"실험 실행 완료: id={experiment.id}, run_id={run_id}, execution_time={execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            # 오류 정보 업데이트
            result.status = "failed"
            result.error = str(e)
            self.db.commit()
            
            logger.error(f"실험 실행 실패: id={experiment.id}, run_id={run_id}, error={str(e)}")
            
            # 오류 전파
            raise
