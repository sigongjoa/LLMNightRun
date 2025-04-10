"""
GitHub 설정 관련 모델 정의 모듈

GitHub 저장소 및 연결 정보를 관리하는 모델을 정의합니다.
"""

from pydantic import Field, BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import IdentifiedModel, TimeStampedModel


class GitHubRepository(IdentifiedModel):
    """GitHub 저장소 정보 모델"""
    name: str
    description: Optional[str] = None
    owner: str
    token: str  # 실제로는 암호화하여 저장해야 함
    is_default: bool = False
    is_private: bool = True
    url: Optional[str] = None
    branch: str = "main"
    repo_info: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[int] = None  # 연결된 프로젝트 ID (있는 경우)


class GitHubRepositoryCreate(TimeStampedModel):
    """GitHub 저장소 생성 요청 모델"""
    name: str
    description: Optional[str] = None
    owner: str
    token: str
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    repo_info: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[int] = None


class GitHubRepositoryUpdate(TimeStampedModel):
    """GitHub 저장소 수정 요청 모델"""
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    token: Optional[str] = None
    is_default: Optional[bool] = None
    is_private: Optional[bool] = None
    branch: Optional[str] = None
    repo_info: Optional[Dict[str, Any]] = None
    project_id: Optional[int] = None


class GitHubRepositoryResponse(IdentifiedModel):
    """GitHub 저장소 응답 모델 (API 응답용) - 토큰은 제외"""
    name: str
    description: Optional[str] = None
    owner: str
    is_default: bool = False
    is_private: bool = True
    url: Optional[str] = None
    branch: str = "main"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[int] = None


class GitHubConfig(BaseModel):
    """GitHub 설정 모델"""
    enabled: bool = False
    repo_url: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    default_branch: str = "main"
    auto_commit: bool = False
    docs_directory: str = "docs"
    commit_message_template: str = "docs: Update {doc_type} documentation"


class GitHubConfigUpdateRequest(BaseModel):
    """GitHub 설정 업데이트 요청 모델"""
    enabled: Optional[bool] = None
    repo_url: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    default_branch: Optional[str] = None
    auto_commit: Optional[bool] = None
    docs_directory: Optional[str] = None
    commit_message_template: Optional[str] = None


class GitHubTestConnectionRequest(BaseModel):
    """GitHub 연결 테스트 요청 모델"""
    repo_url: str
    token: str
    username: str


class GitHubTestConnectionResponse(BaseModel):
    """GitHub 연결 테스트 응답 모델"""
    success: bool
    message: str
    error: Optional[str] = None
    repo_info: Optional[Dict[str, Any]] = None


class GitHubCommit(BaseModel):
    """GitHub 커밋 모델"""
    id: str
    message: str
    author: str
    date: datetime
    url: Optional[str] = None
    files: Optional[List[str]] = None
