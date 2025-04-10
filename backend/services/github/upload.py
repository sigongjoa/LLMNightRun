"""
GitHub 파일 업로드 모듈

GitHub 리포지토리에 파일을 업로드하는 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Any
import requests
from fastapi import HTTPException

from .repository import RepositoryService
from .content import ContentService
from ...database.models import GitHubRepository


class UploadService:
    """GitHub 파일 업로드 서비스"""
    
    def __init__(self, repository_service: RepositoryService, content_service: ContentService):
        """
        서비스 초기화
        
        Args:
            repository_service: 저장소 서비스
            content_service: 콘텐츠 서비스
        """
        self.repository_service = repository_service
        self.content_service = content_service
        
    async def upload_to_github(
        self, 
        question_id: int, 
        folder_path: Optional[str] = None,
        repo_id: Optional[int] = None
    ) -> Dict[str, str]:
        """
        질문에 연결된 코드 스니펫을 GitHub 리포지토리에 업로드합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 저장할 폴더 경로 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            업로드 결과 정보
        """
        # 저장소 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 파일 준비
        files_to_upload = await self.content_service.prepare_files(question_id, folder_path)
        
        # 커밋 메시지 생성
        commit_message = await self.content_service.generate_commit_message(question_id)
        
        # 파일 업로드
        return await self._upload_files(repo, files_to_upload, commit_message)
    
    async def upload_file_to_github(
        self, 
        content: str, 
        file_path: str, 
        commit_message: Optional[str] = None,
        repo_id: Optional[int] = None,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        코드 또는 텍스트를 GitHub 저장소에 업로드합니다.
        
        Args:
            content: 업로드할 내용
            file_path: 파일 경로
            commit_message: 커밋 메시지 (없을 경우 기본값 사용)
            repo_id: 저장소 ID (선택 사항)
            branch: 브랜치 이름 (선택 사항)
            
        Returns:
            업로드 결과 정보
        """
        # 저장소 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 브랜치 설정
        if not branch:
            branch = repo.branch or "main"
        
        # 커밋 메시지 설정
        if not commit_message:
            commit_message = "LLMNightRun에서 업로드된 파일"
        
        # 파일 구성
        files_to_upload = [{
            "path": file_path,
            "content": content
        }]
        
        # 파일 업로드
        return await self._upload_files(repo, files_to_upload, commit_message, branch)
    
    async def _upload_files(
        self,
        repo: GitHubRepository,
        files: List[Dict[str, str]],
        commit_message: str,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        파일 목록을 GitHub에 업로드합니다.
        
        Args:
            repo: 저장소 정보
            files: 업로드할 파일 목록 (경로와 내용)
            commit_message: 커밋 메시지
            branch: 브랜치 이름 (선택 사항)
            
        Returns:
            업로드 결과 정보
        """
        if not branch:
            branch = repo.branch or "main"
            
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            api_base_url = "https://api.github.com"
            
            # 현재 리포지토리의 기본 브랜치 정보 가져오기
            repo_info_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}"
            repo_response = requests.get(repo_info_url, headers=headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            default_branch = branch or repo_data["default_branch"]
            
            # 최신 커밋 SHA 가져오기
            reference_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/refs/heads/{default_branch}"
            ref_response = requests.get(reference_url, headers=headers)
            ref_response.raise_for_status()
            ref_data = ref_response.json()
            base_sha = ref_data["object"]["sha"]
            
            # 최신 커밋의 트리 가져오기
            commit_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/commits/{base_sha}"
            commit_response = requests.get(commit_url, headers=headers)
            commit_response.raise_for_status()
            commit_data = commit_response.json()
            base_tree_sha = commit_data["tree"]["sha"]
            
            # 새 트리 생성
            tree_entries = []
            for file_data in files:
                # 파일 blob 생성
                blob_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/blobs"
                blob_data = {
                    "content": file_data["content"],
                    "encoding": "utf-8"
                }
                blob_response = requests.post(blob_url, headers=headers, json=blob_data)
                blob_response.raise_for_status()
                blob_sha = blob_response.json()["sha"]
                
                # 트리 항목 추가
                tree_entries.append({
                    "path": file_data["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
            
            # 새 트리 생성
            tree_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/trees"
            tree_data = {
                "base_tree": base_tree_sha,
                "tree": tree_entries
            }
            tree_response = requests.post(tree_url, headers=headers, json=tree_data)
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]
            
            # 새 커밋 생성
            new_commit_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/commits"
            commit_data = {
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_sha]
            }
            commit_response = requests.post(new_commit_url, headers=headers, json=commit_data)
            commit_response.raise_for_status()
            new_commit_sha = commit_response.json()["sha"]
            
            # reference 업데이트
            update_ref_url = f"{api_base_url}/repos/{repo.owner}/{repo.name}/git/refs/heads/{default_branch}"
            update_data = {
                "sha": new_commit_sha,
                "force": False
            }
            update_response = requests.patch(update_ref_url, headers=headers, json=update_data)
            update_response.raise_for_status()
            
            # 첫 번째 파일의 경로에서 폴더 경로 추출 (있는 경우)
            folder_path = ""
            if files and files[0]["path"]:
                path_parts = files[0]["path"].split("/")
                if len(path_parts) > 1:
                    folder_path = "/".join(path_parts[:-1])
            
            # 결과 반환
            return {
                "message": "파일이 성공적으로 GitHub에 업로드되었습니다.",
                "repo_url": f"https://github.com/{repo.owner}/{repo.name}",
                "folder_path": folder_path,
                "commit_message": commit_message
            }
        
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
