"""
GitHub 저장소 관리 API 모듈

이 모듈은 GitHub 저장소 관리 관련 API 엔드포인트를 제공합니다.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database.connection import get_db
from ..services.github_service import GitHubService
from ..services.github.models import GitHubRepositoryData


# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    prefix="/github-repos",
    tags=["github-repos"],
    responses={404: {"description": "Not found"}},
)


# 응답 모델 정의
class GitHubRepositoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner: str
    url: str
    is_default: bool
    is_private: bool
    branch: Optional[str] = None
    project_id: Optional[int] = None


class GitHubCreateRepositoryRequest(BaseModel):
    name: str
    description: Optional[str] = None
    owner: str
    token: str
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    project_id: Optional[int] = None


class GitHubUpdateRepositoryRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    token: Optional[str] = None
    is_default: Optional[bool] = None
    is_private: Optional[bool] = None
    branch: Optional[str] = None
    project_id: Optional[int] = None


class GitHubUploadRequest(BaseModel):
    question_id: int
    folder_path: Optional[str] = None
    repo_id: Optional[int] = None


class GitHubFileUploadRequest(BaseModel):
    content: str
    file_path: str
    commit_message: Optional[str] = None
    repo_id: Optional[int] = None
    branch: Optional[str] = None


class GitHubCreateRemoteRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = True
    auto_init: bool = True
    repo_id: Optional[int] = None


# GitHub 서비스 의존성
def get_github_service(db: Session = Depends(get_db)):
    return GitHubService(db)


@router.get("/", response_model=List[GitHubRepositoryResponse])
async def list_repositories(
    project_id: Optional[int] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소 목록 조회
    
    Args:
        project_id: 프로젝트 ID (선택 사항)
    """
    try:
        repositories = github_service.get_repositories(project_id)
        return repositories
    except Exception as e:
        logger.error(f"저장소 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"저장소 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/", response_model=GitHubRepositoryResponse, status_code=201)
async def create_repository(
    request: GitHubCreateRepositoryRequest,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소 정보 생성
    """
    try:
        repo_data = GitHubRepositoryData(**request.dict())
        repository = github_service.create_repository(repo_data)
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"저장소 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{repo_id}", response_model=GitHubRepositoryResponse)
async def get_repository(
    repo_id: int = Path(..., description="저장소 ID"),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소 정보 조회
    """
    try:
        repository = github_service._get_repository(repo_id)
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"저장소 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{repo_id}", response_model=GitHubRepositoryResponse)
async def update_repository(
    repo_id: int = Path(..., description="저장소 ID"),
    request: GitHubUpdateRepositoryRequest = Body(...),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소 정보 업데이트
    """
    try:
        update_data = request.dict(exclude_unset=True)
        repository = github_service.update_repository(repo_id, update_data)
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"저장소 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{repo_id}", response_model=Dict[str, Any])
async def delete_repository(
    repo_id: int = Path(..., description="저장소 ID"),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소 정보 삭제
    """
    try:
        result = github_service.delete_repository(repo_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"저장소 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/upload", response_model=Dict[str, Any])
async def upload_to_github(
    request: GitHubUploadRequest,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    코드 스니펫을 GitHub에 업로드
    """
    try:
        result = await github_service.upload_to_github(
            question_id=request.question_id,
            folder_path=request.folder_path,
            repo_id=request.repo_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/upload-file", response_model=Dict[str, Any])
async def upload_file_to_github(
    request: GitHubFileUploadRequest,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    단일 파일을 GitHub에 업로드
    """
    try:
        result = await github_service.upload_file_to_github(
            content=request.content,
            file_path=request.file_path,
            commit_message=request.commit_message,
            repo_id=request.repo_id,
            branch=request.branch
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub 파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/commit-message/{question_id}", response_model=Dict[str, str])
async def generate_commit_message(
    question_id: int,
    repo_id: Optional[int] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 커밋 메시지 생성
    """
    try:
        message = await github_service.generate_commit_message(question_id, repo_id)
        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커밋 메시지 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"커밋 메시지 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/readme/{question_id}", response_model=Dict[str, str])
async def generate_readme(
    question_id: int,
    repo_id: Optional[int] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub README 파일 생성
    """
    try:
        content = await github_service.generate_readme(question_id, repo_id)
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"README 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"README 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/remote", response_model=List[Dict[str, Any]])
async def list_remote_repositories(
    repo_id: Optional[int] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    사용자의 GitHub 원격 저장소 목록 조회
    """
    try:
        repositories = await github_service.list_remote_repositories(repo_id)
        return repositories
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"원격 저장소 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"원격 저장소 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/remote", response_model=Dict[str, Any])
async def create_remote_repository(
    request: GitHubCreateRemoteRequest,
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 원격 저장소 생성
    """
    try:
        result = await github_service.create_remote_repository(
            name=request.name,
            description=request.description,
            private=request.private,
            auto_init=request.auto_init,
            repo_id=request.repo_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"원격 저장소 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"원격 저장소 생성 중 오류가 발생했습니다: {str(e)}"
        )
