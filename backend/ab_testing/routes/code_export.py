"""
A/B 테스트 코드 내보내기 라우터

코드 내보내기 관련 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from backend.database.connection import get_db
from backend.logger import get_logger
from backend.ab_testing import schemas
from backend.ab_testing import controllers

# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/code-export",
    tags=["AB Testing Code Export"]
)


@router.get("/experiment-sets/{set_id}", response_model=schemas.CodeExportResponse)
async def export_code(
    set_id: int = Path(..., title="실험 세트 ID"),
    language: str = Query("python", title="프로그래밍 언어", regex="^(python|javascript|typescript)$"),
    experiment_id: Optional[int] = Query(None, title="특정 실험 ID (없으면 전체)"),
    db: Session = Depends(get_db)
):
    """실험 세트를 코드로 내보내기"""
    logger.info(f"코드 내보내기: set_id={set_id}, language={language}")
    code_export = await controllers.export_code(db, set_id, language, experiment_id)
    if not code_export:
        raise HTTPException(status_code=404, detail=f"ID {set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
    return code_export
