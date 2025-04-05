"""
코드 스니펫 관련 모델 정의 모듈

코드 스니펫 및 템플릿에 대한 데이터 구조를 정의합니다.
"""

from pydantic import Field
from typing import List, Optional

from .base import VersionedModel
from .enums import CodeLanguage, LLMType


class CodeSnippet(VersionedModel):
    """코드 스니펫 모델"""
    title: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)
    source_llm: Optional[LLMType] = None
    question_id: Optional[int] = None  # 관련 질문 ID (있는 경우)
    response_id: Optional[int] = None  # 관련 응답 ID (있는 경우)
    parent_id: Optional[int] = None    # 부모 스니펫 ID (있는 경우)


class CodeSnippetCreate(VersionedModel):
    """코드 스니펫 생성 요청 모델"""
    title: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)
    source_llm: Optional[LLMType] = None
    question_id: Optional[int] = None
    response_id: Optional[int] = None


class CodeSnippetResponse(VersionedModel):
    """코드 스니펫 응답 모델 (API 응답용)"""
    title: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)
    source_llm: Optional[LLMType] = None
    question_id: Optional[int] = None
    response_id: Optional[int] = None


class CodeTemplate(VersionedModel):
    """코드 템플릿 모델"""
    name: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)


class CodeTemplateCreate(VersionedModel):
    """코드 템플릿 생성 요청 모델"""
    name: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)


class CodeTemplateResponse(VersionedModel):
    """코드 템플릿 응답 모델 (API 응답용)"""
    name: str
    description: Optional[str] = None
    content: str
    language: CodeLanguage
    tags: List[str] = Field(default_factory=list)