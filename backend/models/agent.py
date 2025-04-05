"""
에이전트 관련 모델 정의 모듈

에이전트, 메시지, 도구 호출 등의 데이터 구조를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from .base import IdentifiedModel
from .enums import AgentPhase, AgentState


class ToolCallFunction(BaseModel):
    """도구 호출 함수 정보"""
    name: str
    arguments: str = "{}"


class ToolCall(BaseModel):
    """도구 호출 정보"""
    id: str
    type: str = "function"
    function: ToolCallFunction


class Message(BaseModel):
    """대화 메시지"""
    role: str  # user, assistant, system, tool
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    base64_image: Optional[str] = None  # Base64 인코딩된 이미지

    @classmethod
    def user_message(cls, content: str, base64_image: Optional[str] = None) -> "Message":
        """사용자 메시지 생성"""
        return cls(role="user", content=content, base64_image=base64_image)

    @classmethod
    def assistant_message(cls, content: str) -> "Message":
        """어시스턴트 메시지 생성"""
        return cls(role="assistant", content=content)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """시스템 메시지 생성"""
        return cls(role="system", content=content)

    @classmethod
    def tool_message(cls, content: str, tool_call_id: str = "", name: str = "", base64_image: Optional[str] = None) -> "Message":
        """도구 응답 메시지 생성"""
        return cls(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            base64_image=base64_image,
        )


class AgentSession(IdentifiedModel):
    """에이전트 세션 모델"""
    session_id: str
    agent_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "running"
    total_steps: int = 0
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentLog(IdentifiedModel):
    """에이전트 로그 모델"""
    session_id: str
    step: int
    phase: AgentPhase
    timestamp: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class AgentRequest(BaseModel):
    """에이전트 요청 모델"""
    prompt: str
    workspace: Optional[str] = None
    max_steps: Optional[int] = None


class AgentResponse(BaseModel):
    """에이전트 응답 모델"""
    agent_id: str
    state: AgentState
    messages: List[Dict] = Field(default_factory=list)
    result: str = ""


class ToolResult(BaseModel):
    """도구 실행 결과"""
    output: str
    error: Optional[str] = None
    base64_image: Optional[str] = None

    def __str__(self) -> str:
        """문자열 변환"""
        if self.error:
            return f"Error: {self.error}"
        return self.output


class FunctionDefinition(BaseModel):
    """함수 정의"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)