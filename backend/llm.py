"""
LLM 연동 모듈

다양한 LLM API와의 통신을 처리하는 클래스를 제공합니다.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from backend.models.agent import Message, ToolCall
from backend.models.enums import ToolChoice, LLMType
from backend.llm_studio import call_lm_studio, extract_content, extract_tool_calls

logger = logging.getLogger(__name__)


class ChatCompletionResponse(BaseModel):
    """챗 완성 응답 모델"""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    

class LLM:
    """LLM 래퍼 클래스
    
    다양한 LLM API와의 통신을 처리합니다.
    """
    
    def __init__(
        self, 
        config_name: str = "default", 
        llm_type: LLMType = LLMType.OPENAI_API, 
        base_url: Optional[str] = None
    ):
        """
        LLM 인스턴스 초기화
        
        Args:
            config_name: 설정 프로필 이름
            llm_type: LLM 유형 (OPENAI_API, CLAUDE_API, LOCAL_LLM 등)
            base_url: LLM API 기본 URL (로컬 LLM의 경우)
        """
        self.config_name = config_name
        self.llm_type = llm_type
        self.base_url = base_url
        logger.info(f"LLM({config_name}, {llm_type}) 인스턴스 초기화됨")
    
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
        if not messages:
            raise ValueError("메시지가 제공되지 않았습니다")
        
        last_msg = messages[-1]
        if not isinstance(last_msg, Message):
            raise ValueError(f"마지막 메시지가 Message 타입이 아닙니다: {type(last_msg)}")
        
        logger.info(f"LLM 요청: {len(messages)}개 메시지")
        
        # LM Studio 로컬 LLM 처리
        if self.llm_type == LLMType.LOCAL_LLM and self.base_url:
            try:
                # LM Studio API 호출
                response_data = await call_lm_studio(
                    messages=messages,
                    system_msgs=system_msgs,
                    base_url=self.base_url,
                    **kwargs
                )
                
                # 응답 컨텐츠 추출
                content = extract_content(response_data)
                if content is not None:
                    return content
                
                logger.error(f"LLM API 응답 형식 오류: {response_data}")
                return "LLM 응답을 처리할 수 없습니다."
                
            except Exception as e:
                logger.error(f"LLM API 호출 오류: {str(e)}")
                return f"LLM API 오류: {str(e)}"
        
        # 임시 응답 로직 (다른 LLM 유형일 경우)
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
        if not messages:
            raise ValueError("메시지가 제공되지 않았습니다")
        
        last_msg = messages[-1]
        if not isinstance(last_msg, Message):
            raise ValueError(f"마지막 메시지가 Message 타입이 아닙니다: {type(last_msg)}")
        
        logger.info(f"LLM 도구 요청: {len(messages)}개 메시지, {len(tools) if tools else 0}개 도구")
        
        # LM Studio 로컬 LLM 처리
        if self.llm_type == LLMType.LOCAL_LLM and self.base_url:
            try:
                # 도구 선택 모드 문자열 변환
                tool_choice_str = None
                if tool_choice:
                    tool_choice_str = tool_choice.value
                
                # LM Studio API 호출
                response_data = await call_lm_studio(
                    messages=messages,
                    system_msgs=system_msgs,
                    base_url=self.base_url,
                    tools=tools,
                    tool_choice=tool_choice_str,
                    **kwargs
                )
                
                # 응답 컨텐츠와 도구 호출 추출
                content = extract_content(response_data)
                tool_calls = extract_tool_calls(response_data)
                
                return ChatCompletionResponse(
                    content=content,
                    tool_calls=tool_calls if tool_calls else None
                )
                
            except Exception as e:
                logger.error(f"LLM API 호출 오류: {str(e)}")
                return ChatCompletionResponse(content=f"LLM API 오류: {str(e)}")
        
        # 임시 응답 로직 (다른 LLM 유형일 경우)
        response = ChatCompletionResponse(
            content=f"메시지 '{last_msg.content}'에 대한 응답",
            tool_calls=[]
        )
        
        return response