"""
기본 Pydantic 모델 정의 모듈

모든 API 모델의 기본 클래스를 제공합니다.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TimeStampedModel(BaseModel):
    """타임스탬프가 있는 기본 모델"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IdentifiedModel(TimeStampedModel):
    """ID가 있는 모델"""
    id: Optional[int] = None


class VersionedModel(IdentifiedModel):
    """버전 관리 모델"""
    version: int = 1