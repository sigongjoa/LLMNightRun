"""
GitHub 서비스 관련 데이터 모델
"""

from typing import Optional
from pydantic import BaseModel


class GitHubRepositoryData(BaseModel):
    """GitHub 저장소 데이터 모델"""
    name: str
    description: Optional[str] = None
    owner: str
    token: str
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    project_id: Optional[int] = None


class GitHubFileData(BaseModel):
    """GitHub 파일 데이터 모델"""
    path: str
    content: str


class GitHubCommitData(BaseModel):
    """GitHub 커밋 데이터 모델"""
    message: str
    branch: Optional[str] = None
    files: list[GitHubFileData]
