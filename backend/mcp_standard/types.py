"""
Model Context Protocol (MCP) 타입 정의

이 모듈은 MCP 표준에 따른 타입 정의를 제공합니다.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union, Literal
from pydantic import BaseModel, Field, HttpUrl, AnyUrl


class MessageRole(str, Enum):
    """메시지 역할"""
    USER = "user"
    ASSISTANT = "assistant"


class ContentType(str, Enum):
    """컨텐츠 타입"""
    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"


class TextContent(BaseModel):
    """텍스트 컨텐츠"""
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    """이미지 컨텐츠"""
    type: Literal["image"] = "image"
    data: str  # Base64 인코딩된 이미지 데이터
    mimeType: str


class ResourceRef(BaseModel):
    """리소스 참조"""
    uri: str
    text: Optional[str] = None
    mimeType: Optional[str] = None


class ResourceContent(BaseModel):
    """리소스 컨텐츠"""
    type: Literal["resource"] = "resource"
    resource: ResourceRef


class PromptMessage(BaseModel):
    """프롬프트 메시지"""
    role: MessageRole
    content: Union[TextContent, ImageContent, ResourceContent]


class MCPResource(BaseModel):
    """MCP 리소스 정의"""
    uri: Optional[str] = None
    uriTemplate: Optional[str] = None
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class ResourceContent(BaseModel):
    """리소스 컨텐츠"""
    uri: str
    text: Optional[str] = None
    blob: Optional[str] = None  # Base64 인코딩
    mimeType: Optional[str] = None


class ReadResourceResult(BaseModel):
    """리소스 읽기 결과"""
    contents: List[ResourceContent]


class MCPToolParameter(BaseModel):
    """도구 파라미터 정의"""
    name: str
    description: Optional[str] = None
    type: str
    required: bool = False


class MCPTool(BaseModel):
    """MCP 도구 정의"""
    name: str
    description: Optional[str] = None
    inputSchema: Dict[str, Any]  # JSON Schema


class ToolContent(BaseModel):
    """도구 실행 결과 컨텐츠"""
    type: ContentType
    text: Optional[str] = None
    data: Optional[str] = None  # Base64 인코딩
    mimeType: Optional[str] = None
    resource: Optional[ResourceRef] = None


class ToolCallResult(BaseModel):
    """도구 호출 결과"""
    content: List[ToolContent]
    isError: bool = False


class PromptArgument(BaseModel):
    """프롬프트 인자"""
    name: str
    description: Optional[str] = None
    required: bool = False


class MCPPrompt(BaseModel):
    """MCP 프롬프트 정의"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[PromptArgument]] = None


class GetPromptResult(BaseModel):
    """프롬프트 가져오기 결과"""
    messages: List[PromptMessage]
    description: Optional[str] = None


class ModelHint(BaseModel):
    """모델 힌트"""
    name: Optional[str] = None


class ModelPreferences(BaseModel):
    """모델 선호도"""
    hints: Optional[List[ModelHint]] = None
    costPriority: Optional[float] = None  # 0-1
    speedPriority: Optional[float] = None  # 0-1
    intelligencePriority: Optional[float] = None  # 0-1


class SamplingCreateMessageRequest(BaseModel):
    """샘플링 메시지 생성 요청"""
    messages: List[PromptMessage]
    modelPreferences: Optional[ModelPreferences] = None
    systemPrompt: Optional[str] = None
    includeContext: Optional[Literal["none", "thisServer", "allServers"]] = "none"
    temperature: Optional[float] = 0.7
    maxTokens: int
    stopSequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class LogLevel(str, Enum):
    """로그 레벨"""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class LoggingMessage(BaseModel):
    """로깅 메시지"""
    level: LogLevel
    logger: Optional[str] = None
    data: Any
