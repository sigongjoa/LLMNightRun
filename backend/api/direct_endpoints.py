"""
직접 API 엔드포인트 모듈

개발 및 디버깅을 위한 직접 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Path, Body
from typing import List, Dict, Any, Optional

# 직접 엔드포인트 라우터
router = APIRouter(
    prefix="",  # 전역 엔드포인트 제공
    tags=["direct"],
    responses={404: {"description": "Not found"}},
)

@router.get("/settings")
@router.post("/settings")
async def settings_endpoint():
    """
    설정 직접 엔드포인트 - 디버그용
    """
    return {
        "id": 1,
        "openai_api_key": "test-key",
        "claude_api_key": "test-key",
        "github_token": "test-token",
        "github_repo": "LLMNightRUN_test1",
        "github_username": "sigongjoa"
    }

@router.get("/github/repositories")
async def direct_github_repositories():
    """
    GitHub 저장소 목록 직접 엔드포인트 - 디버그용
    """
    return {
        "repositories": [
            {"id": 1, "name": "LLMNightRUN_test1", "description": "LLM Night Run 테스트 저장소", "owner": "sigongjoa", "is_default": True, "is_private": True, "branch": "main"}
        ]
    }

@router.delete("/github/repositories/{repo_id}")
async def direct_delete_github_repository(repo_id: int = Path(..., description="저장소 ID")):
    """
    GitHub 저장소 삭제 직접 엔드포인트 - 디버그용
    """
    return {
        "message": f"저장소 ID {repo_id}가 삭제되었습니다."
    }

@router.get("/github/generate-commit-message/{question_id}")
async def direct_generate_commit_message(
    question_id: int = Path(..., description="질문 ID"),
    repo_id: Optional[int] = None
):
    """
    GitHub 커밋 메시지 생성 직접 엔드포인트 - 디버그용
    
    실제 백엔드 엔드포인트로 리디렉션 (github-repos/commit-message/...)
    """
    return {
        "commit_message": f"feat: Add solution for question #{question_id}"
    }

@router.get("/github/generate-readme/{question_id}")
async def direct_generate_readme(
    question_id: int = Path(..., description="질문 ID"),
    repo_id: Optional[int] = None
):
    """
    GitHub README 생성 직접 엔드포인트 - 디버그용
    
    실제 백엔드 엔드포인트로 리디렉션 (github-repos/readme/...)
    """
    return {
        "readme_content": f"# Question {question_id}\n\n## 문제 설명\n\n이 저장소는 질문 #{question_id}에 대한 해결책을 담고 있습니다.\n\n## 구현 내용\n\n- 주요 기능 구현\n- 테스트 코드 작성\n\n## 사용 방법\n\n```\n# 코드 실행 예시\npython main.py\n```"
    }

@router.post("/github/upload")
async def direct_upload_to_github(request: Dict[str, Any] = Body(...)):
    """
    GitHub 업로드 직접 엔드포인트 - 디버그용
    """
    question_id = request.get('question_id', 0)
    folder_path = request.get('folder_path', f"question_{question_id}")
    
    # 설정과 일관된 저장소 정보 사용
    username = "sigongjoa"
    repo_name = "LLMNightRUN_test1"
    
    return {
        "success": True,
        "message": "GitHub 업로드가 성공적으로 시뮬레이션되었습니다.",
        "repo_url": f"https://github.com/{username}/{repo_name}/tree/main/{folder_path}",
        "folder_path": folder_path,
        "commit_message": f"feat: Add solution for question #{question_id}",
        "files": [
            "main.py",
            "util.py",
            "README.md"
        ]
    }
