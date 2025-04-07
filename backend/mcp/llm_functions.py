"""
MCP LLM 함수 구현 모듈

로컬 LLM과 MCP를 연동하기 위한 함수 구현을 제공합니다.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union

from .local_llm import LocalLLMTool

logger = logging.getLogger("mcp.llm_functions")

# LLM 도구 인스턴스 생성
local_llm_tool = LocalLLMTool()


# LLM 세션 관리 함수
async def llm_create_session(
    base_url: str = "http://localhost:1234/v1",
    api_key: str = "",
    model: str = "local-model",
    context_length: int = 4096,
    additional_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """로컬 LLM 세션 생성
    
    Args:
        base_url: LLM API 기본 URL
        api_key: API 키
        model: 모델 이름
        context_length: 컨텍스트 길이
        additional_config: 추가 구성 정보
        
    Returns:
        Dict[str, Any]: 세션 생성 결과
    """
    try:
        # 구성 데이터 준비
        config = {
            "baseUrl": base_url,
            "apiKey": api_key,
            "model": model,
            "contextLength": context_length
        }
        
        # 추가 구성 병합
        if additional_config:
            config.update(additional_config)
        
        # 세션 초기화
        session_id = await local_llm_tool.initialize_session(config)
        
        # 세션 정보 반환
        session_info = local_llm_tool.get_session_info(session_id)
        if session_info.get("success", False):
            return {
                "success": True,
                "session_id": session_id,
                "info": session_info
            }
        else:
            return {
                "success": False,
                "error": session_info.get("error", "Failed to get session info"),
                "session_id": session_id
            }
            
    except Exception as e:
        logger.error(f"Error creating LLM session: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def llm_list_sessions() -> Dict[str, Any]:
    """활성 LLM 세션 목록 조회
    
    Returns:
        Dict[str, Any]: 세션 목록
    """
    try:
        return local_llm_tool.list_sessions()
    except Exception as e:
        logger.error(f"Error listing LLM sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "sessions": [],
            "count": 0
        }

def llm_get_session(session_id: str) -> Dict[str, Any]:
    """LLM 세션 정보 조회
    
    Args:
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 세션 정보
    """
    try:
        return local_llm_tool.get_session_info(session_id)
    except Exception as e:
        logger.error(f"Error getting LLM session info: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def llm_delete_session(session_id: str) -> Dict[str, Any]:
    """LLM 세션 삭제
    
    Args:
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    try:
        return local_llm_tool.delete_session(session_id)
    except Exception as e:
        logger.error(f"Error deleting LLM session: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def llm_get_history(session_id: str, count: int = None) -> Dict[str, Any]:
    """LLM 세션 히스토리 조회
    
    Args:
        session_id: 세션 ID
        count: 조회할 기록 수
        
    Returns:
        Dict[str, Any]: 히스토리 정보
    """
    try:
        return local_llm_tool.get_session_history(session_id, count)
    except Exception as e:
        logger.error(f"Error getting LLM session history: {e}")
        return {
            "success": False,
            "error": str(e),
            "history": [],
            "count": 0
        }

async def llm_test_connection(session_id: str) -> Dict[str, Any]:
    """LLM 연결 테스트
    
    Args:
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 테스트 결과
    """
    try:
        return await local_llm_tool.test_connection(session_id)
    except Exception as e:
        logger.error(f"Error testing LLM connection: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# LLM 생성 함수
async def llm_generate(
    session_id: str,
    prompt: Union[str, List[Dict[str, Any]]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop_sequences: List[str] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """LLM에 텍스트 생성 요청
    
    Args:
        session_id: 세션 ID
        prompt: 프롬프트 (문자열 또는 메시지 목록)
        max_tokens: 최대 생성 토큰 수
        temperature: 온도 (0.0 ~ 2.0)
        top_p: 상위 확률 샘플링 (0.0 ~ 1.0)
        frequency_penalty: 빈도 페널티 (0.0 ~ 2.0)
        presence_penalty: 존재 페널티 (0.0 ~ 2.0)
        stop_sequences: 정지 시퀀스 목록
        stream: 스트리밍 여부 (현재 비활성화)
        
    Returns:
        Dict[str, Any]: 생성 결과
    """
    try:
        # 생성 옵션 설정
        options = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }
        
        if stop_sequences:
            options["stop"] = stop_sequences
        
        # 스트리밍 비활성화 (MCP에서는 현재 일관적인 응답 형식 유지)
        options["stream"] = False
        
        # 완성 생성 요청
        result = await local_llm_tool.generate_completion(session_id, prompt, options)
        return result
        
    except Exception as e:
        logger.error(f"Error generating LLM completion: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def llm_chat(
    session_id: str,
    messages: List[Dict[str, Any]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop_sequences: List[str] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """LLM 채팅 완성 요청
    
    Args:
        session_id: 세션 ID
        messages: 채팅 메시지 목록
        max_tokens: 최대 생성 토큰 수
        temperature: 온도 (0.0 ~ 2.0)
        top_p: 상위 확률 샘플링 (0.0 ~ 1.0)
        frequency_penalty: 빈도 페널티 (0.0 ~ 2.0)
        presence_penalty: 존재 페널티 (0.0 ~ 2.0)
        stop_sequences: 정지 시퀀스 목록
        stream: 스트리밍 여부 (현재 비활성화)
        
    Returns:
        Dict[str, Any]: 채팅 결과
    """
    try:
        # 생성 옵션 설정
        options = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }
        
        if stop_sequences:
            options["stop"] = stop_sequences
        
        # 스트리밍 비활성화 (MCP에서는 현재 일관적인 응답 형식 유지)
        options["stream"] = False
        
        # 완성 생성 요청
        result = await local_llm_tool.generate_completion(session_id, messages, options)
        return result
        
    except Exception as e:
        logger.error(f"Error generating LLM chat completion: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# MCP 함수 매핑 - 함수 이름을 함수 객체에 매핑
MCP_LLM_FUNCTION_IMPLEMENTATIONS = {
    # LLM 세션 관리 함수
    "llm_create_session": llm_create_session,
    "llm_list_sessions": llm_list_sessions,
    "llm_get_session": llm_get_session,
    "llm_delete_session": llm_delete_session,
    "llm_get_history": llm_get_history,
    "llm_test_connection": llm_test_connection,
    
    # LLM 생성 함수
    "llm_generate": llm_generate,
    "llm_chat": llm_chat
}
