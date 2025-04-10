"""
LLM 컨트롤러 모듈

LLM 관련 API 엔드포인트의 요청을 처리하는 컨트롤러를 제공합니다.
"""

from typing import Dict, Any, Optional, List

from fastapi import HTTPException, status

from .base_controller import BaseController
from ..interfaces.llm_service import ILLMService
from ..models.enums import LLMType
from ..exceptions import LLMError, TokenLimitExceeded


class LLMController(BaseController):
    """
    LLM 관련 API 요청을 처리하는 컨트롤러
    """
    
    def __init__(self):
        """
        컨트롤러 초기화
        """
        super().__init__()
        self.llm_service = self._get_service(ILLMService)
    
    async def generate_text(
        self, 
        llm_type: LLMType, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        지정된 LLM으로 텍스트를 생성합니다.
        
        Args:
            llm_type: LLM 유형
            prompt: 프롬프트 텍스트
            model: 모델 이름 (선택 사항)
            temperature: 온도 (0~1) (선택 사항)
            max_tokens: 최대 토큰 수 (선택 사항)
            system_prompt: 시스템 프롬프트 (선택 사항)
            **kwargs: 추가 매개변수
            
        Returns:
            응답 데이터
            
        Raises:
            HTTPException: API 호출 실패 시
        """
        try:
            # 요청 로깅
            self.logger.info(f"텍스트 생성 요청: {llm_type}, 프롬프트 길이: {len(prompt)}자")
            
            # 매개변수 설정
            params = {}
            if model:
                params["model"] = model
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens:
                params["max_tokens"] = max_tokens
            if system_prompt:
                params["system_prompt"] = system_prompt
                
            # 추가 매개변수 병합
            params.update(kwargs)
            
            # LLM 서비스 호출
            response_text = await self.llm_service.get_response(llm_type, prompt, **params)
            
            # 응답 로깅
            self.logger.info(f"텍스트 생성 완료: {llm_type}, 응답 길이: {len(response_text)}자")
            
            # 응답 데이터 포맷팅
            return self._format_response({
                "text": response_text,
                "model": model or "default",
                "llm_type": llm_type
            }, "텍스트 생성이 완료되었습니다.")
            
        except TokenLimitExceeded as e:
            self.logger.warning(f"토큰 제한 초과: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"프롬프트가 너무 깁니다: {str(e)}"
            )
            
        except LLMError as e:
            self.logger.error(f"LLM 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM API 호출 실패: {str(e)}"
            )
            
        except Exception as e:
            self.logger.error(f"텍스트 생성 중 예기치 않은 오류: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"텍스트 생성 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_available_models(self, llm_type: Optional[LLMType] = None) -> Dict[str, Any]:
        """
        사용 가능한 LLM 모델 목록을 반환합니다.
        
        Args:
            llm_type: LLM 유형 (선택 사항)
            
        Returns:
            사용 가능한 모델 목록
        """
        # 현재는 하드코딩된 모델 목록을 반환
        # 추후 동적 모델 목록 조회로 변경 가능
        
        models = {
            LLMType.openai_api: [
                "gpt-3.5-turbo", 
                "gpt-4",
                "gpt-4-turbo"
            ],
            LLMType.claude_api: [
                "claude-1", 
                "claude-2",
                "claude-instant-1"
            ],
            LLMType.local_llm: [
                "local-default"
            ],
            LLMType.claude_web: [
                "custom-default"
            ]
        }
        
        if llm_type:
            if llm_type not in models:
                return self._format_response({"models": []}, f"{llm_type.value}에 대한 모델 목록이 없습니다.")
            
            return self._format_response({"models": models[llm_type]}, f"{llm_type.value} 모델 목록입니다.")
        
        # 모든 모델 목록 반환
        all_models = {}
        for type_name, model_list in models.items():
            all_models[type_name.value] = model_list
            
        return self._format_response({"models": all_models}, "모든 LLM 유형의 모델 목록입니다.")
