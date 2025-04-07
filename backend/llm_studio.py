"""
LM Studio 로컬 LLM 연동 모듈

LM Studio로 실행되는 로컬 LLM과의 통신을 처리하는 기능을 제공합니다.
"""

import httpx
import logging
from typing import Dict, List, Optional, Any

from backend.models.agent import Message, ToolCall, ToolCallFunction
from backend.models.enums import LLMType

logger = logging.getLogger(__name__)

DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:11434"


async def call_lm_studio(
    messages: List[Message],
    system_msgs: Optional[List[Message]] = None,
    base_url: str = DEFAULT_LM_STUDIO_URL,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
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
            
        if msg.base64_image is not None:
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
    request_data = {
        "model": "local-model",  # LM Studio에서는 이 필드가 실제로 사용되지 않음
        "messages": formatted_messages,
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 1000),
        "stream": False
    }
    
    # 도구가 있는 경우 추가
    if tools:
        request_data["tools"] = tools
        
    if tool_choice:
        request_data["tool_choice"] = tool_choice
    
    # LM Studio API 호출
    logger.info(f"Local LLM API 호출: {base_url}/api/chat")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return response.json()
    
    except Exception as e:
        logger.error(f"LM Studio API 호출 오류: {str(e)}")
        raise e


def extract_tool_calls(response_data: Dict[str, Any]) -> List[ToolCall]:
    """
    API 응답에서 도구 호출 정보를 추출합니다.
    
    Args:
        response_data: API 응답 데이터
        
    Returns:
        도구 호출 목록
    """
    tool_calls = []
    
    # Ollama API 형식
    if (
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
    
    # OpenAI API 형식 (호환성)
    elif (
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
    
    return tool_calls


def extract_content(response_data: Dict[str, Any]) -> Optional[str]:
    """
    API 응답에서 컨텐츠를 추출합니다.
    
    Args:
        response_data: API 응답 데이터
        
    Returns:
        응답 컨텐츠
    """
    # Ollama API 형식
    if "message" in response_data:
        content = response_data.get("message", {}).get("content")
        
        # <think> 태그를 제거하는 처리
        if content and isinstance(content, str):
            # <think>...</think> 태그 제거
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            return content.strip()
            
        return content
    
    # OpenAI API 형식 (호환성)
    elif (
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
    
    return None
