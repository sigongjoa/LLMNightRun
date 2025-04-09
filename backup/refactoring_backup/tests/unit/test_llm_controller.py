"""
LLM 컨트롤러 테스트 모듈

LLM 컨트롤러 클래스의 단위 테스트를 포함합니다.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from fastapi import HTTPException

from backend.controllers.llm_controller import LLMController
from backend.models.enums import LLMType
from backend.exceptions import LLMError, TokenLimitExceeded
from backend.interfaces.llm_service import ILLMService


class TestLLMController:
    """LLM 컨트롤러 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm_service(self) -> ILLMService:
        """모의 LLM 서비스를 제공하는 fixture"""
        mock_service = AsyncMock(spec=ILLMService)
        return mock_service
    
    @pytest.fixture
    def llm_controller(self, mock_llm_service: ILLMService) -> LLMController:
        """LLM 컨트롤러 인스턴스를 제공하는 fixture"""
        # get_service 패치
        with patch('backend.controllers.base_controller.BaseController._get_service') as mock_get_service:
            mock_get_service.return_value = mock_llm_service
            controller = LLMController()
            return controller
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, llm_controller: LLMController, mock_llm_service: ILLMService):
        """텍스트 생성 성공 테스트"""
        # 모의 서비스 설정
        mock_llm_service.get_response.return_value = "테스트 응답입니다."
        
        # 컨트롤러 호출
        response = await llm_controller.generate_text(
            llm_type=LLMType.OPENAI_API,
            prompt="테스트 프롬프트입니다.",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        
        # 검증
        assert response["success"] is True
        assert response["data"]["text"] == "테스트 응답입니다."
        assert response["data"]["model"] == "gpt-3.5-turbo"
        assert response["data"]["llm_type"] == LLMType.OPENAI_API
        
        # 서비스 호출 검증
        mock_llm_service.get_response.assert_called_once_with(
            LLMType.OPENAI_API, 
            "테스트 프롬프트입니다.",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
    
    @pytest.mark.asyncio
    async def test_generate_text_token_limit_error(self, llm_controller: LLMController, mock_llm_service: ILLMService):
        """토큰 제한 오류 테스트"""
        # 모의 서비스 설정 - 예외 발생
        mock_llm_service.get_response.side_effect = TokenLimitExceeded("토큰 제한 초과 오류입니다.")
        
        # 예외 발생 확인
        with pytest.raises(HTTPException) as excinfo:
            await llm_controller.generate_text(
                llm_type=LLMType.OPENAI_API,
                prompt="너무 긴 프롬프트입니다..." * 1000
            )
        
        # 예외 검증
        assert excinfo.value.status_code == 400
        assert "프롬프트가 너무 깁니다" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_generate_text_llm_error(self, llm_controller: LLMController, mock_llm_service: ILLMService):
        """LLM 오류 테스트"""
        # 모의 서비스 설정 - 예외 발생
        mock_llm_service.get_response.side_effect = LLMError("LLM API 오류입니다.")
        
        # 예외 발생 확인
        with pytest.raises(HTTPException) as excinfo:
            await llm_controller.generate_text(
                llm_type=LLMType.OPENAI_API,
                prompt="테스트 프롬프트입니다."
            )
        
        # 예외 검증
        assert excinfo.value.status_code == 500
        assert "LLM API 호출 실패" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_generate_text_unexpected_error(self, llm_controller: LLMController, mock_llm_service: ILLMService):
        """예기치 않은 오류 테스트"""
        # 모의 서비스 설정 - 예외 발생
        mock_llm_service.get_response.side_effect = ValueError("예기치 않은 오류입니다.")
        
        # 예외 발생 확인
        with pytest.raises(HTTPException) as excinfo:
            await llm_controller.generate_text(
                llm_type=LLMType.OPENAI_API,
                prompt="테스트 프롬프트입니다."
            )
        
        # 예외 검증
        assert excinfo.value.status_code == 500
        assert "텍스트 생성 중 오류가 발생했습니다" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, llm_controller: LLMController):
        """사용 가능한 모델 목록 조회 테스트"""
        # 컨트롤러 호출 - 특정 LLM 유형
        response_openai = await llm_controller.get_available_models(LLMType.OPENAI_API)
        
        # 검증
        assert response_openai["success"] is True
        assert "models" in response_openai["data"]
        assert "gpt-3.5-turbo" in response_openai["data"]["models"]
        assert "gpt-4" in response_openai["data"]["models"]
        
        # 컨트롤러 호출 - 모든 모델
        response_all = await llm_controller.get_available_models()
        
        # 검증
        assert response_all["success"] is True
        assert "models" in response_all["data"]
        assert "openai_api" in response_all["data"]["models"]
        assert "claude_api" in response_all["data"]["models"]
