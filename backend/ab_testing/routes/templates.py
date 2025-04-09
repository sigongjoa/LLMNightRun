"""
A/B 테스트 템플릿 라우터

실험 템플릿 관련 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.database.connection import get_db
from backend.logger import get_logger
from backend.ab_testing import schemas
from backend.ab_testing import controllers

# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/templates",
    tags=["AB Testing Templates"]
)


@router.post("/", response_model=schemas.ExperimentTemplateDB)
async def create_template(
    template: schemas.ExperimentTemplate,
    db: Session = Depends(get_db)
):
    """새 실험 템플릿 생성"""
    logger.info(f"템플릿 생성 요청: {template.name}")
    return await controllers.create_template(db, template)


@router.get("/", response_model=schemas.TemplateListResponse)
async def get_templates(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """템플릿 목록 조회"""
    logger.info(f"템플릿 목록 조회: skip={skip}, limit={limit}")
    templates = await controllers.get_templates(db, skip, limit, search, tag)
    return {
        "total": len(templates),
        "templates": templates
    }


@router.get("/{template_id}", response_model=schemas.ExperimentTemplateDB)
async def get_template(
    template_id: int = Path(..., title="템플릿 ID"),
    db: Session = Depends(get_db)
):
    """템플릿 상세 조회"""
    logger.info(f"템플릿 상세 조회: id={template_id}")
    template = await controllers.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"ID {template_id}에 해당하는 템플릿을 찾을 수 없습니다")
    return template


@router.put("/{template_id}", response_model=schemas.ExperimentTemplateDB)
async def update_template(
    template_id: int = Path(..., title="템플릿 ID"),
    template: schemas.ExperimentTemplate = None,
    db: Session = Depends(get_db)
):
    """템플릿 업데이트"""
    logger.info(f"템플릿 업데이트: id={template_id}")
    updated_template = await controllers.update_template(db, template_id, template)
    if not updated_template:
        raise HTTPException(status_code=404, detail=f"ID {template_id}에 해당하는 템플릿을 찾을 수 없습니다")
    return updated_template


@router.delete("/{template_id}", response_model=schemas.DeleteResponse)
async def delete_template(
    template_id: int = Path(..., title="템플릿 ID"),
    db: Session = Depends(get_db)
):
    """템플릿 삭제"""
    logger.info(f"템플릿 삭제: id={template_id}")
    result = await controllers.delete_template(db, template_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/{template_id}/create-experiment-set", response_model=schemas.ExperimentSetDB)
async def create_experiment_set_from_template(
    template_id: int = Path(..., title="템플릿 ID"),
    params: Dict[str, Any] = Body(..., title="템플릿 파라미터"),
    db: Session = Depends(get_db)
):
    """템플릿으로부터 실험 세트 생성"""
    logger.info(f"템플릿으로부터 실험 세트 생성: template_id={template_id}")
    return await controllers.create_experiment_set_from_template(db, template_id, params)
