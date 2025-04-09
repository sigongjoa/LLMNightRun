"""
A/B 테스트 라우터 모듈

모든 A/B 테스트 관련 라우터를 내보냅니다.
"""

from fastapi import APIRouter

from backend.ab_testing.routes.templates import router as templates_router
from backend.ab_testing.routes.optimization import router as optimization_router
from backend.ab_testing.routes.multi_language import router as multi_language_router
from backend.ab_testing.routes.batch_jobs import router as batch_jobs_router
from backend.ab_testing.routes.code_export import router as code_export_router

# 메인 라우터 생성
router = APIRouter(
    prefix="/ab-testing",
    tags=["AB Testing"]
)

# 서브 라우터 포함
router.include_router(templates_router)
router.include_router(optimization_router)
router.include_router(multi_language_router)
router.include_router(batch_jobs_router)
router.include_router(code_export_router)
