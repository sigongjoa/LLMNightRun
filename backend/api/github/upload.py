"""
GitHub 코드 업로드 API 모듈

코드 업로드 관련 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ...database.connection import get_db

# 라우터 정의
router = APIRouter(
    prefix="/upload",
    tags=["github"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=Dict[str, Any])
async def upload_to_github(
    question_id: int = Query(..., description="질문 ID"),
    folder_path: Optional[str] = Query(None, description="폴더 경로"),
    repo_id: Optional[int] = Query(None, description="저장소 ID"),
    db: Session = Depends(get_db)
):
    """
    코드를 GitHub에 업로드합니다. (스텁 구현)
    """
    return {
        "success": True,
        "message": "GitHub 업로드가 성공적으로 시뮬레이션되었습니다.",
        "repo_url": f"https://github.com/test-user/test-repo/tree/main/{folder_path or f'question_{question_id}'}",
        "folder_path": folder_path or f"question_{question_id}",
        "commit_message": f"Add code for question #{question_id}",
        "files": [
            "main.py",
            "util.py",
            "README.md"
        ]
    }


@router.post("/file", response_model=Dict[str, Any])
async def upload_file_to_github(
    content: str = Body(..., description="파일 내용"),
    file_path: str = Body(..., description="파일 경로"),
    commit_message: Optional[str] = Body(None, description="커밋 메시지"),
    repo_id: Optional[int] = Body(None, description="저장소 ID"),
    branch: Optional[str] = Body(None, description="브랜치"),
    db: Session = Depends(get_db)
):
    """
    단일 파일을 GitHub에 업로드합니다. (스텁 구현)
    """
    return {
        "success": True,
        "message": "GitHub 파일 업로드가 성공적으로 시뮬레이션되었습니다.",
        "repo_url": "https://github.com/test-user/test-repo",
        "file_path": file_path,
        "commit_message": commit_message or f"Add file {file_path}",
        "branch": branch or "main"
    }
