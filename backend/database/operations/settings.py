"""
설정 관련 데이터베이스 작업 모듈

시스템 설정에 대한 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import Optional, Union, Dict, Any
from datetime import datetime

from ..models import Settings as DBSettings


def get_settings(db: Session) -> Optional[DBSettings]:
    """
    시스템 설정을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        설정 객체 또는 None (설정이 없는 경우)
    """
    return db.query(DBSettings).first()


def create_or_update_settings(
    db: Session, 
    settings: Union[Dict[str, Any], Any]
) -> DBSettings:
    """
    시스템 설정을 생성하거나 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        settings: 설정 데이터
        
    Returns:
        생성 또는 업데이트된 설정 객체
    """
    # 딕셔너리로 변환
    if not isinstance(settings, dict):
        settings_data = settings.dict(exclude_unset=True)
    else:
        settings_data = settings
    
    # 기존 설정 조회
    db_settings = get_settings(db)
    
    if db_settings:
        # 기존 설정 업데이트
        for key, value in settings_data.items():
            if hasattr(db_settings, key) and value is not None:
                setattr(db_settings, key, value)
        
        # 수정 시간 갱신
        db_settings.updated_at = datetime.utcnow()
    else:
        # 새 설정 생성
        db_settings = DBSettings(**settings_data)
        db.add(db_settings)
    
    # 변경사항 저장
    db.commit()
    db.refresh(db_settings)
    
    return db_settings