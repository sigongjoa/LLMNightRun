"""
GitHub API 패키지

GitHub 관련 API 모듈을 제공합니다.
"""

from fastapi import APIRouter
from .test_connection import router as test_connection_router
from .repositories import router as repositories_router
from .upload import router as upload_router
from .generate import router as generate_router
from .repository_operations import router as repository_operations_router

router = APIRouter(
    prefix="/github",
    tags=["github"]
)

# 하위 라우터 등록
router.include_router(test_connection_router, prefix="")
router.include_router(repositories_router, prefix="")
router.include_router(upload_router, prefix="")
router.include_router(generate_router, prefix="")
router.include_router(repository_operations_router, prefix="")
