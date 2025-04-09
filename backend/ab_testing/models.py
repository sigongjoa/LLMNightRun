"""
A/B 테스트 데이터 모델

A/B 테스트 관련 데이터베이스 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database.connection import Base


class ExperimentSet(Base):
    """
    실험 세트 모델
    
    여러 실험을 그룹화하는 컨테이너입니다.
    """
    __tablename__ = "ab_experiment_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON, nullable=True)  # 전체 실험 설정을 JSON으로 저장
    is_active = Column(Boolean, default=True)
    created_by = Column(String(255), nullable=True)  # 사용자 ID나 이름
    
    # 관계 정의
    experiments = relationship("Experiment", back_populates="experiment_set", cascade="all, delete-orphan")


class Experiment(Base):
    """
    실험 모델
    
    단일 실험 설정(프롬프트, 모델, 파라미터)을 정의합니다.
    """
    __tablename__ = "ab_experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    name = Column(String(255), index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    model = Column(String(255), nullable=False)
    params = Column(JSON, nullable=True)  # temperature, max_tokens 등
    weight = Column(Float, default=1.0)  # 가중치 (결과 평가시 사용)
    is_control = Column(Boolean, default=False)  # 대조군 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    experiment_set = relationship("ExperimentSet", back_populates="experiments")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentResult(Base):
    """
    실험 결과 모델
    
    실험 실행 결과와 메타데이터를 저장합니다.
    """
    __tablename__ = "ab_experiment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False)
    output = Column(Text, nullable=True)  # 모델 출력 텍스트
    execution_time = Column(Float, nullable=True)  # 실행 시간 (초)
    token_usage = Column(JSON, nullable=True)  # 토큰 사용량 (입력/출력)
    raw_response = Column(JSON, nullable=True)  # LLM의 원본 응답
    status = Column(String(50), default="completed")  # 'completed', 'failed', 'running'
    error = Column(Text, nullable=True)  # 오류 메시지
    created_at = Column(DateTime, default=datetime.utcnow)
    run_id = Column(String(255), nullable=True)  # 배치 실행 ID
    
    # 관계 정의
    experiment = relationship("Experiment", back_populates="results")
    evaluations = relationship("Evaluation", back_populates="result", cascade="all, delete-orphan")


class Evaluation(Base):
    """
    평가 모델
    
    실험 결과에 대한 다양한 평가 지표 결과를 저장합니다.
    """
    __tablename__ = "ab_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
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
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_set_id = Column(Integer, ForeignKey("ab_experiment_sets.id"), nullable=False)
    metric_name = Column(String(255), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 고유 제약 조건: (experiment_set_id, metric_name) 조합이 유니크해야 함
    __table_args__ = (
        # 고유 제약 조건을 위한 SQLAlchemy 문법
        # UniqueConstraint('experiment_set_id', 'metric_name', name='uix_eval_weight_set_metric'),
    )
