from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
import enum

from .connection import Base
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from .connection import Base


class LLMTypeEnum(enum.Enum):
    openai_api = "openai_api"
    openai_web = "openai_web"
    claude_api = "claude_api"
    claude_web = "claude_web"
    manual = "manual"

class CodeLanguageEnum(enum.Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    csharp = "csharp"
    cpp = "cpp"
    go = "go"
    rust = "rust"
    php = "php"
    ruby = "ruby"
    swift = "swift"
    kotlin = "kotlin"
    other = "other"

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    responses = relationship("Response", back_populates="question")
    code_snippets = relationship("CodeSnippet", back_populates="question")

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    llm_type = Column(Enum(LLMTypeEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    question = relationship("Question", back_populates="responses")
    code_snippets = relationship("CodeSnippet", back_populates="response")

class CodeSnippet(Base):
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    language = Column(Enum(CodeLanguageEnum), nullable=False)
    tags = Column(JSON, default=list)
    source_llm = Column(Enum(LLMTypeEnum), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    question = relationship("Question", back_populates="code_snippets")
    response = relationship("Response", back_populates="code_snippets")
    parent_id = Column(Integer, ForeignKey("code_snippets.id"), nullable=True)
    children = relationship("CodeSnippet")

class CodeTemplate(Base):
    __tablename__ = "code_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    language = Column(Enum(CodeLanguageEnum), nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    openai_api_key = Column(String(255), nullable=True)
    claude_api_key = Column(String(255), nullable=True)
    github_token = Column(String(255), nullable=True)
    github_repo = Column(String(255), nullable=True)
    github_username = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IndexingStatus(str, Enum):
    """인덱싱 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class IndexingFrequency(str, Enum):
    """인덱싱 주기"""
    MANUAL = "manual"
    ON_COMMIT = "on_commit"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

class CodebaseIndexingSettings(BaseModel):
    """코드베이스 인덱싱 설정 모델"""
    id: Optional[int] = None
    codebase_id: int
    is_enabled: bool = True
    frequency: IndexingFrequency = IndexingFrequency.ON_COMMIT
    excluded_patterns: List[str] = Field(default_factory=list)  # e.g. ["*.log", "node_modules/*"]
    priority_patterns: List[str] = Field(default_factory=list)  # e.g. ["src/main/*", "*.py"]
    embedding_model: str = "openai/text-embedding-ada-002"  # 기본 임베딩 모델
    chunk_size: int = 1000  # 코드 청크 크기 (문자 수)
    chunk_overlap: int = 200  # 청크 간 겹침 정도
    include_comments: bool = True  # 주석 포함 여부
    max_files_per_run: int = 100  # 한 번의 인덱싱 실행당 최대 파일 수
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class CodebaseIndexingRun(BaseModel):
    """코드베이스 인덱싱 실행 기록 모델"""
    id: Optional[int] = None
    codebase_id: int
    status: IndexingStatus = IndexingStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    files_processed: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    error_message: Optional[str] = None
    is_full_index: bool = False  # 전체 인덱싱 vs 증분 인덱싱
    triggered_by: str = "manual"  # manual, scheduler, webhook 등
    
    class Config:
        orm_mode = True

class CodeEmbedding(BaseModel):
    """코드 임베딩 모델"""
    id: Optional[int] = None
    codebase_id: int
    file_id: int
    chunk_id: str  # 파일 내 청크 식별자 (e.g. "file.py:1-50")
    content: str  # 원본 코드 청크
    embedding: List[float] = Field(default_factory=list)  # 벡터 임베딩
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 추가 메타데이터
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class EmbeddingSearchResult(BaseModel):
    """임베딩 검색 결과 모델"""
    file_id: int
    file_path: str
    chunk_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class CodeSearchQuery(BaseModel):
    """코드 검색 쿼리 모델"""
    codebase_id: int
    query: str
    limit: int = 10
    threshold: Optional[float] = 0.5  # 유사도 임계값
    file_patterns: Optional[List[str]] = None  # 검색할 파일 패턴
    exclude_patterns: Optional[List[str]] = None  # 제외할 파일 패턴

class IndexingSettingsUpdate(BaseModel):
    """인덱싱 설정 업데이트 모델"""
    is_enabled: Optional[bool] = None
    frequency: Optional[IndexingFrequency] = None
    excluded_patterns: Optional[List[str]] = None
    priority_patterns: Optional[List[str]] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    include_comments: Optional[bool] = None
    max_files_per_run: Optional[int] = None

class TriggerIndexingRequest(BaseModel):
    """인덱싱 트리거 요청 모델"""
    codebase_id: int
    is_full_index: bool = False
    priority_files: Optional[List[int]] = None  # 우선적으로 인덱싱할 파일 ID 목록

class IndexingRunResponse(BaseModel):
    """인덱싱 실행 응답 모델"""
    run_id: int
    status: IndexingStatus
    message: str
    start_time: Optional[datetime] = None


class IndexingStatusEnum(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class IndexingFrequencyEnum(enum.Enum):
    manual = "manual"
    on_commit = "on_commit"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"

class CodebaseIndexingSettings(Base):
    __tablename__ = "codebase_indexing_settings"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    frequency = Column(Enum(IndexingFrequencyEnum), default=IndexingFrequencyEnum.on_commit)
    excluded_patterns = Column(JSON, default=list)
    priority_patterns = Column(JSON, default=list)
    embedding_model = Column(String(255), default="openai/text-embedding-ada-002")
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    include_comments = Column(Boolean, default=True)
    max_files_per_run = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    codebase = relationship("Codebase", back_populates="indexing_settings")
    indexing_runs = relationship("CodebaseIndexingRun", back_populates="settings")

class CodebaseIndexingRun(Base):
    __tablename__ = "codebase_indexing_runs"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"), nullable=False)
    settings_id = Column(Integer, ForeignKey("codebase_indexing_settings.id"), nullable=True)
    status = Column(Enum(IndexingStatusEnum), default=IndexingStatusEnum.pending)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    files_processed = Column(Integer, default=0)
    files_indexed = Column(Integer, default=0)
    files_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    is_full_index = Column(Boolean, default=False)
    triggered_by = Column(String(50), default="manual")

    # 관계 정의
    codebase = relationship("Codebase", back_populates="indexing_runs")
    settings = relationship("CodebaseIndexingSettings", back_populates="indexing_runs")
    embeddings = relationship("CodeEmbedding", back_populates="indexing_run")

class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("codebase_files.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("codebase_indexing_runs.id"), nullable=True)
    chunk_id = Column(String(255), nullable=False)  # 파일 내 청크 식별자
    content = Column(Text, nullable=False)  # 원본 코드 청크
    # 벡터 데이터베이스 사용 시 실제 임베딩은 벡터 DB에 저장될 수 있음
    # 이 경우 embedding_id나 embedding_key만 저장
    embedding_key = Column(String(255), nullable=True)  # 외부 벡터 DB에서의 키
    embedding = Column(ARRAY(Float), nullable=True)  # 내부 저장 시 임베딩 벡터
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    codebase = relationship("Codebase", back_populates="embeddings")
    file = relationship("CodebaseFile", back_populates="embeddings")
    indexing_run = relationship("CodebaseIndexingRun", back_populates="embeddings")

# Codebase 모델에 관계 추가
def update_codebase_model():
    from . import models
    
    # 역참조 관계 추가
    models.Codebase.indexing_settings = relationship("CodebaseIndexingSettings", back_populates="codebase", uselist=False)
    models.Codebase.indexing_runs = relationship("CodebaseIndexingRun", back_populates="codebase")
    models.Codebase.embeddings = relationship("CodeEmbedding", back_populates="codebase")
    
    # CodebaseFile에 역참조 추가
    models.CodebaseFile.embeddings = relationship("CodeEmbedding", back_populates="file")

# 데이터베이스 초기화 시 모델 관계 업데이트
update_codebase_model()