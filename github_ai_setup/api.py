"""
GitHub AI 환경 설정 API 모듈

이 모듈은 GitHub 저장소 분석 및 AI 환경 설정 API 엔드포인트를 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from .analyzer import analyze_repository
from .generator import generate_ai_setup
from .applier import apply_ai_setup

# 로깅 설정
logger = logging.getLogger("github_ai_setup.api")

# 라우터 생성
router = APIRouter(
    prefix="/api/github-ai-setup",
    tags=["GitHub AI Setup"],
    responses={404: {"description": "Not found"}},
)


# 요청 및 응답 모델
class RepositoryData(BaseModel):
    """저장소 데이터 모델"""
    url: str = Field(..., description="GitHub 저장소 URL")
    path: Optional[str] = Field(None, description="로컬 저장소 경로")
    branch: Optional[str] = Field("main", description="브랜치 이름")
    access_token: Optional[str] = Field(None, description="GitHub 액세스 토큰")


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    repo_id: str
    language_stats: Dict[str, float]
    frameworks: List[Dict[str, Any]]
    ai_readiness: float
    suggested_improvements: List[str]
    error: Optional[str] = None


class SetupResponse(BaseModel):
    """설정 응답 모델"""
    repo_id: str
    config_files: List[Dict[str, Any]]
    setup_scripts: List[Dict[str, Any]]
    workflows: List[Dict[str, Any]]
    documentation: Dict[str, Any]
    error: Optional[str] = None


class ApplyResponse(BaseModel):
    """적용 응답 모델"""
    repo_id: str
    status: str
    applied_files: List[str]
    pull_request_url: Optional[str] = None
    error: Optional[str] = None


# API 엔드포인트
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_repo(repo_data: RepositoryData) -> Dict[str, Any]:
    """
    GitHub 저장소 분석
    
    저장소 코드를 분석하여 AI 준비도 및 개선 권장 사항을 반환합니다.
    
    Args:
        repo_data: 저장소 데이터
        
    Returns:
        분석 결과
    """
    try:
        logger.info(f"저장소 분석 요청: {repo_data.url}")
        
        # 저장소 분석 실행
        analysis_result = await analyze_repository(repo_data.dict())
        
        if "error" in analysis_result:
            logger.error(f"저장소 분석 오류: {analysis_result['error']}")
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # 필수 필드만 추출하여 응답
        response = {
            "repo_id": analysis_result["repo_id"],
            "language_stats": analysis_result["language_stats"],
            "frameworks": analysis_result["frameworks"],
            "ai_readiness": analysis_result["ai_readiness"],
            "suggested_improvements": analysis_result["suggested_improvements"]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"저장소 분석 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=SetupResponse)
async def generate_setup(repo_data: RepositoryData) -> Dict[str, Any]:
    """
    AI 환경 설정 생성
    
    저장소를 분석하고 AI 환경 설정 파일을 생성합니다.
    
    Args:
        repo_data: 저장소 데이터
        
    Returns:
        생성된 설정 정보
    """
    try:
        logger.info(f"AI 환경 설정 생성 요청: {repo_data.url}")
        
        # 1. 저장소 분석
        analysis_result = await analyze_repository(repo_data.dict())
        
        if "error" in analysis_result:
            logger.error(f"저장소 분석 오류: {analysis_result['error']}")
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # 2. 설정 생성
        setup_result = await generate_ai_setup(analysis_result["repo_id"], analysis_result)
        
        if "error" in setup_result:
            logger.error(f"설정 생성 오류: {setup_result['error']}")
            raise HTTPException(status_code=500, detail=setup_result["error"])
        
        # 필수 필드만 추출하여 응답
        response = {
            "repo_id": setup_result["repo_id"],
            "config_files": setup_result["config_files"],
            "setup_scripts": setup_result["setup_scripts"],
            "workflows": setup_result["workflows"],
            "documentation": setup_result["documentation"]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"설정 생성 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply", response_model=ApplyResponse)
async def apply_setup(
    repo_data: RepositoryData,
    create_pr: bool = Query(True, description="풀 리퀘스트 생성 여부"),
    pr_title: Optional[str] = Query("AI 환경 설정 추가", description="풀 리퀘스트 제목"),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    AI 환경 설정 적용
    
    생성된 AI 환경 설정을 저장소에 적용합니다.
    
    Args:
        repo_data: 저장소 데이터
        create_pr: 풀 리퀘스트 생성 여부
        pr_title: 풀 리퀘스트 제목
        background_tasks: 백그라운드 작업
        
    Returns:
        적용 결과
    """
    try:
        logger.info(f"AI 환경 설정 적용 요청: {repo_data.url}")
        
        # 1. 저장소 분석
        analysis_result = await analyze_repository(repo_data.dict())
        
        if "error" in analysis_result:
            logger.error(f"저장소 분석 오류: {analysis_result['error']}")
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # 2. 설정 생성
        setup_result = await generate_ai_setup(analysis_result["repo_id"], analysis_result)
        
        if "error" in setup_result:
            logger.error(f"설정 생성 오류: {setup_result['error']}")
            raise HTTPException(status_code=500, detail=setup_result["error"])
        
        # 3. 설정 적용
        apply_params = {
            "repo_data": repo_data.dict(),
            "setup_result": setup_result,
            "create_pr": create_pr,
            "pr_title": pr_title,
            "pr_body": f"AI 환경 설정을 추가합니다.\n\n준비도: {analysis_result['ai_readiness']:.2f}"
        }
        
        # 백그라운드 작업으로 실행 또는 즉시 실행
        if background_tasks:
            # 백그라운드 작업 등록
            result_id = f"apply_{analysis_result['repo_id'].replace('/', '_')}"
            background_tasks.add_task(apply_ai_setup, **apply_params)
            
            # 임시 응답 반환
            return {
                "repo_id": analysis_result["repo_id"],
                "status": "processing",
                "applied_files": [],
                "result_id": result_id,
                "message": "설정 적용이 백그라운드에서 실행 중입니다."
            }
        else:
            # 즉시 실행
            apply_result = await apply_ai_setup(**apply_params)
            
            if "error" in apply_result:
                logger.error(f"설정 적용 오류: {apply_result['error']}")
                raise HTTPException(status_code=500, detail=apply_result["error"])
            
            return apply_result
        
    except Exception as e:
        logger.error(f"설정 적용 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{result_id}", response_model=ApplyResponse)
async def get_apply_status(result_id: str) -> Dict[str, Any]:
    """
    설정 적용 상태 조회
    
    백그라운드로 실행된 설정 적용 작업의 상태를 조회합니다.
    
    Args:
        result_id: 결과 ID
        
    Returns:
        적용 상태
    """
    # 실제 구현에서는 데이터베이스에서 상태 조회
    # 여기서는 샘플 응답 반환
    return {
        "repo_id": result_id.replace("apply_", "").replace("_", "/"),
        "status": "completed",
        "applied_files": [
            ".github/workflows/ai-ci.yml",
            ".github/workflows/model-training.yml",
            ".github/workflows/model-deployment.yml",
            "requirements-ai.txt",
            "scripts/setup_ai_env.py",
            "scripts/download_models.py",
            "docs/ai_integration.md"
        ],
        "pull_request_url": "https://github.com/example/repo/pull/42"
    }
