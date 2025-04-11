"""
에이전트 관련 모델 클래스 정의
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    """
    채팅 메시지를 나타내는 클래스
    """
    role: str
    content: str = ""
    name: Optional[str] = None
    base64_image: Optional[str] = None

class ToolCallFunction(BaseModel):
    """
    도구 호출 함수 정보
    """
    name: str
    arguments: str

class ToolCall(BaseModel):
    """
    도구 호출 정보
    """
    id: str
    type: str
    function: ToolCallFunction
