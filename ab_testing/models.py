"""
A/B 테스트 데이터 모델

A/B 테스트 관련 데이터베이스 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime


class Base:
    """ORM 기본 클래스"""
    id = Column(Integer, primary_key=True, index=True)


class ExperimentSet(Base):
    """
    실험 세트 모델
    
    여러 실험을 그룹화하는 컨테이너입니다.
    """
    __tablename__ = "ab_experiment_sets"
    
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON, nullable=True)  # 전체 실험 설정을 JSON으로 저장
    is_active = Column(Boolean, default=True)
    created_by = Column(String(255), nullable=True)  # 사용자 ID나 이름
    
    # 추가 필드
    tags = Column(JSON, nullable=True)  # 태그 목록
    schedule_config = Column(JSON, nullable=True)  # 스케줄 설정
    resource_config = Column(JSON, nullable=True)  # 자원 최적화 설정
    
    # 관계 정의
    experiments = relationship("Experiment", back_populates="experiment_set", cascade="all, delete-orphan")
    evaluation_weights = relationship("EvaluationWeight", back_populates="experiment_set", cascade="all, delete-orphan")
    batch_jobs = relationship("BatchJob", back_populates="experiment_set", cascade="all, delete-orphan")


class Experiment(Base):
    """
    실험 모델
    
    단일 실험 설정(프롬프트, 모델, 파라미터)을 정의합니다.
    """
    __tablename__ = "ab_experiments"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    name = Column(String(255), index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    model = Column(String(255), nullable=False)
    params = Column(JSON, nullable=True)  # temperature, max_tokens 등
    weight = Column(Float, default=1.0)  # 가중치 (결과 평가시 사용)
    is_control = Column(Boolean, default=False)  # 대조군 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 추가 필드
    notes = Column(Text, nullable=True)  # 실험에 대한 메모
    tags = Column(JSON, nullable=True)  # 태그 목록
    template_id = Column(Integer, ForeignKey("ab_experiment_templates.id"), nullable=True)  # 템플릿 ID
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet", back_populates="experiments")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")
    template = relationship("ExperimentTemplate", back_populates="experiments")


class ExperimentResult(Base):
    """
    실험 결과 모델
    
    실험 실행 결과와 메타데이터를 저장합니다.
    """
    __tablename__ = "ab_experiment_results"
    
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False)
    output = Column(Text, nullable=True)  # 모델 출력 텍스트
    execution_time = Column(Float, nullable=True)  # 실행 시간 (초)
    token_usage = Column(JSON, nullable=True)  # 토큰 사용량 (입력/출력)
    raw_response = Column(JSON, nullable=True)  # LLM의 원본 응답
    status = Column(String(50), default="completed")  # 'completed', 'failed', 'running'
    error = Column(Text, nullable=True)  # 오류 메시지
    created_at = Column(DateTime, default=datetime.utcnow)
    run_id = Column(String(255), nullable=True)  # 배치 실행 ID
    
    # 추가 필드
    cost = Column(Float, nullable=True)  # 실행 비용 추정치
    batch_job_id = Column(Integer, ForeignKey("ab_batch_jobs.id"), nullable=True)  # 배치 작업 ID
    
    # 관계 정의
    experiment = relationship("Experiment", back_populates="results")
    evaluations = relationship("Evaluation", back_populates="result", cascade="all, delete-orphan")
    batch_job = relationship("BatchJob", back_populates="results")


class Evaluation(Base):
    """
    평가 모델
    
    실험 결과에 대한 다양한 평가 지표 결과를 저장합니다.
    """
    __tablename__ = "ab_evaluations"
    
    result_id = Column(Integer, ForeignKey("ab_experiment_results.id"), nullable=False)
    metric_name = Column(String(255), index=True, nullable=False)  # BLEU, ROUGE, GPTScore 등
    score = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)  # 세부 평가 데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    evaluator = Column(String(255), nullable=True)  # 평가에 사용된 모델이나 방법
    
    # 관계 정의
    result = relationship("ExperimentResult", back_populates="evaluations")


class EvaluationWeight(Base):
    """
    평가 가중치 모델
    
    여러 평가 지표에 대한 가중치를 정의합니다.
    """
    __tablename__ = "ab_evaluation_weights"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet", back_populates="evaluation_weights")


class ExperimentTemplate(Base):
    """
    실험 템플릿 모델
    
    재사용 가능한 실험 템플릿을 정의합니다.
    """
    __tablename__ = "ab_experiment_templates"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=False)
    model_suggestions = Column(JSON, nullable=True)  # 추천 모델 목록
    default_params = Column(JSON, nullable=True)  # 기본 파라미터
    tags = Column(JSON, nullable=True)  # 태그 목록
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)  # 작성자
    
    # 관계 정의
    experiments = relationship("Experiment", back_populates="template")


class BatchJob(Base):
    """
    배치 작업 모델
    
    대규모 실험 실행을 추적하기 위한 배치 작업 정보를 저장합니다.
    """
    __tablename__ = "ab_batch_jobs"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), default="pending")  # 'pending', 'running', 'completed', 'failed', 'canceled'
    config = Column(JSON, nullable=True)  # 작업 설정
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    items_total = Column(Integer, default=0)
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet", back_populates="batch_jobs")
    results = relationship("ExperimentResult", back_populates="batch_job")


class Report(Base):
    """
    보고서 모델
    
    생성된 보고서 정보를 저장합니다.
    """
    __tablename__ = "ab_reports"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    report_id = Column(String(255), nullable=False, unique=True, index=True)
    report_type = Column(String(50), nullable=False)  # 'html', 'pdf', 'json' 등
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_bytes = Column(Integer, nullable=True)
    report_metadata = Column(JSON, nullable=True)  # 보고서 메타데이터
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet")


class Export(Base):
    """
    내보내기 모델
    
    생성된 내보내기 파일 정보를 저장합니다.
    """
    __tablename__ = "ab_exports"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    export_id = Column(String(255), nullable=False, unique=True, index=True)
    format = Column(String(50), nullable=False)  # 'json', 'csv', 'excel' 등
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_bytes = Column(Integer, nullable=True)
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet")


class ConsistencyTest(Base):
    """
    일관성 테스트 모델
    
    모델 응답의 일관성 테스트 결과를 저장합니다.
    """
    __tablename__ = "ab_consistency_tests"
    
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False)
    test_id = Column(String(255), nullable=False, index=True)
    iterations = Column(Integer, default=0)
    variance_scores = Column(JSON, nullable=True)  # 다양한 지표별 분산
    consistency_rating = Column(Float, nullable=True)  # 일관성 점수 (0.0 ~ 1.0)
    outliers_count = Column(Integer, default=0)
    is_consistent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    experiment = relationship("Experiment")


class PromptOptimization(Base):
    """
    프롬프트 최적화 모델
    
    프롬프트 최적화 실험 및 결과를 저장합니다.
    """
    __tablename__ = "ab_prompt_optimizations"
    
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    optimization_id = Column(String(255), nullable=False, unique=True, index=True)
    target_metric = Column(String(255), nullable=False)
    original_prompt = Column(Text, nullable=False)
    optimized_prompt = Column(Text, nullable=True)
    improvement = Column(Float, nullable=True)  # 성능 향상도
    iterations = Column(Integer, default=0)
    history = Column(JSON, nullable=True)  # 최적화 과정
    status = Column(String(50), default="pending")  # 'pending', 'running', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet")


class MultiLanguageTestResult(Base):
    """
    다국어 테스트 결과 모델
    
    다국어 환경에서의 실험 결과를 저장합니다.
    """
    __tablename__ = "ab_multilanguage_tests"
    
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False)
    language = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    result = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    experiment = relationship("Experiment")
