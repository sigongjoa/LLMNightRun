
"""
테스트 라우터 모듈

API 엔드포인트 테스트용 라우터
"""

from fastapi import APIRouter, HTTPException

# 라우터 정의
router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """
    테스트 엔드포인트
    """
    return {"status": "ok", "message": "테스트 엔드포인트가 정상 작동합니다."}

@router.get("/github/repositories")
async def test_github_repositories():
    """
    GitHub 저장소 테스트 엔드포인트
    """
    return {
        "repositories": [
            {"id": 1, "name": "test-repo-1", "description": "테스트 저장소 1"},
            {"id": 2, "name": "test-repo-2", "description": "테스트 저장소 2"}
        ]
    }

@router.get("/settings/")
async def test_settings_with_slash():
    """
    설정 테스트 엔드포인트 (슬래시 포함)
    """
    return {
        "id": 1,
        "openai_api_key": "test-key",
        "claude_api_key": "test-key",
        "github_token": "test-token",
        "github_repo": "test-repo",
        "github_username": "test-user"
    }
