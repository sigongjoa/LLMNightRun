"""
LLM 서비스 테스트 모듈

LLM 서비스 클래스의 단위 테스트를 포함합니다.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from backend.services.llm_service import (
    LLMService, OpenAIProvider, ClaudeProvider, LocalLLMProvider, CustomAPIProvider
)
from backend.models.enums import LLMType
from backend.exceptions import LLMError, TokenLimitExceeded


class TestLLMService:
    """LLM 서비스 테스트 클래스"""
    
    @pytest.fixture
    def llm_service(self) -> LLMService:
        """LLM 서비스 인스턴스를 제공하는 fixture"""
        # 실제 API 키 초기화를 방지하기 위해 패치
        with patch('backend.services.llm_service.settings') as mock_settings:
            # 모의 설정 구성
            mock_settings.llm.openai_api_key = "test_openai_key"
            mock_settings.llm.claude_api_key = "test_claude_key"
            mock_settings.llm.model_name = "test-model"
            mock_settings.llm.temperature = 0.7
            mock_settings.llm.max_tokens = 1000
            
            # 서비스 인스턴스 생성
            service = LLMService()
            
            return service
    
    @pytest.mark.asyncio
    async def test_get_response_with_openai(self, llm_service: LLMService):
        """OpenAI 제공자를 사용한 응답 생성 테스트"""
        # 모의 OpenAI 제공자 생성
        mock_provider = MagicMock()
        mock_provider.generate.return_value = asyncio.Future()
        mock_provider.generate.return_value.set_result("테스트 응답입니다.")
        
        # 모의 제공자 등록
        llm_service.providers[LLMType.OPENAI_API] = mock_provider
        
        # 서비스 호출
        response = await llm_service.get_response(
            LLMType.OPENAI_API, 
            "테스트 프롬프트입니다.",
            model="test-model"
        )
        
        # 검증
        assert response == "테스트 응답입니다."
        mock_provider.generate.assert_called_once_with(
            "테스트 프롬프트입니다.", 
            model="test-model"
        )
        
    @pytest.mark.asyncio
    async def test_get_response_with_claude(self, llm_service: LLMService):
        """Claude 제공자를 사용한 응답 생성 테스트"""
        # 모의 Claude 제공자 생성
        mock_provider = MagicMock()
        mock_provider.generate.return_value = asyncio.Future()
        mock_provider.generate.return_value.set_result("Claude 응답입니다.")
        
        # 모의 제공자 등록
        llm_service.providers[LLMType.CLAUDE_API] = mock_provider
        
        # 서비스 호출
        response = await llm_service.get_response(
            LLMType.CLAUDE_API, 
            "테스트 프롬프트입니다.",
            model="claude-2"
        )
        
        # 검증
        assert response == "Claude 응답입니다."
        mock_provider.generate.assert_called_once_with(
            "테스트 프롬프트입니다.", 
            model="claude-2"
        )
    
    @pytest.mark.asyncio
    async def test_get_response_unsupported_llm(self, llm_service: LLMService):
        """지원되지 않는 LLM 유형 테스트"""
        # 지원되지 않는 LLM 유형으로 설정
        llm_service.providers = {}
        
        # 예외 발생 확인
        with pytest.raises(LLMError, match="지원되지 않는 LLM 유형입니다"):
            await llm_service.get_response(
                LLMType.OPENAI_API, 
                "테스트 프롬프트입니다."
            )
    
    def test_register_provider(self, llm_service: LLMService):
        """제공자 등록 테스트"""
        # 모의 제공자 생성
        mock_provider = MagicMock()
        
        # 제공자 등록
        llm_service.register_provider(LLMType.LOCAL_LLM, mock_provider)
        
        # 검증
        assert llm_service.providers[LLMType.LOCAL_LLM] == mock_provider
    
    def test_register_custom_provider(self, llm_service: LLMService):
        """커스텀 제공자 등록 테스트"""
        # 기존 제공자 제거
        llm_service.providers = {}
        
        # 커스텀 제공자 등록
        llm_service.register_custom_provider(
            name="custom_test",
            api_url="https://api.example.com",
            api_key="test_key",
            headers={"X-Custom-Header": "value"},
            payload_template={"engine": "test-engine"}
        )
        
        # 검증
        assert LLMType.CUSTOM_API in llm_service.providers
        assert isinstance(llm_service.providers[LLMType.CUSTOM_API], CustomAPIProvider)


class TestOpenAIProvider:
    """OpenAI 제공자 테스트 클래스"""
    
    @pytest.fixture
    def openai_provider(self) -> OpenAIProvider:
        """OpenAI 제공자 인스턴스를 제공하는 fixture"""
        return OpenAIProvider(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_generate(self, openai_provider: OpenAIProvider):
        """텍스트 생성 기능 테스트"""
        # 모의 OpenAI 응답 생성
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI 응답입니다."
        
        # 모의 OpenAI 클라이언트 패치
        with patch('backend.services.llm_service.openai.AsyncOpenAI') as mock_openai:
            # 모의 클라이언트 설정
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = asyncio.Future()
            mock_client.chat.completions.create.return_value.set_result(mock_response)
            mock_openai.return_value = mock_client
            
            # 제공자 호출
            response = await openai_provider.generate(
                "테스트 프롬프트입니다.",
                model="gpt-3.5-turbo"
            )
            
            # 검증
            assert response == "OpenAI 응답입니다."
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_token_limit_error(self, openai_provider: OpenAIProvider):
        """토큰 제한 오류 테스트"""
        # 모의 OpenAI 오류 생성
        mock_error = MagicMock()
        mock_error.__str__.return_value = "maximum context length exceeded"
        
        # 모의 OpenAI 클라이언트 패치
        with patch('backend.services.llm_service.openai.AsyncOpenAI') as mock_openai:
            # 모의 클라이언트 설정
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = mock_error
            mock_openai.return_value = mock_client
            
            # 예외 발생 확인
            with pytest.raises(TokenLimitExceeded):
                await openai_provider.generate(
                    "테스트 프롬프트입니다.",
                    model="gpt-3.5-turbo"
                )


class TestClaudeProvider:
    """Claude 제공자 테스트 클래스"""
    
    @pytest.fixture
    def claude_provider(self) -> ClaudeProvider:
        """Claude 제공자 인스턴스를 제공하는 fixture"""
        return ClaudeProvider(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_generate(self, claude_provider: ClaudeProvider):
        """텍스트 생성 기능 테스트"""
        # 모의 httpx 응답 생성
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"completion": "Claude 응답입니다."}
        
        # 모의 httpx 클라이언트 패치
        with patch('backend.services.llm_service.httpx.AsyncClient') as mock_client:
            # 모의 클라이언트 설정
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 제공자 호출
            response = await claude_provider.generate(
                "테스트 프롬프트입니다.",
                model="claude-2"
            )
            
            # 검증
            assert response == "Claude 응답입니다."
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_error(self, claude_provider: ClaudeProvider):
        """API 오류 테스트"""
        # 모의 httpx 응답 생성
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "오류 메시지입니다."
        
        # 모의 httpx 클라이언트 패치
        with patch('backend.services.llm_service.httpx.AsyncClient') as mock_client:
            # 모의 클라이언트 설정
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # 예외 발생 확인
            with pytest.raises(LLMError):
                await claude_provider.generate(
                    "테스트 프롬프트입니다.",
                    model="claude-2"
                )
