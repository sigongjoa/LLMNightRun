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
    # 명시적으로 던전 이해 안되는 물음표로 column을 선택하여 실제 데이터베이스에 존재하는 것만 사용
    from sqlalchemy import select
    
    # 데이터베이스에 있는 실제 컴럼만 지정하여 조회
    stmt = select(Settings.id, 
               Settings.default_openai_api_key, 
               Settings.default_claude_api_key, 
               Settings.default_github_token, 
               Settings.default_github_repo, 
               Settings.default_github_username, 
               Settings.updated_at)
    
    result = db.execute(stmt).first()
    
    if not result:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    
    # Settings 객체 생성
    settings = Settings(
        id=result.id,
        default_openai_api_key=result.default_openai_api_key,
        default_claude_api_key=result.default_claude_api_key,
        default_github_token=result.default_github_token,
        default_github_repo=result.default_github_repo,
        default_github_username=result.default_github_username,
        updated_at=result.updated_at
    )
    
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
    from sqlalchemy import select, update
    
    # 설정 조회
    stmt = select(Settings.id).limit(1)
    result = db.execute(stmt).first()
    
    if not result:
        # 설정이 없는 경우 생성
        settings = Settings()
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    
    # 업데이트할 값만 선택
    valid_fields = {
        'default_openai_api_key',
        'default_claude_api_key',
        'default_github_token',
        'default_github_repo',
        'default_github_username'
    }
    
    data_to_update = {}
    for key, value in settings_data.items():
        if key in valid_fields and value is not None:
            data_to_update[key] = value
    
    # 업데이트 실행
    if data_to_update:
        stmt = update(Settings).values(**data_to_update).where(Settings.id == result.id)
        db.execute(stmt)
        db.commit()
    
    # 업데이트된 설정 가져오기
    return get_settings(db)
