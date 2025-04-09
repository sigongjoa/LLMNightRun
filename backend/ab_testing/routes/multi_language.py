"""
A/B 테스트 다국어 테스트 라우터

다국어 테스트 관련 API 엔드포인트를 구현합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from backend.database.connection import get_db
from backend.logger import get_logger
from backend.ab_testing import schemas
from backend.ab_testing import controllers

# 로거 설정
logger = get_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/multi-language",
    tags=["AB Testing Multi-Language"]
)


@router.post("/experiment-sets/{set_id}/test", response_model=dict)
async def run_multi_language_test(
    set_id: int,
    multi_language_config: schemas.MultiLanguageTest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """다국어 테스트 실행"""
    logger.info(f"다국어 테스트 실행: set_id={set_id}, languages={multi_language_config.languages}")
    
    test_id = str(uuid.uuid4())
    background_tasks.add_task(
        controllers.run_multi_language_test_background,
        db, set_id, multi_language_config, test_id
    )
    
    return {
        "experiment_set_id": set_id,
        "test_id": test_id,
        "status": "started",
        "message": f"다국어 테스트가 시작되었습니다 (언어: {', '.join(multi_language_config.languages)})",
        "started_at": datetime.utcnow()
    }


@router.get("/experiment-sets/{set_id}/results/{test_id}", response_model=dict)
async def get_multi_language_test_results(
    set_id: int,
    test_id: str,
    db: Session = Depends(get_db)
):
    """다국어 테스트 결과 조회"""
    logger.info(f"다국어 테스트 결과 조회: set_id={set_id}, test_id={test_id}")
    result = await controllers.get_multi_language_test_results(db, set_id, test_id)
    if not result:
        raise HTTPException(status_code=404, detail="해당하는 다국어 테스트 결과를 찾을 수 없습니다")
    return result
