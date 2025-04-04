"""
LLMNightRun 스키마 정의 모듈

에이전트 및 LLM 상호작용에 필요한 데이터 구조를 정의합니다.
"""

import base64
import enum
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


# 기본 타입 정의
ROLE_TYPE = Literal["user", "assistant", "system", "tool"]
TOOL_CHOICE_TYPE = Union[Literal["none", "auto", "required"], Dict[str, Any]]


class AgentState(str, enum.Enum):
    """에이전트 상태"""
    IDLE = "idle"           # 대기 상태
    RUNNING = "running"     # 실행 중
    FINISHED = "finished"   # 작업 완료
    ERROR = "error"         # 오류 발생


class ToolChoice(str, enum.Enum):
    """도구 선택 모드"""
    NONE = "none"           # 도구 사용 안함
    AUTO = "auto"           # 필요시 자동 선택
    REQUIRED = "required"   # 항상 도구 사용 필수


class ToolSchema(BaseModel):
    """도구 스키마 정의"""
    type: str = "function"
    function: Dict[str, Any]


class ToolCallFunction(BaseModel):
    """도구 호출 함수 정보"""
    name: str
    arguments: str = "{}"


class ToolCall(BaseModel):
    """도구 호출 정보"""
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")
    type: str = "function"
    function: ToolCallFunction


class Message(BaseModel):
    """대화 메시지"""
    role: ROLE_TYPE
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

    @classmethod
    def from_tool_calls(cls, content: Optional[str], tool_calls: List[ToolCall]) -> "Message":
        """도구 호출 메시지 생성"""
        return cls(role="assistant", content=content, tool_calls=tool_calls)


class Memory(BaseModel):
    """에이전트 메모리"""
    messages: List[Message] = Field(default_factory=list)
    max_history: int = 100

    def add_message(self, message: Message) -> None:
        """메시지 추가"""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def clear(self) -> None:
        """메모리 초기화"""
        self.messages.clear()


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