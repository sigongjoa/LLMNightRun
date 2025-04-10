"""
설정 관련 데이터베이스 작업 모듈
"""

from sqlalchemy.orm import Session
from ..models import Settings


def get_settings(db: Session) -> Settings:
    """
    시스템 설정을 가져옵니다. 설정이 없으면 새로운 설정을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        설정 객체
    """
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


def update_settings(db: Session, settings_data: dict) -> Settings:
    """
    시스템 설정을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        settings_data: 업데이트할 설정 데이터
        
    Returns:
        업데이트된 설정 객체
    """
    settings = get_settings(db)
    
    for key, value in settings_data.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    
    return settings
