"""
문서 관리 모델

이 모듈은 프로젝트 문서 관리를 위한 데이터 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DocumentType(str, Enum):
    """문서 유형 열거형"""
    README = "README"
    API_DOC = "API_DOC"
    ARCHITECTURE = "ARCHITECTURE"
    DESIGN = "DESIGN"
    DATABASE = "DATABASE"
    SETUP = "SETUP"
    DEPLOYMENT = "DEPLOYMENT"
    CONFIGURATION = "CONFIGURATION"
    CHANGELOG = "CHANGELOG"


class DocumentStatus(str, Enum):
    """문서 상태 열거형"""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Document(BaseModel):
    """문서 모델"""
    id: Optional[str] = None
    type: DocumentType
    title: str
    content: str
    status: DocumentStatus = DocumentStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    github_path: Optional[str] = None
    last_commit_id: Optional[str] = None
    doc_info: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "doc_123",
                "type": "API_DOC",
                "title": "API 문서",
                "content": "# API 문서\n\n## 개요\n\n이 문서는 API를 설명합니다.",
                "status": "GENERATED",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "github_path": "docs/API.md",
                "last_commit_id": "abc123",
                "doc_info": {"version": "1.0.0"}
            }
        }


class DocumentCreateRequest(BaseModel):
    """문서 생성 요청 모델"""
    type: DocumentType
    title: str
    content: Optional[str] = None
    status: Optional[DocumentStatus] = DocumentStatus.DRAFT
    github_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentUpdateRequest(BaseModel):
    """문서 업데이트 요청 모델"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[DocumentStatus] = None
    github_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentGenerateRequest(BaseModel):
    """문서 자동 생성 요청 모델"""
    type: DocumentType
    force_regenerate: bool = False
    custom_params: Dict[str, Any] = Field(default_factory=dict)


class DocumentPublishRequest(BaseModel):
    """문서 GitHub 게시 요청 모델"""
    document_ids: List[str]
    commit_message: Optional[str] = None
    auto_message: bool = True
    branch_name: Optional[str] = None
    create_pr: bool = False
    pr_title: Optional[str] = None
    pr_description: Optional[str] = None


class DocumentResponse(BaseModel):
    """문서 응답 모델"""
    id: str
    type: DocumentType
    title: str
    content: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    github_path: Optional[str] = None
    last_commit_id: Optional[str] = None
    doc_info: Dict[str, Any] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    """문서 목록 응답 모델"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class GitHubSettingsModel(BaseModel):
    """GitHub 설정 모델"""
    enabled: bool = False
    repo_url: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    default_branch: str = "main"
    auto_commit: bool = False
    docs_directory: str = "docs"
    commit_message_template: str = "docs: Update {doc_type} documentation"


class GitHubCommitResponse(BaseModel):
    """GitHub 커밋 응답 모델"""
    success: bool
    commit_id: Optional[str] = None
    message: str
    documents: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    url: Optional[str] = None
    error: Optional[str] = None
