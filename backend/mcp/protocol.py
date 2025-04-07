"""
Model Context Protocol (MCP) 프로토콜 정의

MCP는 LLM에 컨텍스트를 제공하는 방법을 표준화하는 개방형 프로토콜입니다.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field


class MCPMessageType(str, Enum):
    """MCP 메시지 타입"""
    FUNCTION_CALL = "function_call"
    FUNCTION_RESPONSE = "function_response"
    CONTEXT_UPDATE = "context_update"
    ERROR = "error"


class MCPFunctionCall(BaseModel):
    """MCP 함수 호출 요청 모델"""
    name: str
    arguments: Dict[str, Any]
    call_id: str


class MCPFunctionResponse(BaseModel):
    """MCP 함수 응답 모델"""
    call_id: str
    result: Any
    status: str = "success"
    error: Optional[str] = None


class MCPContextUpdate(BaseModel):
    """컨텍스트 업데이트 모델"""
    context_id: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class MCPError(BaseModel):
    """에러 응답 모델"""
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


class MCPMessage(BaseModel):
    """MCP 메시지 기본 모델"""
    type: MCPMessageType
    content: Union[MCPFunctionCall, MCPFunctionResponse, MCPContextUpdate, MCPError]
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    version: str = "1.0"
