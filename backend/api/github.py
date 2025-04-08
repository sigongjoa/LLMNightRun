"""
GitHub 연동 API 모듈

이 모듈은 GitHub 연동 관련 API 엔드포인트를 제공합니다.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query
from fastapi.responses import JSONResponse

from ..models.github_config import (
    GitHubConfig, GitHubConfigUpdateRequest, 
    GitHubTestConnectionRequest, GitHubTestConnectionResponse,
    GitHubCommit
)
from ..services.github_service import GitHubService

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    prefix="/github",
    tags=["github"],
    responses={404: {"description": "Not found"}},
)


# GitHub 서비스 의존성
def get_github_service():
    return GitHubService()


@router.get("/config", response_model=GitHubConfig)
async def get_github_config(
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 설정 조회
    """
    try:
        config = github_service.get_config()
        # API 응답에서 토큰 일부를 마스킹 처리
        if config.token:
            config.token = config.token[:4] + "***" + config.token[-4:]
        return config
    
    except Exception as e:
        logger.error(f"GitHub 설정 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/config", response_model=GitHubConfig)
async def update_github_config(
    request: GitHubConfigUpdateRequest = Body(...),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 설정 업데이트
    """
    try:
        # 업데이트 대상 필드만 추출
        update_data = request.dict(exclude_unset=True)
        
        # 설정 업데이트
        updated_config = github_service.update_config(update_data)
        
        # API 응답에서 토큰 일부를 마스킹 처리
        if updated_config.token:
            updated_config.token = updated_config.token[:4] + "***" + updated_config.token[-4:]
        
        return updated_config
    
    except Exception as e:
        logger.error(f"GitHub 설정 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 설정 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/test-connection", response_model=GitHubTestConnectionResponse)
async def test_github_connection(
    request: GitHubTestConnectionRequest = Body(...),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 연결 테스트
    """
    try:
        # 연결 테스트
        result = github_service.test_connection(
            repo_url=request.repo_url,
            token=request.token,
            username=request.username
        )
        
        return result
    
    except Exception as e:
        logger.error(f"GitHub 연결 테스트 중 오류 발생: {str(e)}")
        return GitHubTestConnectionResponse(
            success=False,
            message="GitHub 연결 테스트 실패",
            error=str(e)
        )


@router.get("/commits", response_model=List[GitHubCommit])
async def list_github_commits(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=50, description="페이지 크기"),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 커밋 이력 조회
    """
    try:
        # GitHub 설정 확인
        if not github_service.is_github_configured():
            raise HTTPException(
                status_code=400,
                detail="GitHub 설정이 구성되지 않았습니다. 먼저 GitHub 설정을 구성해주세요."
            )
        
        # 커밋 이력 조회
        commits = github_service.list_commits(page=page, page_size=page_size)
        return commits
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"GitHub 커밋 이력 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 커밋 이력 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/commits/{commit_id}", response_model=GitHubCommit)
async def get_github_commit(
    commit_id: str = Path(..., description="커밋 ID"),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    특정 GitHub 커밋 조회
    """
    try:
        # GitHub 설정 확인
        if not github_service.is_github_configured():
            raise HTTPException(
                status_code=400,
                detail="GitHub 설정이 구성되지 않았습니다. 먼저 GitHub 설정을 구성해주세요."
            )
        
        # 커밋 조회
        commit = github_service.get_commit(commit_id)
        if not commit:
            raise HTTPException(
                status_code=404,
                detail=f"ID가 {commit_id}인 커밋을 찾을 수 없습니다."
            )
        
        return commit
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"GitHub 커밋 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 커밋 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sync", response_model=Dict[str, Any])
async def sync_with_github(
    github_service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 저장소와 동기화
    """
    try:
        # GitHub 설정 확인
        if not github_service.is_github_configured():
            raise HTTPException(
                status_code=400,
                detail="GitHub 설정이 구성되지 않았습니다. 먼저 GitHub 설정을 구성해주세요."
            )
        
        # 동기화 실행
        result = github_service.sync_with_github()
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"GitHub 동기화 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/generate-commit-message", response_model=Dict[str, str])
async def generate_commit_message(
    document_ids: List[str] = Body(..., embed=True),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    LLM을 사용하여 커밋 메시지 생성
    """
    try:
        # GitHub 설정 확인
        if not github_service.is_github_configured():
            raise HTTPException(
                status_code=400,
                detail="GitHub 설정이 구성되지 않았습니다. 먼저 GitHub 설정을 구성해주세요."
            )
        
        # 메시지 생성
        message = github_service.generate_commit_message(document_ids)
        return {"message": message}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"커밋 메시지 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"커밋 메시지 생성 중 오류가 발생했습니다: {str(e)}"
        )
