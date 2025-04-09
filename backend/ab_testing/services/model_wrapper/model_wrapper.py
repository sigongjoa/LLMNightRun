"""
모델 래퍼 모듈

LLM 모델과의 통신을 처리하는 래퍼 클래스를 제공합니다.
"""

import httpx
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from backend.config.settings import settings
from backend.logger import get_logger

# 로거 설정
logger = get_logger(__name__)


class ModelWrapper(ABC):
    """
    LLM 모델 래퍼 추상 클래스
    """
    
    @abstractmethod
    async def generate(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        LLM을 사용하여 텍스트를 생성합니다.
        
        Args:
            system_message: 시스템 메시지
            user_message: 사용자 메시지
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 텍스트
        """
        pass


class OpenAIWrapper(ModelWrapper):
    """
    OpenAI API 래퍼 클래스
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        OpenAI API 래퍼 초기화
        
        Args:
            model: 사용할 모델 이름
        """
        self.model = model
        self.api_key = settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
            
        logger.info(f"OpenAI API 래퍼 초기화 완료 (모델: {model})")
    
    async def generate(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        OpenAI API를 사용하여 텍스트를 생성합니다.
        
        Args:
            system_message: 시스템 메시지
            user_message: 사용자 메시지
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 텍스트
        """
        try:
            # API 요청 데이터 구성
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # OpenAI API 호출
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # 응답 컨텐츠 추출
                if (
                    "choices" in data 
                    and len(data["choices"]) > 0 
                    and "message" in data["choices"][0]
                    and "content" in data["choices"][0]["message"]
                ):
                    return data["choices"][0]["message"]["content"]
                
                logger.error(f"OpenAI API 응답 형식 오류: {data}")
                return "OpenAI API 응답을 처리할 수 없습니다."
        
        except Exception as e:
            logger.error(f"OpenAI API 호출 오류: {str(e)}")
            return f"OpenAI API 오류: {str(e)}"


class ClaudeWrapper(ModelWrapper):
    """
    Claude API 래퍼 클래스
    """
    
    def __init__(self, model: str = "claude-3-opus-20240229"):
        """
        Claude API 래퍼 초기화
        
        Args:
            model: 사용할 모델 이름
        """
        self.model = model
        self.api_key = settings.claude_api_key
        
        if not self.api_key:
            raise ValueError("Claude API 키가 설정되지 않았습니다")
            
        logger.info(f"Claude API 래퍼 초기화 완료 (모델: {model})")
    
    async def generate(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Claude API를 사용하여 텍스트를 생성합니다.
        
        Args:
            system_message: 시스템 메시지
            user_message: 사용자 메시지
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 텍스트
        """
        try:
            # API 요청 데이터 구성
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Claude API 호출
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=request_data,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # 응답 컨텐츠 추출
                if (
                    "content" in data
                    and len(data["content"]) > 0
                    and "text" in data["content"][0]
                ):
                    return data["content"][0]["text"]
                
                logger.error(f"Claude API 응답 형식 오류: {data}")
                return "Claude API 응답을 처리할 수 없습니다."
        
        except Exception as e:
            logger.error(f"Claude API 호출 오류: {str(e)}")
            return f"Claude API 오류: {str(e)}"


class MistralWrapper(ModelWrapper):
    """
    Mistral API 래퍼 클래스
    """
    
    def __init__(self, model: str = "mistral-large"):
        """
        Mistral API 래퍼 초기화
        
        Args:
            model: 사용할 모델 이름
        """
        self.model = model
        self.api_key = settings.mistral_api_key
        
        if not self.api_key:
            raise ValueError("Mistral API 키가 설정되지 않았습니다")
            
        logger.info(f"Mistral API 래퍼 초기화 완료 (모델: {model})")
    
    async def generate(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Mistral API를 사용하여 텍스트를 생성합니다.
        
        Args:
            system_message: 시스템 메시지
            user_message: 사용자 메시지
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 텍스트
        """
        try:
            # API 요청 데이터 구성
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Mistral API 호출
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # 응답 컨텐츠 추출
                if (
                    "choices" in data 
                    and len(data["choices"]) > 0 
                    and "message" in data["choices"][0]
                    and "content" in data["choices"][0]["message"]
                ):
                    return data["choices"][0]["message"]["content"]
                
                logger.error(f"Mistral API 응답 형식 오류: {data}")
                return "Mistral API 응답을 처리할 수 없습니다."
        
        except Exception as e:
            logger.error(f"Mistral API 호출 오류: {str(e)}")
            return f"Mistral API 오류: {str(e)}"


def get_model_wrapper(model_name: str) -> ModelWrapper:
    """
    모델 이름에 따라 적절한 모델 래퍼를 반환합니다.
    
    Args:
        model_name: 모델 이름
        
    Returns:
        ModelWrapper 인스턴스
        
    Raises:
        ValueError: 지원하지 않는 모델인 경우
    """
    # OpenAI 모델
    if model_name.startswith("gpt-"):
        return OpenAIWrapper(model=model_name)
    
    # Claude 모델
    elif model_name.startswith("claude-"):
        return ClaudeWrapper(model=model_name)
    
    # Mistral 모델
    elif model_name.startswith("mistral-"):
        return MistralWrapper(model=model_name)
    
    # 지원하지 않는 모델
    else:
        logger.warning(f"지원하지 않는 모델: {model_name}, OpenAI의 gpt-4로 대체합니다.")
        return OpenAIWrapper(model="gpt-4")
