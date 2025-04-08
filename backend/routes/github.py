from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from backend.database.connection import get_db
from backend.services.github_service import GitHubService


router = APIRouter(
    prefix="/github",
    tags=["github"],
    responses={404: {"description": "리소스를 찾을 수 없음"}},
)


@router.post("/upload")
async def upload_to_github(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    코드 스니펫이나 프로젝트를 GitHub 저장소에 업로드합니다.
    
    Args:
        data: 업로드할 데이터 및 GitHub 저장소 정보
        db: 데이터베이스 세션
        
    Returns:
        업로드 결과 및, 성공 시 GitHub URL
    """
    try:
        # 필수 필드 확인
        if not data.get("content"):
            raise HTTPException(status_code=400, detail="업로드할 내용이 필요합니다")
            
        if not data.get("repo_name"):
            raise HTTPException(status_code=400, detail="GitHub 저장소 이름이 필요합니다")
        
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # GitHub에 업로드
        result = await github_service.upload_to_github(
            content=data.get("content"),
            repo_name=data.get("repo_name"),
            file_path=data.get("file_path"),
            commit_message=data.get("commit_message", "LLMNightRun에서 업로드된 파일"),
            is_private=data.get("is_private", True),
            branch=data.get("branch", "main")
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub 업로드 오류: {str(e)}")


@router.get("/repositories")
async def list_repositories(
    db: Session = Depends(get_db)
):
    """
    사용자의 GitHub 저장소 목록을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        사용자 GitHub 저장소 목록
    """
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 목록 조회
        repositories = await github_service.list_repositories()
        
        return {"repositories": repositories}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub 저장소 목록 조회 오류: {str(e)}")


@router.post("/create-repository")
async def create_repository(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    새 GitHub 저장소를 생성합니다.
    
    Args:
        data: 저장소 정보 (이름, 설명, 공개 여부 등)
        db: 데이터베이스 세션
        
    Returns:
        생성된 저장소 정보
    """
    try:
        # 필수 필드 확인
        if not data.get("name"):
            raise HTTPException(status_code=400, detail="저장소 이름이 필요합니다")
        
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 저장소 생성
        result = await github_service.create_repository(
            name=data.get("name"),
            description=data.get("description", ""),
            private=data.get("private", True),
            auto_init=data.get("auto_init", True)
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub 저장소 생성 오류: {str(e)}")


@router.post("/generate-docs")
async def generate_documentation(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    코드 기반으로 문서를 생성하고 GitHub에 업로드합니다.
    
    Args:
        data: 문서 생성 대상 (코드, 저장소 등) 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 문서 정보 및 GitHub URL
    """
    try:
        # 필수 필드 확인
        if not (data.get("code") or data.get("snippet_id") or data.get("repo_url")):
            raise HTTPException(
                status_code=400, 
                detail="문서 생성을 위한 코드, 스니펫 ID 또는 저장소 URL이 필요합니다"
            )
        
        # GitHub 서비스 초기화
        github_service = GitHubService(db)
        
        # 문서 생성 및 업로드
        result = await github_service.generate_documentation(
            code=data.get("code"),
            snippet_id=data.get("snippet_id"),
            repo_url=data.get("repo_url"),
            doc_format=data.get("doc_format", "markdown"),
            include_examples=data.get("include_examples", True),
            upload_to_github=data.get("upload_to_github", False),
            repo_name=data.get("repo_name"),
            file_path=data.get("file_path", "docs/README.md")
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 생성 오류: {str(e)}")
