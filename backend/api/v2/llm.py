"""
LLM API 모듈 v2

LLM 관련 API 엔드포인트를 제공합니다. 리팩터링된 버전.
"""

from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...models.enums import LLMType
from ...controllers.llm_controller import LLMController


router = APIRouter(prefix="/api/v2/llm", tags=["LLM"])


class LLMPromptRequest(BaseModel):
    """LLM 프롬프트 요청 모델"""
    prompt: str = Field(..., description="LLM에 전송할 프롬프트")
    llm_type: LLMType = Field(..., description="사용할 LLM 유형")
    model: Optional[str] = Field(None, description="사용할 모델 이름 (선택 사항)")
    temperature: Optional[float] = Field(None, description="온도 (0~1) (선택 사항)")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수 (선택 사항)")
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트 (선택 사항)")


class LLMPromptResponse(BaseModel):
    """LLM 프롬프트 응답 모델"""
    success: bool = Field(..., description="요청 성공 여부")
    data: Dict[str, Any] = Field(..., description="응답 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")


async def get_llm_controller() -> LLMController:
    """LLM 컨트롤러를 의존성으로 제공합니다."""
    return LLMController()


@router.post("/generate", response_model=LLMPromptResponse, summary="LLM 텍스트 생성")
async def generate_text(
    request: LLMPromptRequest,
    controller: LLMController = Depends(get_llm_controller)
) -> Dict[str, Any]:
    """
    LLM에 프롬프트를 전송하고 텍스트를 생성합니다.
    
    Args:
        request: LLM 프롬프트 요청 데이터
        controller: LLM 컨트롤러 인스턴스
        
    Returns:
        생성된 텍스트와 메타데이터
    """
    response = await controller.generate_text(
        llm_type=request.llm_type,
        prompt=request.prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt
    )
    
    return response


@router.get("/models", summary="사용 가능한 LLM 모델 목록 조회")
async def get_models(
    llm_type: Optional[LLMType] = None,
    controller: LLMController = Depends(get_llm_controller)
) -> Dict[str, Any]:
    """
    사용 가능한 LLM 모델 목록을 반환합니다.
    
    Args:
        llm_type: LLM 유형 (선택 사항)
        controller: LLM 컨트롤러 인스턴스
        
    Returns:
        사용 가능한 모델 목록
    """
    return await controller.get_available_models(llm_type)
