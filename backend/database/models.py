"""
데이터베이스 ORM 모델 정의

SQLAlchemy ORM 모델을 정의합니다.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float, UniqueConstraint
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
    local_llm = "local_llm"
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


# 프로젝트 모델
class Project(Base):
    """프로젝트 테이블"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    project_data = Column(JSON, default=dict)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    owner = relationship("User", back_populates="projects")
    questions = relationship("Question", back_populates="project")
    code_snippets = relationship("CodeSnippet", back_populates="project")
    documents = relationship("Document", back_populates="project")
    github_repositories = relationship("GitHubRepository", back_populates="project")
    responses = relationship("Response", back_populates="project", foreign_keys="Response.project_id")
    code_templates = relationship("CodeTemplate", back_populates="project")
    codebases = relationship("Codebase", back_populates="project")
    agent_sessions = relationship("AgentSession", back_populates="project")
    collaborators = relationship("ProjectCollaborator", back_populates="project")
    

class ProjectCollaborator(Base):
    """프로젝트 협업자 테이블"""
    __tablename__ = "project_collaborators"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="editor")  # admin, editor, viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 유니크 제약 조건 (한 프로젝트에 각 사용자는 한 번만 협업자로 추가 가능)
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )
    
    # 관계 정의
    project = relationship("Project", back_populates="collaborators")
    user = relationship("User")


# GitHub 저장소 모델
class GitHubRepository(Base):
    """GitHub 저장소 테이블"""
    __tablename__ = "github_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    github_owner = Column(String(255), nullable=False, comment="GitHub 사용자명/조직명")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="시스템의 저장소 소유자")
    token = Column(String(255), nullable=False)  # 암호화 필요
    is_default = Column(Boolean, default=False)
    is_private = Column(Boolean, default=True)
    url = Column(String(255), nullable=False)
    branch = Column(String(50), default="main")
    webhook_id = Column(String(100), nullable=True)
    webhook_secret = Column(String(100), nullable=True)
    repo_info = Column(JSON, default=dict)
    sync_enabled = Column(Boolean, default=False)
    last_synced_at = Column(DateTime, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    owner = relationship("User", back_populates="github_repositories")
    project = relationship("Project", back_populates="github_repositories")
    commits = relationship("GitHubCommit", back_populates="repository")
    webhook_events = relationship("GitHubWebhookEvent", back_populates="repository")

class GitHubCommit(Base):
    """GitHub 커밋 히스토리 테이블"""
    __tablename__ = "github_commits"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("github_repositories.id"), nullable=False)
    commit_hash = Column(String(40), nullable=False)
    author = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    commit_date = Column(DateTime, nullable=False)
    files_changed = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    commit_data = Column(JSON, default=dict)
    related_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    repository = relationship("GitHubRepository", back_populates="commits")
    related_question = relationship("Question")
    
    # 유니크 제약 조건 (한 저장소에 같은 커밋은 한 번만 기록)
    __table_args__ = (
        UniqueConstraint('repository_id', 'commit_hash', name='uq_repo_commit'),
    )

class GitHubWebhookEvent(Base):
    """GitHub 웹훅 이벤트 테이블"""
    __tablename__ = "github_webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("github_repositories.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # push, pull_request, etc.
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    repository = relationship("GitHubRepository", back_populates="webhook_events")


# 문서 모델
class Document(Base):
    """문서 테이블"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    format = Column(String(50), default="markdown")  # markdown, html, pdf, etc.
    meta_data = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    project = relationship("Project", back_populates="documents")
    question = relationship("Question", back_populates="documents")
    response = relationship("Response", back_populates="documents")


# 기본 모델
class Question(Base):
    """질문 테이블"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    project = relationship("Project", back_populates="questions")
    responses = relationship("Response", back_populates="question")
    code_snippets = relationship("CodeSnippet", back_populates="question")
    documents = relationship("Document", back_populates="question")


class Response(Base):
    """응답 테이블"""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    llm_type = Column(Enum(LLMTypeEnum), nullable=False)
    content = Column(Text, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    project = relationship("Project", back_populates="responses", foreign_keys=[project_id])
    question = relationship("Question", back_populates="responses")
    code_snippets = relationship("CodeSnippet", back_populates="response")
    documents = relationship("Document", back_populates="response")


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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("code_snippets.id"), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    project = relationship("Project", back_populates="code_snippets")
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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    project = relationship("Project", back_populates="code_templates")


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    profile_image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 관계 정의
    projects = relationship("Project", back_populates="owner")
    github_repositories = relationship("GitHubRepository", back_populates="owner")
    user_settings = relationship("UserSettings", back_populates="user", uselist=False)
    api_keys = relationship("ApiKey", back_populates="user")
    oauth_accounts = relationship("OAuthAccount", back_populates="user")


class UserSettings(Base):
    """사용자 설정 테이블"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    openai_api_key = Column(String(255), nullable=True)
    claude_api_key = Column(String(255), nullable=True)
    github_token = Column(String(255), nullable=True)
    default_github_repo = Column(String(255), nullable=True)
    default_github_username = Column(String(255), nullable=True)
    theme = Column(String(20), default="light")
    language = Column(String(10), default="ko")
    notification_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    user = relationship("User", back_populates="user_settings")


class ApiKey(Base):
    """API 키 테이블"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(50), nullable=False)
    key_value = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # 관계 정의
    user = relationship("User", back_populates="api_keys")


class OAuthAccount(Base):
    """OAuth 계정 테이블"""
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(20), nullable=False)  # 'github', 'google', etc.
    provider_user_id = Column(String(100), nullable=False)
    access_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 유니크 제약 조건 (한 유저는 한 제공자당 하나의 계정만 연결 가능)
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_provider_id'),
    )
    
    # 관계 정의
    user = relationship("User", back_populates="oauth_accounts")


class Settings(Base):
    """글로벌 설정 테이블"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    default_openai_api_key = Column(String(255), nullable=True)
    default_claude_api_key = Column(String(255), nullable=True)
    default_github_token = Column(String(255), nullable=True)
    default_github_repo = Column(String(255), nullable=True)
    default_github_username = Column(String(255), nullable=True)
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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    project = relationship("Project", back_populates="codebases")
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
    meta_data = Column(JSON, default=dict)
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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # 관계 정의
    logs = relationship("AgentLog", back_populates="session")
    project = relationship("Project", back_populates="agent_sessions")


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


# 사용자 활동 및 작업 관련 모델
class UserActivity(Base):
    """사용자 활동 로그 테이블"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, create_project, generate_code, etc.
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 길이 고려
    user_agent = Column(String(255), nullable=True)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    user = relationship("User")


class BackgroundTask(Base):
    """백그라운드 작업 테이블"""
    __tablename__ = "background_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_type = Column(String(50), nullable=False)  # github_sync, code_indexing, etc.
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 관계 정의
    user = relationship("User")


class Notification(Base):
    """알림 테이블"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # system, github, task, etc.
    is_read = Column(Boolean, default=False)
    action_url = Column(String(255), nullable=True)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    user = relationship("User")


# GitHub 저장소 파일 및 관리 모델
class GitHubRepositoryFile(Base):
    """GitHub 저장소 파일 테이블"""
    __tablename__ = "github_repository_files"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("github_repositories.id"), nullable=False)
    path = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    size = Column(Integer, nullable=True)
    sha = Column(String(40), nullable=True)
    last_commit_hash = Column(String(40), nullable=True)
    last_updated = Column(DateTime, nullable=True)
    is_directory = Column(Boolean, default=False)
    content_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 정의
    repository = relationship("GitHubRepository")
    
    # 유니크 제약 조건 (저장소 내 동일 경로에 같은 이름의 파일은 존재할 수 없음)
    __table_args__ = (
        UniqueConstraint('repository_id', 'path', 'name', name='uq_repo_file_path'),
    )


from sqlalchemy import UniqueConstraint