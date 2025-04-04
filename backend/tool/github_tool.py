"""
LLMNightRun GitHub 도구 모듈

GitHub 저장소와 상호 작용하는 도구를 정의합니다.
"""

import base64
import os
from typing import Dict, List, Optional

import requests

from backend.config import config
from backend.logger import get_logger
from backend.schema import ToolResult
from backend.tool.base import BaseTool


logger = get_logger(__name__)


class GitHubTool(BaseTool):
    """GitHub 도구
    
    GitHub 저장소와 상호 작용하는 도구입니다.
    파일 업로드, PR 생성 등의 기능을 제공합니다.
    """
    
    name: str = "github_tool"
    description: str = """
    GitHub 저장소와 상호 작용하는 도구입니다.
    파일 업로드, 브랜치 생성, PR 생성 등의 기능을 제공합니다.
    작업 공간의 파일을 GitHub에 업로드하거나, 원격 저장소의 파일을 가져올 수 있습니다.
    """
    
    def __init__(self):
        """GitHub 도구 초기화"""
        self.token = config.github.token
        self.username = config.github.username
        self.repo = config.github.repo
        
        # 기본 헤더
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
    
    async def execute(
        self,
        action: str,
        filepath: Optional[str] = None,
        content: Optional[str] = None,
        branch: str = "main",
        commit_message: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        target_branch: str = "main",
    ) -> ToolResult:
        """도구 실행
        
        Args:
            action: 수행할 작업 (upload, create_branch, create_pr, get_file)
            filepath: 파일 경로 (upload, get_file에서 사용)
            content: 파일 내용 (upload에서 사용)
            branch: 브랜치 이름
            commit_message: 커밋 메시지 (upload에서 사용)
            title: PR 제목 (create_pr에서 사용)
            body: PR 설명 (create_pr에서 사용)
            target_branch: PR 대상 브랜치 (create_pr에서 사용)
            
        Returns:
            ToolResult: 실행 결과
            
        Raises:
            ValueError: 필수 정보가 없거나 인자가 잘못된 경우
        """
        # GitHub 설정 검사
        if not all([self.token, self.username, self.repo]):
            return ToolResult(
                output="",
                error="GitHub 설정이 완료되지 않았습니다. 환경 변수 또는 설정 파일을 확인하세요."
            )
        
        try:
            # 작업 분기
            if action == "upload":
                return await self._upload_file(filepath, content, branch, commit_message)
            elif action == "create_branch":
                return await self._create_branch(branch)
            elif action == "create_pr":
                return await self._create_pr(title, body, branch, target_branch)
            elif action == "get_file":
                return await self._get_file(filepath, branch)
            else:
                return ToolResult(
                    output="",
                    error=f"지원하지 않는 작업: {action}"
                )
        except Exception as e:
            return ToolResult(
                output="",
                error=f"GitHub 작업 오류: {str(e)}"
            )
    
    async def _upload_file(
        self,
        filepath: Optional[str],
        content: Optional[str],
        branch: str,
        commit_message: Optional[str]
    ) -> ToolResult:
        """파일 업로드
        
        Args:
            filepath: 파일 경로
            content: 파일 내용
            branch: 브랜치 이름
            commit_message: 커밋 메시지
            
        Returns:
            ToolResult: 실행 결과
        """
        if not filepath:
            return ToolResult(output="", error="filepath는 필수 인자입니다.")
        
        if not content:
            return ToolResult(output="", error="content는 필수 인자입니다.")
        
        if not commit_message:
            commit_message = f"Update {filepath}"
        
        # API URL
        api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{filepath}"
        
        # 파일 내용을 Base64로 인코딩
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        # 커밋 데이터
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        
        # 기존 파일 확인 (업데이트인 경우 SHA 필요)
        try:
            check_response = requests.get(
                api_url,
                headers=self.headers,
                params={"ref": branch}
            )
            
            if check_response.status_code == 200:
                # 파일이 이미 존재하는 경우 SHA 포함
                sha = check_response.json().get("sha")
                data["sha"] = sha
        except:
            # 조회 실패는 무시 (새 파일 생성으로 진행)
            pass
        
        # API 요청
        response = requests.put(
            api_url,
            headers=self.headers,
            json=data
        )
        
        if response.status_code not in [200, 201]:
            return ToolResult(
                output="",
                error=f"파일 업로드 실패: {response.status_code}, {response.text}"
            )
        
        # 파일 URL 추출
        result = response.json()
        file_url = result.get("content", {}).get("html_url", "")
        
        return ToolResult(
            output=f"파일 '{filepath}'이(가) 성공적으로 업로드되었습니다.\nURL: {file_url}"
        )
    
    async def _create_branch(self, branch: str) -> ToolResult:
        """브랜치 생성
        
        Args:
            branch: 브랜치 이름
            
        Returns:
            ToolResult: 실행 결과
        """
        # main 브랜치의 최신 커밋 SHA 가져오기
        sha_url = f"https://api.github.com/repos/{self.username}/{self.repo}/git/refs/heads/main"
        sha_response = requests.get(sha_url, headers=self.headers)
        
        if sha_response.status_code != 200:
            return ToolResult(
                output="",
                error=f"main 브랜치 정보 조회 실패: {sha_response.status_code}, {sha_response.text}"
            )
        
        sha = sha_response.json()["object"]["sha"]
        
        # 새 브랜치 생성
        branch_url = f"https://api.github.com/repos/{self.username}/{self.repo}/git/refs"
        branch_data = {
            "ref": f"refs/heads/{branch}",
            "sha": sha
        }
        
        branch_response = requests.post(
            branch_url,
            headers=self.headers,
            json=branch_data
        )
        
        if branch_response.status_code != 201:
            return ToolResult(
                output="",
                error=f"브랜치 생성 실패: {branch_response.status_code}, {branch_response.text}"
            )
        
        return ToolResult(
            output=f"브랜치 '{branch}'이(가) 성공적으로 생성되었습니다."
        )
    
    async def _create_pr(
        self,
        title: Optional[str],
        body: Optional[str],
        branch: str,
        target_branch: str
    ) -> ToolResult:
        """PR 생성
        
        Args:
            title: PR 제목
            body: PR 설명
            branch: 소스 브랜치
            target_branch: 대상 브랜치
            
        Returns:
            ToolResult: 실행 결과
        """
        if not title:
            return ToolResult(output="", error="title은 필수 인자입니다.")
        
        if not body:
            body = f"PR from {branch} to {target_branch}"
        
        # PR 데이터
        pr_data = {
            "title": title,
            "body": body,
            "head": branch,
            "base": target_branch
        }
        
        # PR 생성
        pr_url = f"https://api.github.com/repos/{self.username}/{self.repo}/pulls"
        pr_response = requests.post(
            pr_url,
            headers=self.headers,
            json=pr_data
        )
        
        if pr_response.status_code != 201:
            return ToolResult(
                output="",
                error=f"PR 생성 실패: {pr_response.status_code}, {pr_response.text}"
            )
        
        # PR URL 추출
        pr_url = pr_response.json().get("html_url", "")
        
        return ToolResult(
            output=f"PR이 성공적으로 생성되었습니다.\nURL: {pr_url}"
        )
    
    async def _get_file(self, filepath: str, branch: str) -> ToolResult:
        """파일 가져오기
        
        Args:
            filepath: 파일 경로
            branch: 브랜치 이름
            
        Returns:
            ToolResult: 실행 결과
        """
        if not filepath:
            return ToolResult(output="", error="filepath는 필수 인자입니다.")
        
        # API URL
        api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{filepath}"
        
        # API 요청
        response = requests.get(
            api_url,
            headers=self.headers,
            params={"ref": branch}
        )
        
        if response.status_code != 200:
            return ToolResult(
                output="",
                error=f"파일 조회 실패: {response.status_code}, {response.text}"
            )
        
        # 파일 내용 디코딩
        result = response.json()
        content = base64.b64decode(result.get("content", "")).decode("utf-8")
        
        return ToolResult(
            output=f"파일 '{filepath}' 내용:\n\n{content}"
        )