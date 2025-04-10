import os
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union

from backend.database.connection import get_db
from backend.services.github_service import GitHubService
from backend.models.github_config import GitHubRepositoryCreate, GitHubRepositoryUpdate


# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["github"],
    responses={404: {"description": "리소스를 찾을 수 없음"}},
)


# API 모델
class QuestionUploadRequest(BaseModel):
    question_id: int
    folder_path: Optional[str] = None
    repo_id: Optional[int] = None


class ContentUploadRequest(BaseModel):
    content: str
    file_path: str
    commit_message: Optional[str] = None
    repo_id: Optional[int] = None
    branch: Optional[str] = None


class CommitMessageGenerateRequest(BaseModel):
    question_id: int
    repo_id: Optional[int] = None


class ReadmeGenerateRequest(BaseModel):
    question_id: int
    repo_id: Optional[int] = None


class GitHubRepositoryRequest(BaseModel):
    name: str
    owner: str
    token: str
    description: Optional[str] = None
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    project_id: Optional[int] = None


@router.post("/upload")
async def upload_to_github(
    request: QuestionUploadRequest,
    db: Session = Depends(get_db)
):
    """
    질문에 연결된 코드 스니펫을 GitHub 저장소에 업로드합니다.
    
    Args:
        request: 업로드 요청 정보 (질문 ID, 폴더 경로 등)
        db: 데이터베이스 세션
        
    Returns:
        업로드 결과 및 GitHub URL
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # GitHub에 업로드
        result = await github_service.upload_to_github(
            question_id=request.question_id,
            folder_path=request.folder_path,
            repo_id=request.repo_id
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub 업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub 업로드 오류: {str(e)}")


@router.post("/upload-file")
async def upload_file_to_github(
    request: ContentUploadRequest,
    db: Session = Depends(get_db)
):
    """
    단일 파일을 GitHub 저장소에 업로드합니다.
    
    Args:
        request: 업로드 요청 정보 (파일 내용, 경로 등)
        db: 데이터베이스 세션
        
    Returns:
        업로드 결과 및 GitHub URL
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 파일 업로드
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
        logger.error(f"GitHub 파일 업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub 파일 업로드 오류: {str(e)}")


@router.get("/generate-commit-message/{question_id}")
async def generate_commit_message(
    question_id: int,
    repo_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    질문과 코드 스니펫을 기반으로 커밋 메시지를 생성합니다.
    
    Args:
        question_id: 질문 ID
        repo_id: 저장소 ID (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        생성된 커밋 메시지
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 커밋 메시지 생성
        commit_message = await github_service.generate_commit_message(question_id, repo_id)
        
        return {"commit_message": commit_message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커밋 메시지 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"커밋 메시지 생성 오류: {str(e)}")


@router.get("/generate-readme/{question_id}")
async def generate_readme(
    question_id: int,
    repo_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    질문과 코드 스니펫을 기반으로 README 파일을 생성합니다.
    
    Args:
        question_id: 질문 ID
        repo_id: 저장소 ID (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        생성된 README 내용
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # README 생성
        readme_content = await github_service.generate_readme(question_id, repo_id)
        
        return {"readme_content": readme_content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"README 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"README 생성 오류: {str(e)}")


# 저장소 관리 엔드포인트
@router.get("/repositories")
async def list_repositories(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    GitHub 저장소 목록을 조회합니다.
    
    Args:
        project_id: 프로젝트 ID (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        저장소 목록
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 목록 가져오기
        repositories = github_service.get_repositories(project_id)
        
        return {"repositories": repositories}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장소 목록 조회 오류: {str(e)}")


@router.post("/repositories", status_code=201)
async def create_repository(
    repository: GitHubRepositoryCreate,
    db: Session = Depends(get_db)
):
    """
    새 GitHub 저장소 정보를 추가합니다.
    
    Args:
        repository: 저장소 생성 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 저장소 정보
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 생성
        from backend.services.github.models import GitHubRepositoryData
        
        repo_data = GitHubRepositoryData(
            name=repository.name,
            description=repository.description,
            owner=repository.owner, 
            token=repository.token,
            is_default=repository.is_default,
            is_private=repository.is_private,
            branch=repository.branch,
            project_id=repository.project_id
        )
        
        created_repo = github_service.create_repository(repo_data)
        
        return created_repo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장소 생성 오류: {str(e)}")


@router.get("/repositories/{repo_id}")
async def get_repository(
    repo_id: int,
    db: Session = Depends(get_db)
):
    """
    GitHub 저장소 정보를 조회합니다.
    
    Args:
        repo_id: 저장소 ID
        db: 데이터베이스 세션
        
    Returns:
        저장소 정보
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 정보 가져오기
        repository = github_service._get_repository(repo_id)
        
        # 보안을 위해 토큰 정보 제외
        repository_dict = {
            "id": repository.id,
            "name": repository.name,
            "description": repository.description,
            "owner": repository.owner,
            "url": repository.url,
            "is_default": repository.is_default,
            "is_private": repository.is_private,
            "branch": repository.branch,
            "project_id": repository.project_id
        }
        
        return repository_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장소 조회 오류: {str(e)}")


@router.put("/repositories/{repo_id}")
async def update_repository(
    repo_id: int,
    repository: GitHubRepositoryUpdate,
    db: Session = Depends(get_db)
):
    """
    GitHub 저장소 정보를 업데이트합니다.
    
    Args:
        repo_id: 저장소 ID
        repository: 업데이트할 저장소 정보
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 저장소 정보
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 정보 업데이트
        updated_repo = github_service.update_repository(repo_id, repository.dict(exclude_unset=True))
        
        # 보안을 위해 토큰 정보 제외
        repository_dict = {
            "id": updated_repo.id,
            "name": updated_repo.name,
            "description": updated_repo.description,
            "owner": updated_repo.owner,
            "url": updated_repo.url,
            "is_default": updated_repo.is_default,
            "is_private": updated_repo.is_private,
            "branch": updated_repo.branch,
            "project_id": updated_repo.project_id
        }
        
        return repository_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장소 업데이트 오류: {str(e)}")


@router.delete("/repositories/{repo_id}")
async def delete_repository(
    repo_id: int,
    db: Session = Depends(get_db)
):
    """
    GitHub 저장소 정보를 삭제합니다.
    
    Args:
        repo_id: 저장소 ID
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 삭제
        result = github_service.delete_repository(repo_id)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"저장소 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"저장소 삭제 오류: {str(e)}")


@router.get("/remote-repositories")
async def list_remote_repositories(
    repo_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    GitHub 원격 저장소 목록을 가져옵니다.
    
    Args:
        repo_id: 저장소 ID (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        원격 저장소 목록
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 원격 저장소 목록 가져오기
        repositories = await github_service.list_remote_repositories(repo_id)
        
        return {"repositories": repositories}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"원격 저장소 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"원격 저장소 목록 조회 오류: {str(e)}")


@router.post("/remote-repositories")
async def create_remote_repository(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    GitHub에 새 원격 저장소를 생성합니다.
    
    Args:
        data: 저장소 생성 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 저장소 정보
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 원격 저장소 생성
        result = await github_service.create_remote_repository(
            name=data.get("name"),
            description=data.get("description", ""),
            private=data.get("private", True),
            auto_init=data.get("auto_init", True),
            repo_id=data.get("repo_id")
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"원격 저장소 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"원격 저장소 생성 오류: {str(e)}")
