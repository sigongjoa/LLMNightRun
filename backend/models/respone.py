"""
응답 관련 모델 정의 모듈

LLM 응답 및 관련 데이터 구조를 정의합니다.
"""

from pydantic import Field
from typing import Optional

from .base import IdentifiedModel
from .enums import LLMType


class Response(IdentifiedModel):
    """LLM 응답 모델"""
    question_id: int
    llm_type: LLMType
    content: str


class ResponseCreate(IdentifiedModel):
    """응답 생성 요청 모델"""
    question_id: int
    llm_type: LLMType
    content: str


class ResponseResponse(IdentifiedModel):
    """응답 응답 모델 (API 응답용)"""
    question_id: int
    llm_type: LLMType
    content: str


class LLMRequest(IdentifiedModel):
    """LLM 요청 모델"""
    content: str
    max_tokens: int = 1500
    temperature: float = 0.7