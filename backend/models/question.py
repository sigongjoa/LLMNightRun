"""
질문 관련 모델 정의 모듈

질문 및 관련 데이터 구조를 정의합니다.
"""

from pydantic import Field
from typing import List, Optional

from .base import IdentifiedModel


class Question(IdentifiedModel):
    """사용자 질문 모델"""
    content: str
    tags: List[str] = Field(default_factory=list)


class QuestionCreate(IdentifiedModel):
    """질문 생성 요청 모델"""
    content: str
    tags: List[str] = Field(default_factory=list)


class QuestionResponse(IdentifiedModel):
    """질문 응답 모델 (API 응답용)"""
    content: str
    tags: List[str] = Field(default_factory=list)