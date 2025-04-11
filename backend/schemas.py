from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime


# 사용자 관련 스키마
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# 질문 관련 스키마
class QuestionBase(BaseModel):
    content: str
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class QuestionCreate(QuestionBase):
    pass


class Question(QuestionBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 응답 관련 스키마
class ResponseBase(BaseModel):
    content: str
    question_id: int
    llm_type: str  # 'openai', 'claude', 'local', 등
    metadata: Optional[dict] = {}


class ResponseCreate(ResponseBase):
    pass


class Response(ResponseBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# GitHub 저장소 관련 스키마
class GitHubRepositoryBase(BaseModel):
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    is_private: bool = False


class GitHubRepositoryCreate(GitHubRepositoryBase):
    pass


# 수정된 부분: User 객체 대신 owner_id와 owner_name을 별도로 사용
class GitHubRepositoryResponse(GitHubRepositoryBase):
    id: int
    owner_id: int  # User.id
    owner_name: str  # User.username
    
    class Config:
        from_attributes = True


# 코드 스니펫 관련 스키마
class CodeSnippetBase(BaseModel):
    content: str
    language: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    question_id: Optional[int] = None
    response_id: Optional[int] = None


class CodeSnippetCreate(CodeSnippetBase):
    pass


class CodeSnippet(CodeSnippetBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 코드 템플릿 관련 스키마
class CodeTemplateBase(BaseModel):
    title: str
    content: str
    language: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class CodeTemplateCreate(CodeTemplateBase):
    pass


class CodeTemplate(CodeTemplateBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 설정 관련 스키마
class Settings(BaseModel):
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    github_access_token: Optional[str] = None
    default_llm: Optional[str] = "openai"
    theme: Optional[str] = "light"
    code_font_size: Optional[int] = 14
    enable_code_highlighting: Optional[bool] = True
    auto_save: Optional[bool] = True
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# 내보내기 관련 스키마
class ExportOptions(BaseModel):
    format: str  # "html", "markdown", "pdf", "json"
    include_metadata: Optional[bool] = False
    include_tags: Optional[bool] = True
    include_timestamps: Optional[bool] = True
    include_llm_info: Optional[bool] = True
    code_highlighting: Optional[bool] = True


# 프롬프트 템플릿 관련 스키마
class PromptTemplateBase(BaseModel):
    name: str
    content: str
    system_prompt: Optional[str] = None  # 시스템 프롬프트 필드 추가
    description: Optional[str] = None
    category: Optional[str] = "일반"
    tags: Optional[List[str]] = []
    template_variables: Optional[List[str]] = []


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    system_prompt: Optional[str] = None  # 시스템 프롬프트 필드 추가
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    template_variables: Optional[List[str]] = None


class PromptTemplate(PromptTemplateBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 에이전트 관련 스키마
class AgentSessionBase(BaseModel):
    name: str
    description: Optional[str] = None


class AgentSessionCreate(AgentSessionBase):
    pass


class AgentSession(AgentSessionBase):
    id: str  # UUID
    user_id: int
    created_at: datetime
    last_active: datetime
    status: str  # "active", "completed", "failed"

    class Config:
        from_attributes = True


class AgentLogEntry(BaseModel):
    session_id: str
    timestamp: datetime
    level: str  # "info", "warning", "error", "debug"
    message: str
    metadata: Optional[dict] = {}

    class Config:
        from_attributes = True
