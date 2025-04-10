"""
프로젝트 관련 모델 정의 모듈

프로젝트 및 관련 데이터 구조를 정의합니다.
프로젝트는 여러 질문, 응답, 코드 스니펫, 문서 등을 그룹화하는 상위 개념입니다.
"""

from pydantic import Field
from typing import List, Optional, Dict, Any

from .base import IdentifiedModel, TimeStampedModel


class Project(IdentifiedModel):
    """프로젝트 모델"""
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(TimeStampedModel):
    """프로젝트 생성 요청 모델"""
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(TimeStampedModel):
    """프로젝트 수정 요청 모델"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(IdentifiedModel):
    """프로젝트 응답 모델 (API 응답용)"""
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    question_count: int = 0
    code_count: int = 0
    document_count: int = 0
