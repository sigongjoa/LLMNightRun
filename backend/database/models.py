"""
데이터베이스 ORM 모델 정의

SQLAlchemy ORM 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .connection import Base
from backend.models.enums import LLMType, CodeLanguage, IndexingStatus, IndexingFrequency, AgentPhase


# 데이터베이스용 열거형
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

class AgentPhaseEnum(enum.Enum):
    think = "think"
    act = "act"
    observe = "observe"
    initialize = "initialize"
    finish = "finish"
    error = "error"


# 기본 모델
class Question(Base):
    """질문 테이블"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    responses = relationship("Response", back_populates="question")
    code_snippets = relationship("CodeSnippet", back_populates="question")


class Response(Base):
    """응답 테이블"""
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
    """코드 스니펫 테이블"""
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
    parent_id = Column(Integer, ForeignKey("code_snippets.id"), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    question = relationship("Question", back_populates="code_snippets")
    response = relationship("Response", back_populates="code_snippets")
    children = relationship("CodeSnippet", 
                           backref="parent", 
                           remote_side=[id])


class CodeTemplate(Base):
    """코드 템플릿 테이블"""
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
    """설정 테이블"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    openai_api_key = Column(String(255), nullable=True)
    claude_api_key = Column(String(255), nullable=True)
    github_token = Column(String(255), nullable=True)
    github_repo = Column(String(255), nullable=True)
    github_username = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Codebase(Base):
    """코드베이스 테이블"""
    __tablename__ = "codebases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(255), nullable=True)
    language = Column(String(50), nullable=True)
    path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    files = relationship("CodebaseFile", back_populates="codebase")
    indexing_settings = relationship("CodebaseIndexingSettings", back_populates="codebase", uselist=False)
    indexing_runs = relationship("CodebaseIndexingRun", back_populates="codebase")
    embeddings = relationship("CodeEmbedding", back_populates="codebase")


class CodebaseFile(Base):
    """코드베이스 파일 테이블"""
    __tablename__ = "codebase_files"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"), nullable=False)
    path = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    is_directory = Column(Boolean, default=False)
    size = Column(Integer, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    codebase = relationship("Codebase", back_populates="files")
    embeddings = relationship("CodeEmbedding", back_populates="file")


class CodebaseIndexingSettings(Base):
    """코드베이스 인덱싱 설정 테이블"""
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
    """코드베이스 인덱싱 실행 테이블"""
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
    """코드 임베딩 테이블"""
    __tablename__ = "code_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("codebase_files.id"), nullable=False)
    run_id = Column(Integer, ForeignKey("codebase_indexing_runs.id"), nullable=True)
    chunk_id = Column(String(255), nullable=False)  # 파일 내 청크 식별자
    content = Column(Text, nullable=False)  # 원본 코드 청크
    embedding_key = Column(String(255), nullable=True)  # 외부 벡터 DB에서의 키
    embedding = Column(JSON, nullable=True)  # 내부 저장 시 임베딩 벡터
    meta_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    codebase = relationship("Codebase", back_populates="embeddings")
    file = relationship("CodebaseFile", back_populates="embeddings")
    indexing_run = relationship("CodebaseIndexingRun", back_populates="embeddings")


class AgentSession(Base):
    """Agent 세션 테이블"""
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    agent_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    total_steps = Column(Integer, default=0)
    parameters = Column(JSON, default=dict)
    
    # 관계 정의
    logs = relationship("AgentLog", back_populates="session")


class AgentLog(Base):
    """Agent 로그 테이블"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("agent_sessions.session_id"), nullable=False)
    step = Column(Integer, nullable=False)
    phase = Column(Enum(AgentPhaseEnum), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # 관계 정의
    session = relationship("AgentSession", back_populates="logs")