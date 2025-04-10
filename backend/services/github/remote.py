"""
GitHub 원격 API 조작 모듈

GitHub API를 사용하여 원격 저장소를 관리하는 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Any
import requests
from fastapi import HTTPException

from .repository import RepositoryService


class RemoteService:
    """GitHub 원격 API 서비스"""
    
    def __init__(self, repository_service: RepositoryService):
        """
        서비스 초기화
        
        Args:
            repository_service: 저장소 서비스
        """
        self.repository_service = repository_service
    
    async def list_remote_repositories(self, repo_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        사용자의 GitHub 저장소 목록을 가져옵니다.
        
        Args:
            repo_id: 특정 저장소 ID (선택 사항)
        
        Returns:
            저장소 목록 (이름, 설명, URL 등)
        """
        # 저장소 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # GitHub API 호출
            repos_url = f"https://api.github.com/user/repos?sort=updated&per_page=100"
            response = requests.get(repos_url, headers=headers)
            response.raise_for_status()
            
            # 결과 파싱
            repos = response.json()
            result = []
            
            for repo_data in repos:
                result.append({
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data["description"],
                    "url": repo_data["html_url"],
                    "default_branch": repo_data["default_branch"],
                    "private": repo_data["private"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "language": repo_data["language"],
                    "size": repo_data["size"]
                })
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def create_remote_repository(
        self, 
        name: str, 
        description: str = "", 
        private: bool = True, 
        auto_init: bool = True,
        repo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        새 GitHub 저장소를 생성합니다.
        
        Args:
            name: 저장소 이름
            description: 저장소 설명
            private: 비공개 여부
            auto_init: README.md 파일로 초기화 여부
            repo_id: 사용할 로컬 저장소 정보 ID (선택 사항)
            
        Returns:
            생성된 저장소 정보
        """
        # 저장소 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # GitHub API 호출
            create_url = f"https://api.github.com/user/repos"
            data = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": auto_init
            }
            
            response = requests.post(create_url, headers=headers, json=data)
            response.raise_for_status()
            
            # 결과 파싱
            new_repo = response.json()
            
            return {
                "message": "저장소가 성공적으로 생성되었습니다.",
                "name": new_repo["name"],
                "full_name": new_repo["full_name"],
                "url": new_repo["html_url"],
                "description": new_repo["description"],
                "private": new_repo["private"],
                "default_branch": new_repo["default_branch"]
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
    
    async def get_repository_info(
        self,
        owner: str,
        repo_name: str,
        repo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        GitHub 저장소 정보를 가져옵니다.
        
        Args:
            owner: 저장소 소유자
            repo_name: 저장소 이름
            repo_id: 사용할 로컬 저장소 정보 ID (선택 사항)
            
        Returns:
            저장소 정보
        """
        # 토큰 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # GitHub API 호출
            repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            response = requests.get(repo_url, headers=headers)
            response.raise_for_status()
            
            # 결과 파싱
            repo_data = response.json()
            
            return {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data["description"],
                "url": repo_data["html_url"],
                "default_branch": repo_data["default_branch"],
                "private": repo_data["private"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "language": repo_data["language"],
                "size": repo_data["size"],
                "owner": {
                    "login": repo_data["owner"]["login"],
                    "avatar_url": repo_data["owner"]["avatar_url"],
                    "url": repo_data["owner"]["html_url"]
                }
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
    
    async def list_branches(
        self,
        owner: str,
        repo_name: str,
        repo_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        GitHub 저장소의 브랜치 목록을 가져옵니다.
        
        Args:
            owner: 저장소 소유자
            repo_name: 저장소 이름
            repo_id: 사용할 로컬 저장소 정보 ID (선택 사항)
            
        Returns:
            브랜치 목록
        """
        # 토큰 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # GitHub API 호출
            branches_url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"
            response = requests.get(branches_url, headers=headers)
            response.raise_for_status()
            
            # 결과 파싱
            branches = response.json()
            result = []
            
            for branch in branches:
                result.append({
                    "name": branch["name"],
                    "protected": branch.get("protected", False),
                    "commit_sha": branch["commit"]["sha"]
                })
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def create_branch(
        self,
        owner: str,
        repo_name: str,
        branch_name: str,
        source_branch: Optional[str] = None,
        repo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        GitHub 저장소에 새 브랜치를 생성합니다.
        
        Args:
            owner: 저장소 소유자
            repo_name: 저장소 이름
            branch_name: 새 브랜치 이름
            source_branch: 소스 브랜치 이름 (선택 사항, 기본값은 기본 브랜치)
            repo_id: 사용할 로컬 저장소 정보 ID (선택 사항)
            
        Returns:
            생성된 브랜치 정보
        """
        # 토큰 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        try:
            # GitHub API 설정
            headers = {
                "Authorization": f"token {repo.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # 소스 브랜치 정보 가져오기
            if not source_branch:
                # 저장소 기본 브랜치 가져오기
                repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
                repo_response = requests.get(repo_url, headers=headers)
                repo_response.raise_for_status()
                source_branch = repo_response.json()["default_branch"]
            
            # 소스 브랜치의 최신 커밋 SHA 가져오기
            ref_url = f"https://api.github.com/repos/{owner}/{repo_name}/git/refs/heads/{source_branch}"
            ref_response = requests.get(ref_url, headers=headers)
            ref_response.raise_for_status()
            source_sha = ref_response.json()["object"]["sha"]
            
            # 새 브랜치 생성
            create_url = f"https://api.github.com/repos/{owner}/{repo_name}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": source_sha
            }
            
            response = requests.post(create_url, headers=headers, json=data)
            response.raise_for_status()
            
            return {
                "message": f"브랜치 '{branch_name}'이(가) 성공적으로 생성되었습니다.",
                "name": branch_name,
                "source_branch": source_branch,
                "sha": source_sha
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
