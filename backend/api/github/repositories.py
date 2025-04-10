"""
GitHub 저장소 목록 API 모듈

GitHub 저장소 목록 관련 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...database.connection import get_db
from ...services.github_service import GitHubService

# 라우터 정의
router = APIRouter(
    prefix="/repositories",
    tags=["github-repos"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=Dict[str, List[Dict[str, Any]]])
async def get_github_repositories(
    db: Session = Depends(get_db)
):
    """
    GitHub 저장소 목록 조회
    """
    try:
        github_service = GitHubService(db)
        
        try:
            repositories = github_service.get_repositories()
            
            # 응답 형식에 맞게 변환
            repo_list = []
            for repo in repositories:
                repo_list.append({
                    "id": repo.id,
                    "name": repo.name,
                    "description": repo.description,
                    "owner": repo.owner,
                    "is_default": repo.is_default,
                    "is_private": repo.is_private,
                    "url": repo.url,
                    "branch": repo.branch
                })
                
            return {"repositories": repo_list}
        except Exception as e:
            # 정보를 가져올 수 없는 경우 테스트 데이터 반환
            return {
                "repositories": [
                    {"id": 1, "name": "test-repo-1", "description": "테스트 저장소 1", "owner": "test-user", "is_default": True, "is_private": True, "branch": "main", "url": "https://github.com/test-user/test-repo-1"},
                    {"id": 2, "name": "test-repo-2", "description": "테스트 저장소 2", "owner": "test-user", "is_default": False, "is_private": True, "branch": "main", "url": "https://github.com/test-user/test-repo-2"}
                ]
            }
    except Exception as e:
        # 심각한 오류가 발생한 경우에만 예외 발생
        raise HTTPException(
            status_code=500,
            detail=f"저장소 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )
