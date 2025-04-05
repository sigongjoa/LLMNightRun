"""
GitHub 서비스 모듈

GitHub API와의 통신을 관리하는 서비스를 제공합니다.
"""

import base64
import os
import logging
import requests
from typing import Dict, List, Optional, Any, Union

from ..config import settings
from ..exceptions import GitHubError

# 로거 설정
logger = logging.getLogger(__name__)


class GitHubService:
    """GitHub API와 통신하는 서비스 클래스"""
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None, repo: Optional[str] = None):
        """서비스 초기화"""
        self.token = token or settings.github.token
        self.username = username or settings.github.username
        self.repo = repo or settings.github.repo
        
        # GitHub 설정 검증
        if not all([self.token, self.username, self.repo]):
            logger.warning("GitHub 설정이 완전하지 않습니다. token, username, repo가 모두 필요합니다.")
        
        # 기본 헤더
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
    
    def get_file(self, filepath: str, branch: str = "main") -> Dict[str, Any]:
        """
        GitHub에서 파일 가져오기
        
        Args:
            filepath: 파일 경로
            branch: 브랜치 이름
            
        Returns:
            파일 정보 및 내용
            
        Raises:
            GitHubError: API 호출 실패 또는 파일을 찾을 수 없는 경우
        """
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{filepath}"
            
            # API 요청
            response = requests.get(
                api_url,
                headers=self.headers,
                params={"ref": branch}
            )
            
            # 응답 확인
            if response.status_code != 200:
                raise GitHubError(f"GitHub API 오류: {response.status_code}, {response.text}")
            
            # 결과 파싱
            result = response.json()
            
            # 파일 내용이 있는 경우 디코딩
            if "content" in result:
                result["decoded_content"] = base64.b64decode(result["content"]).decode("utf-8")
            
            return result
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub 파일 조회 오류: {str(e)}")
            raise GitHubError(f"GitHub 파일 조회 실패: {str(e)}")
    
    def create_or_update_file(
        self,
        filepath: str,
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        GitHub에 파일 생성 또는 업데이트
        
        Args:
            filepath: 파일 경로
            content: 파일 내용
            commit_message: 커밋 메시지
            branch: 브랜치 이름
            
        Returns:
            결과 정보
            
        Raises:
            GitHubError: API 호출 실패 또는 권한 부족한 경우
        """
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{filepath}"
            
            # 파일 내용을 Base64로 인코딩
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            
            # 요청 데이터 준비
            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": branch
            }
            
            # 기존 파일이 있는 경우 SHA 필요
            try:
                existing_file = self.get_file(filepath, branch)
                if "sha" in existing_file:
                    data["sha"] = existing_file["sha"]
            except:
                # 파일이 없는 경우 무시
                pass
            
            # API 요청
            response = requests.put(
                api_url,
                headers=self.headers,
                json=data
            )
            
            # 응답 확인
            if response.status_code not in [200, 201]:
                raise GitHubError(f"GitHub API 오류: {response.status_code}, {response.text}")
            
            return response.json()
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub 파일 업로드 오류: {str(e)}")
            raise GitHubError(f"GitHub 파일 업로드 실패: {str(e)}")
    
    def create_branch(self, branch: str, source_branch: str = "main") -> Dict[str, Any]:
        """
        GitHub에서 새 브랜치 생성
        
        Args:
            branch: 새 브랜치 이름
            source_branch: 소스 브랜치 이름
            
        Returns:
            결과 정보
            
        Raises:
            GitHubError: API 호출 실패 또는 브랜치가 이미 존재하는 경우
        """
        try:
            # 소스 브랜치의 최신 커밋 SHA 조회
            ref_url = f"https://api.github.com/repos/{self.username}/{self.repo}/git/refs/heads/{source_branch}"
            ref_response = requests.get(ref_url, headers=self.headers)
            
            if ref_response.status_code != 200:
                raise GitHubError(f"GitHub API 오류: 소스 브랜치 정보 조회 실패 - {ref_response.status_code}, {ref_response.text}")
            
            sha = ref_response.json()["object"]["sha"]
            
            # 새 브랜치 생성
            create_url = f"https://api.github.com/repos/{self.username}/{self.repo}/git/refs"
            create_data = {
                "ref": f"refs/heads/{branch}",
                "sha": sha
            }
            
            create_response = requests.post(
                create_url,
                headers=self.headers,
                json=create_data
            )
            
            # 응답 확인
            if create_response.status_code not in [201]:
                # 브랜치가 이미 존재하는 경우 (409) 정보 반환
                if create_response.status_code == 409:
                    return {
                        "message": f"브랜치 '{branch}'가 이미 존재합니다.",
                        "exists": True
                    }
                
                raise GitHubError(f"GitHub API 오류: 브랜치 생성 실패 - {create_response.status_code}, {create_response.text}")
            
            return create_response.json()
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub 브랜치 생성 오류: {str(e)}")
            raise GitHubError(f"GitHub 브랜치 생성 실패: {str(e)}")
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        GitHub에서 Pull Request 생성
        
        Args:
            title: PR 제목
            body: PR 내용
            head_branch: 소스 브랜치
            base_branch: 대상 브랜치
            
        Returns:
            결과 정보
            
        Raises:
            GitHubError: API 호출 실패 또는 권한 부족한 경우
        """
        try:
            # Pull Request 생성 API URL
            pr_url = f"https://api.github.com/repos/{self.username}/{self.repo}/pulls"
            
            # 요청 데이터 준비
            data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
            
            # API 요청
            response = requests.post(
                pr_url,
                headers=self.headers,
                json=data
            )
            
            # 응답 확인
            if response.status_code not in [201]:
                raise GitHubError(f"GitHub API 오류: PR 생성 실패 - {response.status_code}, {response.text}")
            
            return response.json()
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub PR 생성 오류: {str(e)}")
            raise GitHubError(f"GitHub PR 생성 실패: {str(e)}")
    
    def get_repository_contents(self, path: str = "", branch: str = "main") -> List[Dict[str, Any]]:
        """
        GitHub 저장소 내용 조회
        
        Args:
            path: 저장소 내 경로
            branch: 브랜치 이름
            
        Returns:
            파일 및 디렉토리 목록
            
        Raises:
            GitHubError: API 호출 실패 또는 경로가 없는 경우
        """
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{path}"
            
            # API 요청
            response = requests.get(
                api_url,
                headers=self.headers,
                params={"ref": branch}
            )
            
            # 응답 확인
            if response.status_code != 200:
                raise GitHubError(f"GitHub API 오류: 저장소 내용 조회 실패 - {response.status_code}, {response.text}")
            
            # 결과 파싱
            results = response.json()
            
            # 리스트 타입인지 확인 (단일 파일인 경우 딕셔너리로 반환됨)
            if not isinstance(results, list):
                results = [results]
            
            return results
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub 저장소 내용 조회 오류: {str(e)}")
            raise GitHubError(f"GitHub 저장소 내용 조회 실패: {str(e)}")
    
    def get_commits(self, branch: str = "main", path: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        GitHub 커밋 내역 조회
        
        Args:
            branch: 브랜치 이름
            path: 특정 파일 경로 (선택 사항)
            limit: 최대 조회 개수
            
        Returns:
            커밋 목록
            
        Raises:
            GitHubError: API 호출 실패 또는 브랜치가 없는 경우
        """
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/commits"
            
            # 요청 파라미터
            params = {
                "sha": branch,
                "per_page": limit
            }
            
            # 특정 파일 경로가 있는 경우
            if path:
                params["path"] = path
            
            # API 요청
            response = requests.get(
                api_url,
                headers=self.headers,
                params=params
            )
            
            # 응답 확인
            if response.status_code != 200:
                raise GitHubError(f"GitHub API 오류: 커밋 내역 조회 실패 - {response.status_code}, {response.text}")
            
            return response.json()
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub 커밋 내역 조회 오류: {str(e)}")
            raise GitHubError(f"GitHub 커밋 내역 조회 실패: {str(e)}")
    
    def generate_commit_message(self, changes: List[Dict[str, str]]) -> str:
        """
        변경 내용에 기반한 커밋 메시지 생성
        
        Args:
            changes: 변경된 파일 목록 (경로, 변경 유형)
            
        Returns:
            생성된 커밋 메시지
        """
        # 변경 유형별로 그룹화
        added = []
        modified = []
        deleted = []
        
        for change in changes:
            path = change.get("path", "")
            change_type = change.get("type", "")
            
            if change_type == "add" or change_type == "added":
                added.append(path)
            elif change_type == "modify" or change_type == "modified":
                modified.append(path)
            elif change_type == "delete" or change_type == "deleted":
                deleted.append(path)
        
        # 메시지 구성
        message_parts = []
        
        if len(added) + len(modified) + len(deleted) == 1:
            # 단일 파일 변경인 경우
            if added:
                return f"Add {added[0]}"
            elif modified:
                return f"Update {modified[0]}"
            elif deleted:
                return f"Delete {deleted[0]}"
        
        # 여러 파일 변경인 경우
        if added:
            if len(added) <= 3:
                message_parts.append(f"Add {', '.join(added)}")
            else:
                message_parts.append(f"Add {len(added)} files")
        
        if modified:
            if len(modified) <= 3:
                message_parts.append(f"Update {', '.join(modified)}")
            else:
                message_parts.append(f"Update {len(modified)} files")
        
        if deleted:
            if len(deleted) <= 3:
                message_parts.append(f"Delete {', '.join(deleted)}")
            else:
                message_parts.append(f"Delete {len(deleted)} files")
        
        # 최종 메시지
        if message_parts:
            return " / ".join(message_parts)
        else:
            return "Update repository content"
    
    def analyze_pr_changes(self, pr_number: int) -> Dict[str, Any]:
        """
        Pull Request 변경 내용 분석
        
        Args:
            pr_number: Pull Request 번호
            
        Returns:
            분석 결과
            
        Raises:
            GitHubError: API 호출 실패 또는 PR을 찾을 수 없는 경우
        """
        try:
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.username}/{self.repo}/pulls/{pr_number}/files"
            
            # API 요청
            response = requests.get(
                api_url,
                headers=self.headers
            )
            
            # 응답 확인
            if response.status_code != 200:
                raise GitHubError(f"GitHub API 오류: PR 변경 내용 조회 실패 - {response.status_code}, {response.text}")
            
            # 결과 파싱
            files = response.json()
            
            # 변경 유형별로 그룹화
            added = []
            modified = []
            deleted = []
            
            # 확장자별 통계
            extensions = {}
            
            # 변경 라인 수
            total_additions = 0
            total_deletions = 0
            
            for file in files:
                filename = file.get("filename", "")
                status = file.get("status", "")
                additions = file.get("additions", 0)
                deletions = file.get("deletions", 0)
                
                # 변경 유형 분류
                if status == "added":
                    added.append(filename)
                elif status == "modified":
                    modified.append(filename)
                elif status == "removed":
                    deleted.append(filename)
                
                # 확장자 통계
                _, ext = os.path.splitext(filename)
                ext = ext.lstrip(".").lower() if ext else "none"
                extensions[ext] = extensions.get(ext, 0) + 1
                
                # 라인 수 합산
                total_additions += additions
                total_deletions += deletions
            
            # 분석 결과
            return {
                "added_count": len(added),
                "added_files": added,
                "modified_count": len(modified),
                "modified_files": modified,
                "deleted_count": len(deleted),
                "deleted_files": deleted,
                "extensions": extensions,
                "total_changes": len(files),
                "total_additions": total_additions,
                "total_deletions": total_deletions
            }
        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"GitHub PR 분석 오류: {str(e)}")
            raise GitHubError(f"GitHub PR 분석 실패: {str(e)}")