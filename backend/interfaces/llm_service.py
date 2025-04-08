"""
LLM 서비스 인터페이스 모듈

LLM(Large Language Model) 서비스의 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

from ..models.enums import LLMType
from ..models.agent import Message


class ILLMProvider(ABC):
    """LLM 제공자 인터페이스"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        LLM API를 사용하여 텍스트 생성
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션 (모델, 온도, 토큰 수 등)
            
        Returns:
            생성된 텍스트
        """
        pass


class ILLMService(ABC):
    """LLM 서비스 인터페이스"""
    
    @abstractmethod
    def register_provider(self, llm_type: LLMType, provider: ILLMProvider) -> None:
        """
        새 LLM 제공자 등록
        
        Args:
            llm_type: LLM 유형
            provider: LLM 제공자 인스턴스
        """
        pass
    
    @abstractmethod
    def register_custom_provider(
        self, 
        name: str, 
        api_url: str, 
        api_key: str, 
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        커스텀 LLM 제공자 등록
        
        Args:
            name: 제공자 이름
            api_url: API 엔드포인트 URL
            api_key: API 키
            headers: 요청 헤더 (선택 사항)
            payload_template: 요청 본문 템플릿 (선택 사항)
        """
        pass
    
    @abstractmethod
    async def get_response(self, llm_type: LLMType, prompt: str, **kwargs) -> str:
        """
        지정된 LLM에 프롬프트를 전송하고 응답을 받아옵니다.
        
        Args:
            llm_type: LLM 유형
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - model: 모델 이름
                - temperature: 온도
                - max_tokens: 최대 토큰 수
                - system_prompt: 시스템 프롬프트
            
        Returns:
            LLM의 응답 텍스트
        """
        pass
