"""
LM Studio 로컬 LLM 연동 모듈

LM Studio로 실행되는 로컬 LLM과의 통신을 처리하는 기능을 제공합니다.

# DO NOT CHANGE CODE: 이 파일은 Local LLM과 LM Studio 연동 핵심 기능입니다.
"""

import httpx
import logging
from typing import Dict, List, Optional, Any

from backend.models.agent import Message, ToolCall, ToolCallFunction
from backend.models.enums import LLMType

logger = logging.getLogger(__name__)

DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234"  # LM Studio 기본 포트


async def call_lm_studio(
    messages: List[Message],
    system_msgs: Optional[List[Message]] = None,
    base_url: str = DEFAULT_LM_STUDIO_URL,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    # DO NOT CHANGE CODE: LM Studio API 호출 핵심 기능
    """
    LM Studio API를 호출하여 응답을 받습니다.
    
    Args:
        messages: 메시지 목록
        system_msgs: 시스템 메시지 목록 (선택 사항)
        base_url: LM Studio API URL
        tools: 도구 정의 목록 (선택 사항)
        tool_choice: 도구 선택 모드 (선택 사항)
        **kwargs: 추가 LLM 옵션
        
    Returns:
        LM Studio API 응답
    """
    # OpenAI 호환 API 형식으로 메시지 변환
    formatted_messages = []
    
    # 시스템 메시지 추가
    if system_msgs and len(system_msgs) > 0:
        for sys_msg in system_msgs:
            formatted_messages.append({
                "role": sys_msg.role,
                "content": sys_msg.content
            })
    
    # 일반 메시지 추가
    for msg in messages:
        formatted_msg = {"role": msg.role}
        
        if msg.content is not None:
            formatted_msg["content"] = msg.content
        
        if msg.name is not None:
            formatted_msg["name"] = msg.name
            
        if hasattr(msg, 'base64_image') and msg.base64_image is not None:
            # 다중 모달리티 지원 (이미지 포함)
            formatted_msg["content"] = [
                {"type": "text", "text": msg.content or ""},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{msg.base64_image}"}
                }
            ]
        
        formatted_messages.append(formatted_msg)
    
    # API 요청 데이터 구성
    # 모델 ID를 우선적으로 사용
    model_id = kwargs.get("model_id", None)
    
    # model_id가 없으면 설정에서 가져오기 시도
    if not model_id:
        from backend.config.settings import settings
        if hasattr(settings, "llm") and hasattr(settings.llm, "local_llm_model_id"):
            model_id = settings.llm.local_llm_model_id
        else:
            # 디폴트 모델 ID
            model_id = "deepseek-r1-distill-qwen-7b"
    
    logger.info(f"사용하는 모델 ID: {model_id}")
    
    # URL 슬래시 정리 (중복 슬래시 방지)
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # OpenAI 호환 형식으로 요청 데이터 구성
    request_data = {
        "model": model_id,
        "messages": formatted_messages,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 1000)
    }
    
    # 도구가 있는 경우 추가
    if tools:
        request_data["tools"] = tools
        
    if tool_choice:
        request_data["tool_choice"] = tool_choice
    
    # LLM API 호출 (LM Studio 전용 엔드포인트 사용)
    # LM Studio는 OpenAI 호환 API를 사용함
    endpoint = "/v1/chat/completions"
    
    logger.info(f"LM Studio API 호출: {base_url}{endpoint}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # 타임아웃 감소
            response = await client.post(
                f"{base_url}{endpoint}",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"LM Studio API 성공적으로 호출됨")
                return response.json()
            else:
                logger.error(f"LM Studio API 오류: {response.status_code} {response.text}")
                raise Exception(f"LM Studio API 오류: {response.status_code} {response.text}")
    
    except httpx.ConnectError as e:
        logger.error(f"LM Studio 연결 오류: {str(e)}")
        raise Exception(f"LM Studio 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요: {base_url}")
    
    except httpx.TimeoutException as e:
        logger.error(f"LM Studio API 타임아웃: {str(e)}")
        raise Exception(f"LM Studio API 요청 타임아웃. 서버 응답이 너무 느립니다.")
        
    except Exception as e:
        logger.error(f"LM Studio API 호출 오류: {str(e)}")
        raise Exception(f"LM Studio API 호출 오류: {str(e)}")


def extract_tool_calls(response_data: Dict[str, Any]) -> List[ToolCall]:
    """
    API 응답에서 도구 호출 정보를 추출합니다.
    
    Args:
        response_data: API 응답 데이터
        
    Returns:
        도구 호출 목록
    """
    tool_calls = []
    
    # OpenAI API 형식 (LM Studio는 이 형식 사용)
    if (
        "choices" in response_data 
        and len(response_data["choices"]) > 0 
        and "message" in response_data["choices"][0]
        and "tool_calls" in response_data["choices"][0]["message"]
    ):
        for tc in response_data["choices"][0]["message"]["tool_calls"]:
            tool_calls.append(ToolCall(
                id=tc["id"],
                type=tc["type"],
                function=ToolCallFunction(
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                )
            ))
    
    # Ollama API 형식 (더 이상 사용하지 않음 - 참고용)
    elif (
        "message" in response_data
        and "tool_calls" in response_data["message"]
    ):
        for tc in response_data["message"]["tool_calls"]:
            tool_calls.append(ToolCall(
                id=tc.get("id", "0"),  # Ollama는 ID가 없을 수 있음
                type=tc.get("type", "function"),
                function=ToolCallFunction(
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                )
            ))
    
    return tool_calls


def extract_content(response_data: Dict[str, Any]) -> Optional[str]:
    """
    API 응답에서 컨텐츠를 추출합니다.
    
    Args:
        response_data: API 응답 데이터
        
    Returns:
        응답 컨텐츠
    """
    # OpenAI API 형식 (LM Studio는 이 형식 사용)
    if (
        "choices" in response_data 
        and len(response_data["choices"]) > 0 
        and "message" in response_data["choices"][0]
    ):
        content = response_data["choices"][0]["message"].get("content")
        
        # <think> 태그를 제거하는 처리
        if content and isinstance(content, str):
            # <think>...</think> 태그 제거
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            return content.strip()
            
        return content
    
    # Ollama API 형식 (더 이상 사용하지 않음 - 참고용)
    elif "message" in response_data:
        content = response_data.get("message", {}).get("content")
        
        # <think> 태그를 제거하는 처리
        if content and isinstance(content, str):
            # <think>...</think> 태그 제거
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            return content.strip()
            
        return content
    
    return None


async def generate_from_local_llm(messages: List[Dict[str, str]], **kwargs) -> str:
    """
    로컬 LLM(LM Studio)을 사용하여 텍스트를 생성합니다.
    
    Args:
        messages: 메시지 목록 (OpenAI 형식)
        **kwargs: 추가 매개변수
        
    Returns:
        생성된 텍스트
    """
    from backend.config.settings import settings
    from .models.agent import Message
    
    # LM Studio URL 설정
    base_url = settings.llm.get("local_llm_base_url", DEFAULT_LM_STUDIO_URL)
    
    # 메시지 변환
    formatted_messages = []
    for msg in messages:
        formatted_messages.append(Message(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            name=msg.get("name")
        ))
    
    # API 호출
    response_data = await call_lm_studio(
        messages=formatted_messages,
        base_url=base_url,
        model_id=kwargs.get("model_id", settings.llm.get("local_llm_model_id")),
        temperature=kwargs.get("temperature", settings.llm.get("local_llm_temperature", 0.7)),
        max_tokens=kwargs.get("max_tokens", settings.llm.get("local_llm_max_tokens", 1000))
    )
    
    # 응답 컨텐츠 추출
    content = extract_content(response_data)
    
    return content if content else ""
