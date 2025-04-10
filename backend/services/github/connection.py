"""
GitHub 연결 테스트 모듈

GitHub API와의 연결 및 인증을 테스트하는 기능을 제공합니다.
"""

import aiohttp
import logging
from typing import Dict, Any, Optional

from ...models.github_config import GitHubTestConnectionResponse

logger = logging.getLogger(__name__)

class ConnectionService:
    """GitHub 연결 테스트 서비스"""
    
    def __init__(self, db):
        """서비스 초기화"""
        self.db = db
    
    async def test_connection(
        self, 
        repo_url: str, 
        token: str, 
        username: str
    ) -> GitHubTestConnectionResponse:
        """
        GitHub 연결 테스트
        
        Args:
            repo_url: 저장소 URL
            token: GitHub 토큰
            username: GitHub 사용자 이름
            
        Returns:
            GitHubTestConnectionResponse: 연결 테스트 결과
        """
        # repo_url에서 소유자/저장소 이름 추출
        repo_parts = repo_url.rstrip('/').split('/')
        if len(repo_parts) < 2:
            return GitHubTestConnectionResponse(
                success=False,
                message="잘못된 저장소 URL 형식입니다.",
                error="URL은 'owner/repo' 형식이어야 합니다."
            )
        
        # 저장소 이름 추출 (URL 마지막 부분)
        repo_name = repo_parts[-1]
        
        # 저장소 소유자 추출 (URL 마지막에서 두 번째 부분)
        owner = repo_parts[-2] if len(repo_parts) >= 2 else username
        
        # .git 확장자 제거 (있는 경우)
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # GitHub API 호출을 위한 헤더 설정
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}"
        }
        
        try:
            # GitHub API 호출하여 저장소 정보 확인
            async with aiohttp.ClientSession() as session:
                # 사용자 정보 확인
                async with session.get(
                    f"https://api.github.com/user",
                    headers=headers
                ) as user_response:
                    if user_response.status != 200:
                        error_info = await user_response.json()
                        return GitHubTestConnectionResponse(
                            success=False,
                            message="GitHub 인증에 실패했습니다.",
                            error=error_info.get("message", "알 수 없는 오류")
                        )
                    
                    user_info = await user_response.json()
                    
                    # 사용자 이름 확인
                    if user_info.get("login") != username:
                        return GitHubTestConnectionResponse(
                            success=False,
                            message="GitHub 사용자 이름 불일치",
                            error=f"토큰에 연결된 사용자({user_info.get('login')})가 입력한 사용자({username})와 다릅니다."
                        )
                
                # 저장소 정보 확인
                repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
                async with session.get(
                    repo_url,
                    headers=headers
                ) as repo_response:
                    if repo_response.status == 404:
                        # 저장소가 존재하지 않는 경우
                        return GitHubTestConnectionResponse(
                            success=False,
                            message="GitHub 저장소를 찾을 수 없습니다.",
                            error=f"저장소 '{owner}/{repo_name}'가 존재하지 않거나 접근 권한이 없습니다."
                        )
                    elif repo_response.status != 200:
                        # 기타 오류
                        error_info = await repo_response.json()
                        return GitHubTestConnectionResponse(
                            success=False,
                            message="GitHub 저장소 접근에 실패했습니다.",
                            error=error_info.get("message", "알 수 없는 오류")
                        )
                    
                    # 저장소 정보 가져오기
                    repo_info = await repo_response.json()
                    
                    # 연결 테스트 성공
                    return GitHubTestConnectionResponse(
                        success=True,
                        message="GitHub 연결 테스트 성공",
                        repo_info={
                            "name": repo_info.get("name"),
                            "full_name": repo_info.get("full_name"),
                            "description": repo_info.get("description"),
                            "default_branch": repo_info.get("default_branch"),
                            "private": repo_info.get("private"),
                            "owner": {
                                "login": repo_info.get("owner", {}).get("login")
                            }
                        }
                    )
        
        except aiohttp.ClientError as e:
            # 네트워크 오류
            logger.error(f"GitHub API 연결 중 오류 발생: {str(e)}")
            return GitHubTestConnectionResponse(
                success=False,
                message="GitHub API 연결에 실패했습니다.",
                error=str(e)
            )
        
        except Exception as e:
            # 기타 오류
            logger.error(f"GitHub 연결 테스트 중 예상치 못한 오류 발생: {str(e)}")
            return GitHubTestConnectionResponse(
                success=False,
                message="GitHub 연결 테스트 중 오류가 발생했습니다.",
                error=str(e)
            )
