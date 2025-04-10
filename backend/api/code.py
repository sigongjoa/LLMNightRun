"""
코드 API 라우터 모듈 (스니펫 기능 비활성화)

코드 관련 엔드포인트를 정의합니다. 코드 스니펫 기능은 비활성화되었습니다.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..database.connection import get_db

# 로거 설정
logger = logging.getLogger(__name__)

# 코드 스니펫 라우터 생성
router = APIRouter(
    prefix="/code-snippets",
    tags=["code"],
    responses={404: {"description": "찾을 수 없음"}},
)

# 코드 템플릿 라우터 생성
template_router = APIRouter(
    prefix="/code-templates",
    tags=["code"],
    responses={404: {"description": "찾을 수 없음"}},
)

# 메인 라우터에 템플릿 라우터 포함
router.include_router(template_router)


# 스니펫 기능 비활성화 메시지
@router.get("/", response_model=Dict[str, Any])
async def list_snippets():
    """
    코드 스니펫 목록을 조회합니다. (비활성화)
    """
    return {
        "message": "코드 스니펫 기능이 비활성화되었습니다.",
        "data": []
    }


@router.post("/", response_model=Dict[str, Any])
async def create_snippet():
    """
    새로운 코드 스니펫을 생성합니다. (비활성화)
    """
    return {
        "message": "코드 스니펫 기능이 비활성화되었습니다."
    }


@router.get("/{snippet_id}", response_model=Dict[str, Any])
async def get_snippet(snippet_id: int):
    """
    특정 코드 스니펫을 조회합니다. (비활성화)
    """
    return {
        "message": "코드 스니펫 기능이 비활성화되었습니다."
    }


@router.put("/{snippet_id}", response_model=Dict[str, Any])
async def update_snippet(snippet_id: int):
    """
    코드 스니펫을 업데이트합니다. (비활성화)
    """
    return {
        "message": "코드 스니펫 기능이 비활성화되었습니다."
    }


@router.delete("/{snippet_id}", response_model=Dict[str, Any])
async def delete_snippet(snippet_id: int):
    """
    코드 스니펫을 삭제합니다. (비활성화)
    """
    return {
        "message": "코드 스니펫 기능이 비활성화되었습니다."
    }


# 템플릿 기능 비활성화 메시지
@template_router.get("/", response_model=Dict[str, Any])
async def list_templates():
    """
    코드 템플릿 목록을 조회합니다. (비활성화)
    """
    return {
        "message": "코드 템플릿 기능이 비활성화되었습니다.",
        "data": []
    }


@template_router.post("/", response_model=Dict[str, Any])
async def create_template():
    """
    새로운 코드 템플릿을 생성합니다. (비활성화)
    """
    return {
        "message": "코드 템플릿 기능이 비활성화되었습니다."
    }


@template_router.get("/{template_id}", response_model=Dict[str, Any])
async def get_template(template_id: int):
    """
    특정 코드 템플릿을 조회합니다. (비활성화)
    """
    return {
        "message": "코드 템플릿 기능이 비활성화되었습니다."
    }


@template_router.put("/{template_id}", response_model=Dict[str, Any])
async def update_template(template_id: int):
    """
    코드 템플릿을 업데이트합니다. (비활성화)
    """
    return {
        "message": "코드 템플릿 기능이 비활성화되었습니다."
    }


@template_router.delete("/{template_id}", response_model=Dict[str, Any])
async def delete_template(template_id: int):
    """
    코드 템플릿을 삭제합니다. (비활성화)
    """
    return {
        "message": "코드 템플릿 기능이 비활성화되었습니다."
    }
