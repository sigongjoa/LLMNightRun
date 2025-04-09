"""
모델 설치 API 모듈

이 모듈은 GitHub 모델 자동 설치 시스템의 API 라우트를 정의합니다.
"""

import os
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Body, Path
from pydantic import BaseModel, Field, HttpUrl

from ..model_installer.controller import ModelInstallerController


# API 라우터 생성
router = APIRouter(
    prefix="/model-installer",
    tags=["model-installer"],
    responses={404: {"description": "Not found"}},
)

# 컨트롤러 인스턴스
MODEL_DIR = os.path.join(os.getcwd(), "models")
os.makedirs(MODEL_DIR, exist_ok=True)
controller = ModelInstallerController(models_base_dir=MODEL_DIR)


# 모델 스키마
class ModelInstallRequest(BaseModel):
    repo_url: HttpUrl = Field(..., description="GitHub 저장소 URL")
    model_name: Optional[str] = Field(None, description="모델 이름 (기본값: 저장소 이름에서 추출)")


class ModelRunRequest(BaseModel):
    model_name: str = Field(..., description="모델 이름")
    script_name: Optional[str] = Field(None, description="실행할 스크립트 이름 (기본값: 통합 런처)")


class ErrorAnalysisRequest(BaseModel):
    error_log: str = Field(..., description="분석할 에러 로그")


class ModelPushRequest(BaseModel):
    model_name: str = Field(..., description="모델 이름")


class ModelUpdateRequest(BaseModel):
    model_name: str = Field(..., description="모델 이름")


# API 라우트
@router.post("/install", response_model=Dict[str, Any])
async def install_model(
    request: ModelInstallRequest,
    background_tasks: BackgroundTasks
):
    """
    GitHub 저장소에서 모델 설치
    
    - **repo_url**: GitHub 저장소 URL
    - **model_name**: 모델 이름 (선택 사항)
    """
    return controller.install_model(str(request.repo_url), request.model_name)


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models():
    """설치된 모델 목록 조회"""
    return controller.list_installed_models()


@router.get("/models/{model_name}", response_model=Dict[str, Any])
async def get_model_info(model_name: str):
    """
    모델 정보 조회
    
    - **model_name**: 모델 이름
    """
    model_info = controller.get_model_info(model_name)
    if not model_info:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    return model_info


@router.post("/run", response_model=Dict[str, Any])
async def run_model(request: ModelRunRequest):
    """
    모델 실행
    
    - **model_name**: 모델 이름
    - **script_name**: 실행할 스크립트 이름 (선택 사항)
    """
    result = controller.run_model(request.model_name, request.script_name)
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/analyze-error", response_model=Dict[str, Any])
async def analyze_error(request: ErrorAnalysisRequest):
    """
    에러 로그 분석
    
    - **error_log**: 분석할 에러 로그
    """
    return controller.analyze_error(request.error_log)


@router.post("/push-to-mcp", response_model=Dict[str, Any])
async def push_to_mcp(request: ModelPushRequest):
    """
    설치된 모델을 MCP 서버에 푸시
    
    - **model_name**: 모델 이름
    """
    result = controller.push_to_mcp(request.model_name)
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/mcp-status/{model_name}", response_model=Dict[str, Any])
async def get_mcp_model_status(model_name: str = Path(..., description="모델 이름")):
    """
    MCP 서버에 업로드된 모델 상태 조회
    
    - **model_name**: 모델 이름
    """
    return controller.get_mcp_model_status(model_name)


@router.post("/update-mcp", response_model=Dict[str, Any])
async def update_mcp_model(request: ModelUpdateRequest):
    """
    MCP 서버에 업로드된 모델 업데이트
    
    - **model_name**: 모델 이름
    """
    result = controller.update_mcp_model(request.model_name)
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    return result
