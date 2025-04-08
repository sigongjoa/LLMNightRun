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
    name: str = Field(...)
    arguments: str = Field(default="{}")


class ToolCall(BaseModel):
    """도구 호출 정보"""
    id: str
    type: str = "function"
    function: ToolCallFunction = Field(...)


import uuid

class Message(BaseModel):
    """대화 메시지"""
    role: str = Field(...)  # user, assistant, system, tool
    content: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None) 
    tool_call_id: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)  # Base64 인코딩된 이미지
    id: str = Field(default_factory=lambda: f"{uuid.uuid4().hex}")  # 고유 메시지 ID

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
    def from_tool_calls(cls, content: Optional[str], tool_calls: List[ToolCall]) -> "Message":
        """도구 호출을 포함하는 어시스턴트 메시지 생성"""
        return cls(
            role="assistant", 
            content=content, 
            tool_calls=tool_calls
        )

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
    session_id: str = Field(...)
    agent_type: str = Field(...)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    status: str = Field(default="running")
    total_steps: int = Field(default=0)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentLog(IdentifiedModel):
    """에이전트 로그 모델"""
    session_id: str = Field(...)
    step: int = Field(...)
    phase: AgentPhase = Field(...)
    timestamp: Optional[datetime] = Field(default=None)
    input_data: Optional[Dict[str, Any]] = Field(default=None)
    output_data: Optional[Dict[str, Any]] = Field(default=None)
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None)
    error: Optional[str] = Field(default=None)


class AgentRequest(BaseModel):
    """에이전트 요청 모델"""
    prompt: str = Field(...)
    workspace: Optional[str] = Field(default=None)
    max_steps: Optional[int] = Field(default=None)


class AgentResponse(BaseModel):
    """에이전트 응답 모델"""
    agent_id: str = Field(...)
    state: AgentState = Field(...)
    messages: List[Dict] = Field(default_factory=list)
    result: str = Field(default="")


class ToolResult(BaseModel):
    """도구 실행 결과"""
    output: str = Field(...)
    error: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    def __str__(self) -> str:
        """문자열 변환"""
        if self.error:
            return f"Error: {self.error}"
        return self.output


class FunctionDefinition(BaseModel):
    """함수 정의"""
    name: str = Field(...)
    description: str = Field(...)
    parameters: Dict[str, Any] = Field(default_factory=dict)