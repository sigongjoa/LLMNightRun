"""
GitHub 설정 모델

이 모듈은 GitHub 연동 설정을 위한 데이터 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class GitHubConfig(BaseModel):
    """GitHub 설정 모델"""
    id: str = "github_config"
    enabled: bool = False
    repo_url: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    default_branch: str = "main"
    auto_commit: bool = False
    docs_directory: str = "docs"
    commit_message_template: str = "docs: Update {doc_type} documentation"
    updated_at: datetime = Field(default_factory=datetime.now)


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


class GitHubCommit(BaseModel):
    """GitHub 커밋 모델"""
    id: str
    commit_id: str
    message: str
    document_ids: List[str]
    timestamp: datetime
    url: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GitHubTestConnectionRequest(BaseModel):
    """GitHub 연결 테스트 요청 모델"""
    repo_url: str
    token: str
    username: str


class GitHubTestConnectionResponse(BaseModel):
    """GitHub 연결 테스트 응답 모델"""
    success: bool
    message: str
    repo_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
