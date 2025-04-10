"""
GitHub 서비스 팩토리 모듈

GitHub 관련 서비스를 생성하고 관리하는 팩토리 클래스를 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any, Union

from .repository import RepositoryService
from .content import ContentService
from .models import GitHubRepositoryData


class GitHubServiceFactory:
    """
    GitHub 서비스 팩토리 클래스
    
    GitHub 관련 다양한 서비스를 생성하고 관리합니다.
    """
    
    def __init__(self, db: Session):
        """
        팩토리 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self.repository_service = RepositoryService(db)
        self.content_service = ContentService(db, self.repository_service)
    
    def get_repository(self, repo_id: Optional[int] = None):
        """
        저장소 정보를 가져옵니다.
        
        Args:
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            저장소 정보
        """
        return self.repository_service.get_repository(repo_id)
    
    def create_repository(self, repo_data: GitHubRepositoryData):
        """
        새 저장소 정보를 데이터베이스에 추가합니다.
        
        Args:
            repo_data: 저장소 정보
            
        Returns:
            생성된 저장소 정보
        """
        return self.repository_service.create_repository(repo_data)
    
    def update_repository(self, repo_id: int, repo_data: dict):
        """
        저장소 정보를 업데이트합니다.
        
        Args:
            repo_id: 저장소 ID
            repo_data: 업데이트할 정보
            
        Returns:
            업데이트된 저장소 정보
        """
        return self.repository_service.update_repository(repo_id, repo_data)
    
    def delete_repository(self, repo_id: int):
        """
        저장소 정보를 삭제합니다.
        
        Args:
            repo_id: 저장소 ID
            
        Returns:
            성공 여부
        """
        return self.repository_service.delete_repository(repo_id)
    
    def get_repositories(self, project_id: Optional[int] = None):
        """
        저장소 목록을 조회합니다.
        
        Args:
            project_id: 프로젝트 ID (선택 사항)
            
        Returns:
            저장소 목록
        """
        return self.repository_service.get_repositories(project_id)
    
    async def generate_commit_message(self, question_id: int):
        """
        커밋 메시지를 생성합니다.
        
        Args:
            question_id: 질문 ID
            
        Returns:
            생성된 커밋 메시지
        """
        return await self.content_service.generate_commit_message(question_id)
    
    async def generate_readme(self, question_id: int):
        """
        README 파일을 생성합니다.
        
        Args:
            question_id: 질문 ID
            
        Returns:
            생성된 README 내용
        """
        return await self.content_service.generate_readme(question_id)
    
    async def upload_to_github(self, question_id: int, folder_path: Optional[str] = None, repo_id: Optional[int] = None):
        """
        코드 스니펫을 GitHub에 업로드합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 폴더 경로 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            업로드 결과
        """
        return await self.content_service.upload_to_github(question_id, folder_path, repo_id)
    
    async def upload_file_to_github(self, content: str, file_path: str, commit_message: Optional[str] = None, 
                                  repo_id: Optional[int] = None, branch: Optional[str] = None):
        """
        파일을 GitHub에 업로드합니다.
        
        Args:
            content: 파일 내용
            file_path: 파일 경로
            commit_message: 커밋 메시지 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            branch: 브랜치 (선택 사항)
            
        Returns:
            업로드 결과
        """
        return await self.content_service.upload_file_to_github(content, file_path, commit_message, repo_id, branch)
    
    async def list_remote_repositories(self, repo_id: Optional[int] = None):
        """
        원격 저장소 목록을 조회합니다.
        
        Args:
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            원격 저장소 목록
        """
        return await self.content_service.list_remote_repositories(repo_id)
    
    async def create_remote_repository(self, name: str, description: str = "", private: bool = True, 
                                      auto_init: bool = True, repo_id: Optional[int] = None):
        """
        원격 저장소를 생성합니다.
        
        Args:
            name: 저장소 이름
            description: 저장소 설명 (선택 사항)
            private: 비공개 여부 (선택 사항)
            auto_init: 자동 초기화 여부 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            생성된 원격 저장소 정보
        """
        return await self.content_service.create_remote_repository(name, description, private, auto_init, repo_id)
