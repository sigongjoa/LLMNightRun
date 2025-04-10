"""
GitHub 서비스 팩토리 모듈

다양한 GitHub 서비스 구현체를 생성하고 관리하는 팩토리 클래스를 제공합니다.
"""

from sqlalchemy.orm import Session

from .repository import RepositoryService
from .content import ContentService
from .upload import UploadService
from .remote import RemoteService
from .models import GitHubRepositoryData


class GitHubServiceFactory:
    """GitHub 서비스 팩토리"""
    
    def __init__(self, db: Session):
        """
        서비스 팩토리 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self._repository_service = None
        self._content_service = None
        self._upload_service = None
        self._remote_service = None
    
    @property
    def repository_service(self) -> RepositoryService:
        """저장소 서비스 인스턴스를 반환합니다."""
        if not self._repository_service:
            self._repository_service = RepositoryService(self.db)
        return self._repository_service
    
    @property
    def content_service(self) -> ContentService:
        """콘텐츠 생성 서비스 인스턴스를 반환합니다."""
        if not self._content_service:
            self._content_service = ContentService(self.db)
        return self._content_service
    
    @property
    def upload_service(self) -> UploadService:
        """업로드 서비스 인스턴스를 반환합니다."""
        if not self._upload_service:
            self._upload_service = UploadService(
                self.repository_service,
                self.content_service
            )
        return self._upload_service
    
    @property
    def remote_service(self) -> RemoteService:
        """원격 API 서비스 인스턴스를 반환합니다."""
        if not self._remote_service:
            self._remote_service = RemoteService(self.repository_service)
        return self._remote_service
    
    # 기존 메서드들을 편의를 위해 팩토리 클래스에 추가
    
    def get_repository(self, repo_id=None):
        """저장소 정보를 가져옵니다."""
        return self.repository_service.get_repository(repo_id)
    
    def create_repository(self, repo_data):
        """새 저장소 정보를 데이터베이스에 추가합니다."""
        return self.repository_service.create_repository(repo_data)
    
    def update_repository(self, repo_id, repo_data):
        """저장소 정보를 업데이트합니다."""
        return self.repository_service.update_repository(repo_id, repo_data)
    
    def delete_repository(self, repo_id):
        """저장소 정보를 삭제합니다."""
        return self.repository_service.delete_repository(repo_id)
    
    def get_repositories(self, project_id=None):
        """저장소 목록을 조회합니다."""
        return self.repository_service.get_repositories(project_id)
    
    async def generate_commit_message(self, question_id):
        """커밋 메시지를 생성합니다."""
        return await self.content_service.generate_commit_message(question_id)
    
    async def generate_readme(self, question_id):
        """README 파일을 생성합니다."""
        return await self.content_service.generate_readme(question_id)
    
    async def upload_to_github(self, question_id, folder_path=None, repo_id=None):
        """코드 스니펫을 GitHub에 업로드합니다."""
        return await self.upload_service.upload_to_github(question_id, folder_path, repo_id)
    
    async def upload_file_to_github(self, content, file_path, commit_message=None, repo_id=None, branch=None):
        """파일을 GitHub에 업로드합니다."""
        return await self.upload_service.upload_file_to_github(content, file_path, commit_message, repo_id, branch)
    
    async def list_remote_repositories(self, repo_id=None):
        """원격 저장소 목록을 조회합니다."""
        return await self.remote_service.list_remote_repositories(repo_id)
    
    async def create_remote_repository(self, name, description="", private=True, auto_init=True, repo_id=None):
        """원격 저장소를 생성합니다."""
        return await self.remote_service.create_remote_repository(name, description, private, auto_init, repo_id)
    
    async def get_repository_info(self, owner, repo_name, repo_id=None):
        """원격 저장소 정보를 조회합니다."""
        return await self.remote_service.get_repository_info(owner, repo_name, repo_id)
    
    async def list_branches(self, owner, repo_name, repo_id=None):
        """브랜치 목록을 조회합니다."""
        return await self.remote_service.list_branches(owner, repo_name, repo_id)
    
    async def create_branch(self, owner, repo_name, branch_name, source_branch=None, repo_id=None):
        """새 브랜치를 생성합니다."""
        return await self.remote_service.create_branch(owner, repo_name, branch_name, source_branch, repo_id)
