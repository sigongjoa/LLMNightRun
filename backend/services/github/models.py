"""
GitHub 서비스 모듈에서 사용하는 모델 정의
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class GitHubRepositoryData:
    """GitHub 저장소 데이터 클래스"""
    name: str
    owner: str  # 호환성을 위해 owner 유지, 내부적으로 기본 테이블에서 github_owner로 사용
    token: str
    description: Optional[str] = None
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    project_id: Optional[int] = None
    repo_info: Dict[str, Any] = field(default_factory=dict)
    user_id: int = 1  # 기본 사용자 ID


@dataclass
class GitHubFileData:
    """GitHub 파일 데이터 클래스"""
    path: str
    content: str
    commit_message: Optional[str] = None


@dataclass
class GitHubCommitData:
    """GitHub 커밋 데이터 클래스"""
    message: str
    files: List[GitHubFileData]
    author: Optional[str] = None
    email: Optional[str] = None
    branch: Optional[str] = None
