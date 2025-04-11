"""
로컬 LLM(LM Studio) 관련 라우터
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import httpx
import logging
from pydantic import BaseModel

# 로깅 설정
logger = logging.getLogger(__name__)

# LM Studio URL 설정
from backend.llm_studio import DEFAULT_LM_STUDIO_URL

# 라우터 생성 (경로 지정 없이 생성)
router = APIRouter(tags=["local-llm"])

# 기본 포트 정의 (LM Studio는 1234 포트 사용)
DEFAULT_PORT = 1234

# 모델 클래스 정의
class LLMStatusResponse(BaseModel):
    enabled: bool = True
    connected: bool
    base_url: str
    model_id: Optional[str] = None
    error: Optional[str] = None

class LLMModel(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None

class LLMGenerateRequest(BaseModel):
    prompt: str
    model_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class LLMGenerateResponse(BaseModel):
    text: str
    model_id: str

# 채팅 관련 클래스
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None

class ChatResponse(BaseModel):
    content: str
    model_id: str

# LM Studio 설정 변경 엔드포인트
class LLMConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    model_id: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

class LLMConfig(BaseModel):
    enabled: bool
    base_url: str
    name: str = "LM Studio"
    model_id: str
    max_tokens: int
    temperature: float
    top_p: float = 1.0
    timeout: int = 30

# 서버 핑 엔드포인트
@router.get("/ping")
async def ping():
    """
    서버가 살아있는지 확인하는 간단한 엔드포인트
    """
    return {"status": "ok", "message": "LLM API 서버가 정상적으로 응답하고 있습니다."}

# LM Studio 상태 확인 엔드포인트
@router.get("/status")
async def get_local_llm_status():
    """
    로컬 LLM(LM Studio) 상태를 확인합니다.
    """
    try:
        from backend.config.settings import settings
        
        # 설정에서 URL 가져오기 (기본값: 1234 포트)
        base_url = settings.llm.local_llm_base_url or DEFAULT_LM_STUDIO_URL
        
        # URL 슬래시 정리
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        # 로그 추가
        logger.info(f"LM Studio URL 확인: {base_url}")
        
        # 기본 응답 생성(커넥션 상태 확인 실패시 대비)
        default_response = {
            "enabled": True,
            "connected": False,
            "base_url": base_url,
            "error": "LM Studio에 연결할 수 없습니다. LM Studio가 실행 중인지 확인해주세요."
        }
        
        # LM Studio 모델 목록 요청
        async with httpx.AsyncClient(timeout=5.0) as client:
            logger.info(f"LM Studio 모델 목록 요청 중: {base_url}/v1/models")
            response = await client.get(f"{base_url}/v1/models")
            
            logger.info(f"LM Studio 응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                # 응답 파싱
                models_data = response.json()
                models = models_data.get("data", [])
                
                # LM Studio 연결 성공
                logger.info(f"LM Studio 연결 성공: {len(models)}개 모델 발견")
                
                # 우선 사용할 모델을 찾습니다
                selected_model_id = None
                if len(models) > 0:
                    selected_model_id = models[0].get("id")
                    logger.info(f"선택된 모델 ID: {selected_model_id}")
                
                # 프론트에서 기대하는 응답 양식으로 반환
                return {
                    "enabled": True, 
                    "connected": True,
                    "base_url": base_url,
                    "model_id": selected_model_id
                }
            else:
                logger.warning(f"LM Studio 요청 실패: {response.status_code} {response.text}")
                return default_response
    
    except httpx.ConnectError as e:
        logger.error(f"LM Studio 연결 오류: {str(e)}")
        return {
            "enabled": True,
            "connected": False,
            "base_url": DEFAULT_LM_STUDIO_URL,
            "error": f"LM Studio 연결 오류: {str(e)}"
        }
    
    except httpx.TimeoutException as e:
        logger.error(f"LM Studio 요청 타임아웃: {str(e)}")
        return {
            "enabled": True,
            "connected": False,
            "base_url": DEFAULT_LM_STUDIO_URL,
            "error": f"LM Studio 요청 타임아웃: {str(e)}"
        }
        
    except Exception as e:
        logger.error(f"LM Studio 상태 확인 중 오류: {str(e)}")
        return {
            "enabled": True,
            "connected": False,
            "base_url": DEFAULT_LM_STUDIO_URL,
            "error": f"LM Studio 상태 확인 중 오류: {str(e)}"
        }

# 사용 가능한 모델 목록 조회
@router.get("/models", response_model=List[LLMModel])
async def get_local_llm_models():
    """
    LM Studio에서 사용 가능한 모델 목록을 반환합니다.
    """
    try:
        # 상태 API 호출
        status = await get_local_llm_status()
        
        if not status.connected:
            raise HTTPException(
                status_code=503,
                detail=f"LM Studio 서버에 연결할 수 없습니다: {status.error}"
            )
        
        # 모델 목록 변환
        models = []
        for model_data in status.available_models:
            models.append(LLMModel(
                id=model_data.get("id", "unknown"),
                name=model_data.get("name", model_data.get("id", "Unknown Model")),
                description=model_data.get("description", "")
            ))
        
        return models
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"모델 목록 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 텍스트 생성 엔드포인트
@router.post("/generate", response_model=LLMGenerateResponse)
async def generate_text(request: LLMGenerateRequest):
    """
    LM Studio를 사용하여 텍스트를 생성합니다.
    """
    from backend.llm_studio import generate_from_local_llm
    from backend.config.settings import settings
    
    try:
        # 모델 ID 설정
        model_id = request.model_id
        if not model_id:
            # 설정에서 모델 ID 가져오기
            if hasattr(settings, "llm") and hasattr(settings.llm, "local_llm_model_id"):
                model_id = settings.llm.local_llm_model_id
            else:
                model_id = "deepseek-r1-distill-qwen-7b"  # 기본값
        
        # 메시지 구성
        messages = [
            {"role": "user", "content": request.prompt}
        ]
        
        # 텍스트 생성
        generated_text = await generate_from_local_llm(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model_id=model_id
        )
        
        return LLMGenerateResponse(
            text=generated_text,
            model_id=model_id
        )
    
    except Exception as e:
        logger.error(f"텍스트 생성 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"텍스트 생성 중 오류가 발생했습니다: {str(e)}"
        )

# LM Studio 설정 변경 엔드포인트
@router.put("/config", response_model=LLMConfig)
async def update_llm_settings(settings_update: LLMConfigUpdate):
    """
    LM Studio 설정을 업데이트합니다.
    """
    try:
        from backend.config.settings import settings
        
        # 설정 업데이트
        if settings_update.enabled is not None:
            settings.llm.enabled = settings_update.enabled
        
        if settings_update.base_url:
            settings.llm.local_llm_base_url = settings_update.base_url
        
        if settings_update.model_id:
            settings.llm.local_llm_model_id = settings_update.model_id
        
        if settings_update.temperature is not None:
            settings.llm.local_llm_temperature = settings_update.temperature
        
        if settings_update.max_tokens is not None:
            settings.llm.local_llm_max_tokens = settings_update.max_tokens
            
        # 추가 설정 (필요하면 추가)
        top_p = getattr(settings.llm, 'top_p', 1.0)
        if settings_update.top_p is not None:
            top_p = settings_update.top_p
        
        # 변경된 설정 반환
        return LLMConfig(
            enabled=getattr(settings.llm, 'enabled', True),
            base_url=settings.llm.local_llm_base_url,
            name="LM Studio",
            model_id=settings.llm.local_llm_model_id,
            temperature=settings.llm.local_llm_temperature,
            max_tokens=settings.llm.local_llm_max_tokens,
            top_p=top_p,
            timeout=getattr(settings.llm, 'timeout', 30)
        )
    
    except Exception as e:
        logger.error(f"설정 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"설정 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

# 채팅 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat_with_local_llm(request: ChatRequest):
    """
    LM Studio를 사용하여 채팅을 진행합니다.
    """
    from backend.llm_studio import call_lm_studio, extract_content
    from backend.config.settings import settings
    from backend.models.agent import Message
    
    try:
        # 설정에서 URL 가져오기
        base_url = settings.llm.local_llm_base_url or DEFAULT_LM_STUDIO_URL
        
        # 메세지 변환
        messages = []
        for msg in request.messages:
            messages.append(Message(
                role=msg.role,
                content=msg.content,
                name=msg.name
            ))
        
        # 시스템 메세지 처리
        system_msgs = None
        if request.system_message:
            system_msgs = [Message(role="system", content=request.system_message)]
        
        # 옵션 설정
        model_id = settings.llm.local_llm_model_id
        temperature = request.temperature if request.temperature is not None else settings.llm.local_llm_temperature
        max_tokens = request.max_tokens if request.max_tokens is not None else settings.llm.local_llm_max_tokens
        
        # API 호출
        response_data = await call_lm_studio(
            messages=messages,
            system_msgs=system_msgs,
            base_url=base_url,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 응답 컨텐츠 추출
        content = extract_content(response_data) or ""
        
        return ChatResponse(
            content=content,
            model_id=model_id
        )
    
    except Exception as e:
        logger.error(f"채팅 중 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"채팅 중 오류가 발생했습니다: {str(e)}"
        )
