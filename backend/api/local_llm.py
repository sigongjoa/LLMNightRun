"""
로컬 LLM API 모듈

LM Studio 등의 로컬 LLM 연동 관련 API 엔드포인트를 제공합니다.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from backend.models.agent import Message
from backend.models.enums import LLMType
from backend.llm import LLM, ChatCompletionResponse
from backend.config.settings import settings
from backend.llm_studio import DEFAULT_LM_STUDIO_URL
from backend.config.local_llm import LocalLLMConfig, default_local_llm_config

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/api/local-llm",
    tags=["Local LLM"],
    responses={404: {"description": "Not found"}},
)


class LocalLLMStatusResponse(BaseModel):
    """로컬 LLM 상태 응답 모델"""
    enabled: bool
    connected: bool
    base_url: str
    model_id: Optional[str] = None
    error: Optional[str] = None


class LocalLLMConfigUpdateRequest(BaseModel):
    """로컬 LLM 설정 업데이트 요청 모델"""
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class LocalLLMChatRequest(BaseModel):
    """로컬 LLM 채팅 요청 모델"""
    messages: List[Message]
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class LocalLLMChatResponse(BaseModel):
    """로컬 LLM 채팅 응답 모델"""
    content: str
    model_id: str


# 현재 구성 (글로벌 변수)
current_config = default_local_llm_config
llm_instance = None


@router.get("/ping")
async def ping():
    """
    프론트엔드와 백엔드 통신 테스트
    
    Returns:
        간단한 응답
    """
    return {"status": "ok", "message": "pong"}


def get_llm_instance() -> LLM:
    """LLM 인스턴스 가져오기"""
    global llm_instance
    
    if llm_instance is None:
        llm_instance = LLM(
            config_name="local",
            llm_type=LLMType.LOCAL_LLM,
            base_url=current_config.base_url
        )
    
    return llm_instance


@router.get("/status")
async def get_status() -> LocalLLMStatusResponse:
    """
    로컬 LLM 상태 확인
    
    Returns:
        로컬 LLM 상태 정보
    """
    global current_config
    
    # LLM 상태 기본값
    status = LocalLLMStatusResponse(
        enabled=current_config.enabled,
        connected=False,
        base_url=current_config.base_url,
        model_id=current_config.model_id
    )
    
    # 비활성화된 경우 바로 반환
    if not current_config.enabled:
        return status
    
    # 연결 테스트
    try:
        llm = get_llm_instance()
        # 간단한 테스트 메시지
        test_message = Message(role="user", content="테스트 메시지입니다.")
        
        # LLM 호출 (비동기)
        await llm.ask([test_message], max_tokens=10)
        
        # 연결 성공
        status.connected = True
        
    except Exception as e:
        # 연결 실패
        logger.error(f"로컬 LLM 연결 오류: {str(e)}")
        status.error = str(e)
        status.connected = False
    
    return status


@router.put("/config")
async def update_config(config: LocalLLMConfigUpdateRequest) -> LocalLLMConfig:
    """
    로컬 LLM 설정 업데이트
    
    Args:
        config: 업데이트할 설정 정보
        
    Returns:
        업데이트된 전체 설정
    """
    global current_config, llm_instance
    
    # 제공된 값으로 설정 업데이트
    if config.enabled is not None:
        current_config.enabled = config.enabled
    
    if config.base_url is not None:
        current_config.base_url = config.base_url
        # URL이 변경되면 LLM 인스턴스 재생성 필요
        llm_instance = None
    
    if config.model_id is not None:
        current_config.model_id = config.model_id
    
    if config.max_tokens is not None:
        current_config.max_tokens = config.max_tokens
    
    if config.temperature is not None:
        current_config.temperature = config.temperature
    
    if config.top_p is not None:
        current_config.top_p = config.top_p
    
    return current_config


@router.post("/chat")
async def chat(request: LocalLLMChatRequest) -> LocalLLMChatResponse:
    """
    로컬 LLM과 채팅
    
    Args:
        request: 채팅 요청 정보
        
    Returns:
        LLM 응답
    """
    global current_config
    
    # LLM이 비활성화된 경우
    if not current_config.enabled:
        raise HTTPException(status_code=400, detail="로컬 LLM이 비활성화되어 있습니다")
    
    try:
        # LLM 인스턴스 가져오기
        llm = get_llm_instance()
        
        # 시스템 메시지 처리
        system_msgs = None
        if request.system_message:
            system_msgs = [Message(role="system", content=request.system_message)]
        
        # LLM 호출 옵션
        options = {
            "max_tokens": request.max_tokens or current_config.max_tokens,
            "temperature": request.temperature or current_config.temperature,
            "top_p": request.top_p or current_config.top_p,
            "timeout": 120  # 타임아웃 증가
        }
        
        logger.info(f"LLM 호출 시작: {len(request.messages)}개 메시지, 옵션: {options}")
        
        # LLM 호출
        response = await llm.ask(
            messages=request.messages,
            system_msgs=system_msgs,
            **options
        )
        
        logger.info(f"LLM 호출 완료: 응답 길이 {len(response) if response else 0} 문자")
        
        # 응답 반환
        return LocalLLMChatResponse(
            content=response,
            model_id=current_config.model_id
        )
        
    except Exception as e:
        logger.error(f"로컬 LLM 채팅 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로컬 LLM 오류: {str(e)}")
