"""
GitHub 서비스 모듈

GitHub 리포지토리에 파일을 업로드하고 커밋 메시지를 자동 생성하는 기능을 제공합니다.
또한 저장소 목록 조회, 저장소 생성, 문서 생성 등의 GitHub 관련 기능을 제공합니다.
다중 저장소 지원 및 프로젝트별 저장소 관리 기능이 추가되었습니다.

이 모듈은 하위 모듈로 리팩토링되었습니다. 하위 모듈 접근은 GitHubServiceFactory를 통해 가능합니다.
"""

from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException
import aiohttp

from .github import GitHubServiceFactory
from .github.models import GitHubRepositoryData


class GitHubService:
    """
    GitHub 서비스 클래스
    
    이 클래스는 GitHubServiceFactory를 래핑하여 기존 코드와의 호환성을 유지합니다.
    새로운 코드에서는 GitHubServiceFactory를 직접 사용하는 것이 권장됩니다.
    """
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        self.factory = GitHubServiceFactory(db)
        self.settings = self.factory.repository_service.settings
        
    def _get_repository(self, repo_id: Optional[int] = None):
        """저장소 정보를 가져옵니다."""
        return self.factory.get_repository(repo_id)
    
    def create_repository(self, repo_data: GitHubRepositoryData):
        """새 저장소 정보를 데이터베이스에 추가합니다."""
        return self.factory.create_repository(repo_data)
    
    def update_repository(self, repo_id, repo_data):
        """저장소 정보를 업데이트합니다."""
        return self.factory.update_repository(repo_id, repo_data)
    
    def delete_repository(self, repo_id):
        """저장소 정보를 삭제합니다."""
        return self.factory.delete_repository(repo_id)
    
    def get_repositories(self, project_id=None):
        """저장소 목록을 조회합니다."""
        return self.factory.get_repositories(project_id)
    
    async def generate_commit_message(self, question_id, repo_id=None):
        """커밋 메시지를 생성합니다."""
        return await self.factory.generate_commit_message(question_id)
    
    async def generate_readme(self, question_id, repo_id=None):
        """README 파일을 생성합니다."""
        return await self.factory.generate_readme(question_id)
    
    async def upload_to_github(self, question_id, folder_path=None, repo_id=None):
        """코드 스니펫을 GitHub에 업로드합니다."""
        return await self.factory.upload_to_github(question_id, folder_path, repo_id)
    
    async def upload_file_to_github(self, content, file_path, commit_message=None, repo_id=None, branch=None):
        """파일을 GitHub에 업로드합니다."""
        return await self.factory.upload_file_to_github(content, file_path, commit_message, repo_id, branch)
    
    async def list_remote_repositories(self, repo_id=None):
        """원격 저장소 목록을 조회합니다."""
        return await self.factory.list_remote_repositories(repo_id)
    
    async def create_remote_repository(self, name, description="", private=True, auto_init=True, repo_id=None):
        """원격 저장소를 생성합니다."""
        return await self.factory.create_remote_repository(name, description, private, auto_init, repo_id)

    async def test_connection(self, repo_url: str, token: str, username: str):
        """
        GitHub 연결 테스트
        
        Args:
            repo_url: 저장소 URL
            token: GitHub 토큰
            username: GitHub 사용자 이름
            
        Returns:
            연결 테스트 결과
        """
        return await self.factory.test_connection(repo_url, token, username)

    # 새로운 메서드 추가 - 모든 GitHub 서비스 기능에 접근할 수 있도록 팩토리 반환
    def get_factory(self):
        """GitHub 서비스 팩토리를 반환합니다. 고급 기능이 필요한 경우 사용합니다."""
        return self.factory
