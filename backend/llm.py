"""
LLM 연동 모듈

다양한 LLM API와의 통신을 처리하는 클래스를 제공합니다.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from backend.models.agent import Message, ToolCall
from backend.models.enums import ToolChoice

logger = logging.getLogger(__name__)


class ChatCompletionResponse(BaseModel):
    """챗 완성 응답 모델"""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    

class LLM:
    """LLM 래퍼 클래스
    
    다양한 LLM API와의 통신을 처리합니다.
    """
    
    def __init__(self, config_name: str = "default"):
        """
        LLM 인스턴스 초기화
        
        Args:
            config_name: 설정 프로필 이름
        """
        self.config_name = config_name
        logger.info(f"LLM({config_name}) 인스턴스 초기화됨")
    
    async def ask(
        self, 
        messages: List[Message], 
        system_msgs: Optional[List[Message]] = None,
        **kwargs
    ) -> str:
        """
        메시지 목록을 LLM에 전송하고 텍스트 응답을 받음
        
        Args:
            messages: 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            **kwargs: 추가 LLM 옵션
            
        Returns:
            LLM의 텍스트 응답
            
        Raises:
            ValueError: 메시지 형식 오류 시
        """
        # 실제 구현에서는 여기서 API 호출
        # 지금은 임시로 메시지를 에코만 함
        if not messages:
            raise ValueError("메시지가 제공되지 않았습니다")
        
        last_msg = messages[-1]
        if not isinstance(last_msg, Message):
            raise ValueError(f"마지막 메시지가 Message 타입이 아닙니다: {type(last_msg)}")
        
        logger.info(f"LLM 요청: {len(messages)}개 메시지")
        
        # 임시 응답 로직 (실제 구현에서는 API 호출)
        return f"메시지 '{last_msg.content}'에 대한 응답"
    
    async def ask_tool(
        self, 
        messages: List[Message], 
        system_msgs: Optional[List[Message]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[ToolChoice] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        메시지 목록을 LLM에 전송하고 도구 호출 응답을 받음
        
        Args:
            messages: 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            tools: 도구 정의 목록 (선택 사항)
            tool_choice: 도구 선택 모드 (선택 사항)
            **kwargs: 추가 LLM 옵션
            
        Returns:
            LLM의 응답 (텍스트 또는 도구 호출)
            
        Raises:
            ValueError: 메시지 형식 오류 시
        """
        # 실제 구현에서는 여기서 API 호출
        # 지금은 임시로 응답만 생성
        if not messages:
            raise ValueError("메시지가 제공되지 않았습니다")
        
        last_msg = messages[-1]
        if not isinstance(last_msg, Message):
            raise ValueError(f"마지막 메시지가 Message 타입이 아닙니다: {type(last_msg)}")
        
        logger.info(f"LLM 도구 요청: {len(messages)}개 메시지, {len(tools) if tools else 0}개 도구")
        
        # 임시 응답 로직 (실제 구현에서는 API 호출)
        response = ChatCompletionResponse(
            content=f"메시지 '{last_msg.content}'에 대한 응답",
            tool_calls=[]  # 실제 구현에서는 필요한 경우 도구 호출 추가
        )
        
        return response