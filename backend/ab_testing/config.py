"""
A/B 테스트 모듈 설정

A/B 테스트 관련 설정 및 상수를 정의합니다.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field

# 기본 평가 메트릭 가중치
DEFAULT_METRIC_WEIGHTS = {
    "bleu": 0.2,
    "rouge": 0.3,
    "gpt_score": 0.5,
}

# 지원하는 모델별 최대 토큰 길이
MODEL_MAX_TOKENS = {
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16384,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 180000,
    "claude-3-haiku": 150000,
    "mistral-small": 32000,
    "mistral-medium": 32000,
    "mistral-large": 32000,
    "local-model": 16384,  # 기본값
}

# 병렬 처리 설정
PARALLEL_PROCESSING = {
    "max_workers": 5,
    "default_timeout": 300,  # 5분
}

# GPT 기반 평가시 사용할 프롬프트 템플릿
GPT_EVALUATOR_PROMPT_TEMPLATE = """
당신은 텍스트 품질을 평가하는 전문가입니다. 
다음 기준에 따라 제시된 텍스트를 1~10점 척도로 평가해 주세요:

평가 기준: {criteria}

평가할 텍스트:
---
{text}
---

평가 결과는 JSON 형식으로 제공해주세요:
{{
  "score": (1-10 사이의 점수),
  "reasoning": "점수에 대한 상세한 근거"
}}
"""

# LLM 기반 비교 평가 프롬프트 템플릿
COMPARISON_PROMPT_TEMPLATE = """
다음 두 응답 A와 B를 비교하고, 어떤 응답이 더 우수한지 평가해 주세요.

질문 또는 프롬프트:
---
{prompt}
---

응답 A:
---
{response_a}
---

응답 B:
---
{response_b}
---

다음 기준으로 평가해 주세요:
{criteria}

두 응답의 우수성을 비교하여 다음 형식으로 JSON 응답을 제공해 주세요:
{{
  "winner": "A" 또는 "B" 또는 "tie",
  "reasoning": "선택한 이유에 대한 상세한 설명",
  "scores": {{
    "A": (1-10 사이의 점수),
    "B": (1-10 사이의 점수)
  }}
}}
"""


class ABTestingSettings(BaseModel):
    """A/B 테스트 설정 모델"""
    
    # 기본 평가 메트릭
    default_metrics: List[str] = Field(
        default=["bleu", "rouge", "gpt_score"]
    )
    
    # 기본 평가 메트릭 가중치
    default_weights: Dict[str, float] = Field(
        default=DEFAULT_METRIC_WEIGHTS
    )
    
    # 병렬 처리 설정
    parallel: Dict[str, Any] = Field(
        default=PARALLEL_PROCESSING
    )
    
    # 보고서 저장 경로
    reports_dir: str = Field(
        default="./exports/ab_testing/reports"
    )
    
    # 차트 저장 경로
    charts_dir: str = Field(
        default="./exports/ab_testing/charts"
    )
    
    # 결과 내보내기 저장 경로
    exports_dir: str = Field(
        default="./exports/ab_testing/exports"
    )
    
    # 평가 캐싱 사용 여부
    cache_evaluations: bool = Field(
        default=True
    )
    
    # LLM 평가자 기본 설정
    llm_evaluator: Dict[str, Any] = Field(
        default={
            "model": "gpt-4",
            "temperature": 0.2,
            "prompt_template": GPT_EVALUATOR_PROMPT_TEMPLATE,
            "comparison_template": COMPARISON_PROMPT_TEMPLATE,
        }
    )


# 설정 인스턴스 생성
ab_testing_settings = ABTestingSettings()
