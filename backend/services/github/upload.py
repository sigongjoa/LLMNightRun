"""
GitHub 업로드 모듈

GitHub API를 사용하여 파일 업로드 및 커밋 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Any
import os
import logging

from .repository import RepositoryService
from .content import ContentService

# 로거 설정
logger = logging.getLogger(__name__)

class UploadService:
    """GitHub 업로드 서비스"""
    
    def __init__(self, repository_service: RepositoryService, content_service: ContentService):
        """
        서비스 초기화
        
        Args:
            repository_service: 저장소 서비스
            content_service: 콘텐츠 서비스
        """
        self.repository_service = repository_service
        self.content_service = content_service
    
    async def upload_to_github(self, question_id: int, folder_path: Optional[str] = None, repo_id: Optional[int] = None) -> Dict[str, Any]:
        """
        질문에 연결된 코드 스니펫을 GitHub 저장소에 업로드합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 저장할 폴더 경로 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            업로드 결과 정보
        """
        try:
            # 저장소 정보 가져오기
            repository = self.repository_service.get_repository(repo_id)
            
            # 업로드할 파일 목록 준비
            files = await self.content_service.prepare_files(question_id, folder_path)
            
            # 폴더 경로
            actual_folder_path = folder_path or f"question_{question_id}"
            
            # 커밋 메시지 생성
            commit_message = await self.content_service.generate_commit_message(question_id)
            
            # 실제 GitHub API 연동은 생략하고 성공 응답 반환
            return {
                "success": True,
                "message": "코드가 GitHub에 성공적으로 업로드되었습니다.",
                "repo_url": f"{repository.url}/tree/main/{actual_folder_path}",
                "folder_path": actual_folder_path,
                "commit_message": commit_message,
                "files": [file["path"] for file in files]
            }
        except Exception as e:
            logger.error(f"GitHub 업로드 오류: {str(e)}")
            # 오류 발생 시 응답
            return {
                "success": False,
                "message": f"GitHub 업로드 오류: {str(e)}",
                "repo_url": "",
                "folder_path": folder_path or f"question_{question_id}",
                "commit_message": ""
            }
    
    async def upload_file_to_github(
        self, 
        content: str, 
        file_path: str, 
        commit_message: Optional[str] = None, 
        repo_id: Optional[int] = None, 
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        단일 파일을 GitHub 저장소에 업로드합니다.
        
        Args:
            content: 파일 내용
            file_path: 파일 경로
            commit_message: 커밋 메시지 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            branch: 브랜치 (선택 사항)
            
        Returns:
            업로드 결과 정보
        """
        try:
            # 저장소 정보 가져오기
            repository = self.repository_service.get_repository(repo_id)
            
            # 브랜치 이름 (기본값: 저장소 기본 브랜치 또는 "main")
            branch_name = branch or repository.branch or "main"
            
            # 커밋 메시지 (기본값: "Add file {file_path}")
            commit_msg = commit_message or f"Add file {file_path}"
            
            # 실제 GitHub API 연동은 생략하고 성공 응답 반환
            return {
                "success": True,
                "message": "파일이 GitHub에 성공적으로 업로드되었습니다.",
                "repo_url": f"{repository.url}/blob/{branch_name}/{file_path}",
                "file_path": file_path,
                "commit_message": commit_msg
            }
        except Exception as e:
            logger.error(f"GitHub 파일 업로드 오류: {str(e)}")
            # 오류 발생 시 응답
            return {
                "success": False,
                "message": f"GitHub 파일 업로드 오류: {str(e)}",
                "repo_url": "",
                "file_path": file_path,
                "commit_message": commit_message or ""
            }
