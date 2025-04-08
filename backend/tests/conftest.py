"""
pytest 설정 모듈

테스트에 필요한 fixture 및 설정을 제공합니다.
"""

import os
import sys
import pytest
from typing import Dict, Any, Generator, Optional

# 백엔드 루트 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.main import app
from backend.core.di import DiContainer
from backend.core.service_locator import setup_services
from backend.interfaces.llm_service import ILLMService
from backend.models.enums import LLMType


@pytest.fixture
def app_instance() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 제공하는 fixture"""
    return app


@pytest.fixture
def test_client(app_instance: FastAPI) -> TestClient:
    """테스트 클라이언트를 제공하는 fixture"""
    return TestClient(app_instance)


@pytest.fixture
def di_container() -> DiContainer:
    """
    테스트를 위한 빈 DI 컨테이너를 제공하는 fixture
    """
    return DiContainer()


class MockLLMProvider:
    """테스트를 위한 모의 LLM 제공자"""
    
    def __init__(self, response_text: str = "테스트 응답입니다."):
        self.response_text = response_text
        self.last_prompt = None
        self.last_kwargs = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """모의 텍스트 생성 함수"""
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return self.response_text


class MockLLMService:
    """테스트를 위한 모의 LLM 서비스"""
    
    def __init__(self):
        self.providers = {}
        self.last_llm_type = None
        self.last_prompt = None
        self.last_kwargs = None
        
        # 기본 모의 제공자 등록
        self.providers[LLMType.OPENAI_API] = MockLLMProvider("OpenAI 응답입니다.")
        self.providers[LLMType.CLAUDE_API] = MockLLMProvider("Claude 응답입니다.")
        self.providers[LLMType.LOCAL_LLM] = MockLLMProvider("로컬 LLM 응답입니다.")
    
    def register_provider(self, llm_type: LLMType, provider: Any) -> None:
        """모의 제공자 등록 함수"""
        self.providers[llm_type] = provider
    
    def register_custom_provider(
        self, 
        name: str, 
        api_url: str, 
        api_key: str, 
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None
    ) -> None:
        """모의 커스텀 제공자 등록 함수"""
        try:
            llm_type = LLMType(name)
        except ValueError:
            llm_type = LLMType.CUSTOM_API
        
        self.providers[llm_type] = MockLLMProvider(f"{name} 응답입니다.")
    
    async def get_response(self, llm_type: LLMType, prompt: str, **kwargs) -> str:
        """모의 응답 생성 함수"""
        self.last_llm_type = llm_type
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        
        if llm_type not in self.providers:
            return f"지원되지 않는 LLM 유형입니다: {llm_type}"
        
        provider = self.providers[llm_type]
        return await provider.generate(prompt, **kwargs)


@pytest.fixture
def mock_llm_service() -> MockLLMService:
    """모의 LLM 서비스 인스턴스를 제공하는 fixture"""
    return MockLLMService()


@pytest.fixture
def test_di_container(di_container: DiContainer, mock_llm_service: MockLLMService) -> DiContainer:
    """
    모의 서비스가 등록된 DI 컨테이너를 제공하는 fixture
    """
    # 모의 LLM 서비스 등록
    di_container.register_instance(ILLMService, mock_llm_service)
    
    return di_container
