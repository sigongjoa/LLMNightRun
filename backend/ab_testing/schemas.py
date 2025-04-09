"""
A/B 테스트 요청/응답 스키마

API 요청 및 응답에 대한 Pydantic 모델을 정의합니다.
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """지원되는 LLM 모델 타입"""
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE3_OPUS = "claude-3-opus"
    CLAUDE3_SONNET = "claude-3-sonnet"
    CLAUDE3_HAIKU = "claude-3-haiku"
    MISTRAL_SMALL = "mistral-small"
    MISTRAL_MEDIUM = "mistral-medium"
    MISTRAL_LARGE = "mistral-large"
    LOCAL_MODEL = "local-model"  # LM Studio 등 로컬 모델
    CUSTOM = "custom"  # 커스텀 모델


class ExperimentStatus(str, Enum):
    """실험 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class EvaluationMetric(str, Enum):
    """지원되는 평가 지표"""
    BLEU = "bleu"
    ROUGE = "rouge"
    METEOR = "meteor"
    GPT_SCORE = "gpt_score"
    G_EVAL = "g_eval"
    FACTUALITY = "factuality"
    COHERENCE = "coherence"
    RELEVANCE = "relevance"
    GROUNDEDNESS = "groundedness"
    CUSTOM = "custom"


# 요청 스키마
class ModelParamsBase(BaseModel):
    """LLM 모델 파라미터 기본 모델"""
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=0.0, le=2.0)
    presence_penalty: Optional[float] = Field(0.0, ge=0.0, le=2.0)


class ExperimentBase(BaseModel):
    """실험 기본 모델"""
    name: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1, max_length=255)
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    weight: Optional[float] = Field(1.0, ge=0.0)
    is_control: Optional[bool] = False


class ExperimentCreate(ExperimentBase):
    """실험 생성 모델"""
    pass


class ExperimentSetBase(BaseModel):
    """실험 세트 기본 모델"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExperimentSetCreate(ExperimentSetBase):
    """실험 세트 생성 모델"""
    experiments: List[ExperimentCreate] = Field(..., min_items=1)
    
    @validator('experiments')
    def at_least_one_experiment(cls, v):
        if not v:
            raise ValueError('실험 세트에는 최소 하나 이상의 실험이 필요합니다')
        return v


class EvaluationWeightCreate(BaseModel):
    """평가 가중치 생성 모델"""
    metric_name: str = Field(..., min_length=1, max_length=255)
    weight: float = Field(..., ge=0.0, le=1.0)


class EvaluationConfig(BaseModel):
    """평가 구성 모델"""
    metrics: List[str] = Field(default_factory=list)
    weights: Optional[Dict[str, float]] = Field(default_factory=dict)
    llm_evaluator: Optional[str] = None
    llm_evaluator_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reference_text: Optional[str] = None  # Ground truth가 있는 경우
    
    @validator('weights')
    def validate_weights_sum(cls, v, values):
        if v and 'metrics' in values and sum(v.values()) != 1.0:
            raise ValueError('가중치 합은 1.0이어야 합니다')
        return v


class RunExperimentSet(BaseModel):
    """실험 세트 실행 모델"""
    parallel: Optional[bool] = True
    max_workers: Optional[int] = Field(5, ge=1, le=20)
    timeout: Optional[int] = Field(300, ge=1)  # seconds
    evaluation_config: Optional[EvaluationConfig] = None


# 응답 스키마
class ExperimentDB(ExperimentBase):
    """실험 DB 모델"""
    id: int
    experiment_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ExperimentSetDB(ExperimentSetBase):
    """실험 세트 DB 모델"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str] = None
    experiments: List[ExperimentDB] = []

    class Config:
        orm_mode = True


class ExperimentResultBase(BaseModel):
    """실험 결과 기본 모델"""
    output: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    status: str = "completed"
    error: Optional[str] = None


class ExperimentResultDB(ExperimentResultBase):
    """실험 결과 DB 모델"""
    id: int
    experiment_id: int
    created_at: datetime
    run_id: Optional[str] = None

    class Config:
        orm_mode = True


class EvaluationBase(BaseModel):
    """평가 기본 모델"""
    metric_name: str
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    evaluator: Optional[str] = None


class EvaluationDB(EvaluationBase):
    """평가 DB 모델"""
    id: int
    result_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EvaluationWeightDB(BaseModel):
    """평가 가중치 DB 모델"""
    id: int
    experiment_set_id: int
    metric_name: str
    weight: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 응답 통합 모델
class ExperimentWithResults(ExperimentDB):
    """결과가 포함된 실험 모델"""
    results: List[ExperimentResultDB] = []


class ExperimentSetWithExperiments(ExperimentSetDB):
    """실험이 포함된 실험 세트 모델"""
    experiments: List[ExperimentWithResults] = []


class ExperimentResultWithEvaluations(ExperimentResultDB):
    """평가가 포함된 실험 결과 모델"""
    evaluations: List[EvaluationDB] = []


class ExperimentWithDetailedResults(ExperimentDB):
    """상세 결과가 포함된 실험 모델"""
    results: List[ExperimentResultWithEvaluations] = []


class ExperimentSetDetailResponse(ExperimentSetDB):
    """실험 세트 상세 응답 모델"""
    experiments: List[ExperimentWithDetailedResults] = []


# 상태 응답
class StatusResponse(BaseModel):
    """실험 세트 상태 응답 모델"""
    experiment_set_id: int
    name: str
    total_experiments: int
    completed: int
    running: int
    failed: int
    pending: int
    status: str  # overall status
    progress: float  # 0.0 - 1.0
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


# 실행 응답
class RunResponse(BaseModel):
    """실험 세트 실행 응답 모델"""
    experiment_set_id: int
    run_id: str
    status: str
    message: str
    started_at: datetime


# 결과 요약 응답
class ExperimentSummary(BaseModel):
    """실험 요약 모델"""
    id: int
    name: str
    model: str
    avg_execution_time: Optional[float] = None
    avg_scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: Optional[float] = None
    rank: Optional[int] = None


class ResultsResponse(BaseModel):
    """실험 세트 결과 응답 모델"""
    experiment_set_id: int
    name: str
    run_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    experiment_summaries: List[ExperimentSummary] = []
    best_experiment_id: Optional[int] = None
    evaluation_metrics: List[str] = []


# 보고서 응답
class ReportResponse(BaseModel):
    """실험 세트 보고서 응답 모델"""
    experiment_set_id: int
    name: str
    report_url: str
    report_type: str
    generated_at: datetime


# 내보내기 응답
class ExportResponse(BaseModel):
    """실험 세트 내보내기 응답 모델"""
    experiment_set_id: int
    file_url: str
    format: str
    size_bytes: int
    generated_at: datetime


# 삭제 응답
class DeleteResponse(BaseModel):
    """삭제 응답 모델"""
    success: bool
    message: str
