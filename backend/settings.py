from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import crud
import schemas
from database import get_db
from auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=dict)
def get_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """사용자 설정 정보 조회"""
    try:
        # 여기서는 더미 데이터를 반환하지만, 실제로는 데이터베이스에서 설정을 가져와야 합니다
        return {
            "theme": "light",
            "language": "ko",
            "openai_api_key": "",
            "claude_api_key": "",
            "github_token": "",
            "default_llm": "openai",
            "code_font_size": 14,
            "enable_code_highlighting": True,
            "auto_save": True,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정을 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/", response_model=dict)
def update_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """사용자 설정 정보 업데이트"""
    try:
        # 여기서는 설정 업데이트 로직을 구현해야 하지만, 일단 받은 설정을 그대로 반환합니다
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정을 업데이트하는 중 오류가 발생했습니다: {str(e)}"
        )
