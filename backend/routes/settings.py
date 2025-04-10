"""
설정 관리 API 모듈

이 모듈은, API 키, GitHub 설정, 웹 크롤링 설정 등
애플리케이션 설정을 관리하는 API 엔드포인트를 제공합니다.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.database.connection import get_db
from backend.database.models import Settings
from pydantic import BaseModel

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

# 응답 및 요청 모델
class SettingsModel(BaseModel):
    id: Optional[int] = None
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    github_username: Optional[str] = None

# 설정 가져오기 함수
def get_current_settings(db: Session):
    """현재 설정을 데이터베이스에서 가져옵니다. 없으면 기본 설정을 생성합니다."""
    settings = db.query(Settings).first()
    
    # 설정이 없으면 기본 설정 생성
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

@router.get("/", response_model=SettingsModel)
async def get_settings(db: Session = Depends(get_db)):
    """
    현재 설정을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        현재 설정
    """
    try:
        settings = get_current_settings(db)
        return settings
    except Exception as e:
        logger.error(f"설정 가져오기 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"설정을 가져오는 중 오류가 발생했습니다: {str(e)}")

@router.post("/", response_model=SettingsModel)
async def update_settings(
    settings_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    설정을 업데이트합니다.
    
    Args:
        settings_data: 업데이트할 설정 데이터
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 설정
    """
    try:
        # 현재 설정 가져오기
        settings = get_current_settings(db)
        
        # 제공된 데이터로 설정 업데이트
        for key, value in settings_data.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)
        
        # 변경사항 저장
        db.commit()
        db.refresh(settings)
        
        return settings
    except Exception as e:
        db.rollback()
        logger.error(f"설정 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"설정을 업데이트하는 중 오류가 발생했습니다: {str(e)}")

@router.post("/test-connection")
async def test_connection(
    connection_type: str,
    connection_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    API 연결을 테스트합니다.
    
    Args:
        connection_type: 연결 유형 (예: "openai", "claude", "github")
        connection_data: 연결 테스트에 사용할 데이터
        db: 데이터베이스 세션
        
    Returns:
        연결 테스트 결과
    """
    try:
        # 연결 유형에 따라 다른 로직 수행
        if connection_type == "openai":
            # OpenAI API 연결 테스트
            api_key = connection_data.get("api_key")
            if not api_key:
                raise HTTPException(status_code=400, detail="API 키가 필요합니다")
            
            # TODO: 실제 OpenAI API 연결 테스트 구현
            
            return {"success": True, "message": "OpenAI API 연결 성공"}
            
        elif connection_type == "claude":
            # Claude API 연결 테스트
            api_key = connection_data.get("api_key")
            if not api_key:
                raise HTTPException(status_code=400, detail="API 키가 필요합니다")
            
            # TODO: 실제 Claude API 연결 테스트 구현
            
            return {"success": True, "message": "Claude API 연결 성공"}
            
        elif connection_type == "github":
            # GitHub 연결 테스트
            token = connection_data.get("token")
            username = connection_data.get("username")
            
            if not token or not username:
                raise HTTPException(status_code=400, detail="토큰과 사용자명이 필요합니다")
            
            # TODO: 실제 GitHub API 연결 테스트 구현
            
            return {"success": True, "message": "GitHub 연결 성공"}
            
        else:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 연결 유형: {connection_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"연결 테스트 오류: {str(e)}")
        return {"success": False, "message": f"연결 테스트 중 오류 발생: {str(e)}"}
