from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from datetime import datetime

class LLMType(str, Enum):
    """LLM 유형 정의"""
    OPENAI_API = "openai_api"
    OPENAI_WEB = "openai_web"
    CLAUDE_API = "claude_api"
    CLAUDE_WEB = "claude_web"
    MANUAL = "manual"  # 수동으로 입력한 경우

class Question(BaseModel):
    """사용자 질문 모델"""
    id: Optional[int] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class Response(BaseModel):
    """LLM 응답 모델"""
    id: Optional[int] = None
    question_id: int
    llm_type: LLMType
    content: str
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class CodeLanguage(str, Enum):
    """코드 언어 유형"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    OTHER = "other"

class CodeSnippet(BaseModel):
    """코드 스니펫 모델"""
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)
    source_llm: Optional[LLMType] = None
    question_id: Optional[int] = None  # 관련 질문 ID (있는 경우)
    response_id: Optional[int] = None  # 관련 응답 ID (있는 경우)
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class CodeTemplate(BaseModel):
    """코드 템플릿 모델"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class Settings(BaseModel):
    """시스템 설정 모델"""
    id: Optional[int] = None
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    github_username: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True