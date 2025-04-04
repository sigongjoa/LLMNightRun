"""
LLMNightRun LLM 인터페이스 모듈

다양한 LLM API와의 통신을 추상화하는 인터페이스를 제공합니다.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

import openai
from pydantic import BaseModel, Field

from backend.config import config
from backend.logger import get_logger
from backend.schema import Message, ToolCall, ToolSchema, TOOL_CHOICE_TYPE


logger = get_logger(__name__)


class LLMResponse(BaseModel):
    """LLM 응답 모델"""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class LLM:
    """LLM 인터페이스
    
    다양한 LLM 서비스와의 통신을 추상화합니다.
    OpenAI API 및 Claude API를 지원합니다.
    """
    
    def __init__(self, config_name: Optional[str] = None):
        """LLM 인스턴스 초기화
        
        Args:
            config_name: 설정 이름 (선택 사항)
        """
        self.openai_api_key = config.llm.openai_api_key
        self.claude_api_key = config.llm.claude_api_key
        self.model = config.llm.model_name
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
        self.timeout = config.llm.timeout
        
        # 설정 이름이 지정된 경우 추가 설정 로드
        if config_name:
            # 추가 설정 로직을 넣을 수 있습니다
            pass
        
        # OpenAI API 키 설정
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # 모델에 맞게 프로바이더 결정
        if self.model.startswith("gpt"):
            self.provider = "openai"
        elif self.model.startswith("claude"):
            self.provider = "anthropic"
        else:
            self.provider = "openai"  # 기본값
            logger.warning(f"알 수 없는 모델: {self.model}, OpenAI로 기본 설정됨")
    
    async def ask(
        self, 
        messages: List[Message], 
        system_msgs: Optional[List[Message]] = None
    ) -> str:
        """LLM에 질문하고 텍스트 응답을 받습니다
        
        Args:
            messages: 대화 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            
        Returns:
            str: LLM 응답 텍스트
            
        Raises:
            ValueError: 필수 API 키가 없거나 응답이 없는 경우
        """
        response = await self.ask_tool(messages, system_msgs)
        return response.content or ""
    
    async def ask_tool(
        self,
        messages: List[Message],
        system_msgs: Optional[List[Message]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: TOOL_CHOICE_TYPE = "auto",
    ) -> LLMResponse:
        """LLM에 도구 기능을 사용하여 질문
        
        Args:
            messages: 대화 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            tools: 사용 가능한 도구 정의 목록 (선택 사항)
            tool_choice: 도구 선택 모드
            
        Returns:
            LLMResponse: 응답 및 도구 호출 정보
            
        Raises:
            ValueError: 필수 API 키가 없거나 응답이 없는 경우
        """
        if self.provider == "openai":
            result = await self._call_openai(messages, system_msgs, tools, tool_choice)
        elif self.provider == "anthropic":
            result = await self._call_claude(messages, system_msgs, tools, tool_choice)
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {self.provider}")
        
        return result
    
    async def _call_openai(
        self,
        messages: List[Message],
        system_msgs: Optional[List[Message]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: TOOL_CHOICE_TYPE = "auto",
    ) -> LLMResponse:
        """OpenAI API 호출
        
        Args:
            messages: 대화 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            tools: 사용 가능한 도구 정의 목록 (선택 사항)
            tool_choice: 도구 선택 모드
            
        Returns:
            LLMResponse: 응답 및 도구 호출 정보
            
        Raises:
            ValueError: API 키가 없거나 응답이 없는 경우
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
        
        # 메시지 변환
        formatted_messages = []
        
        # 시스템 메시지 추가
        if system_msgs:
            for msg in system_msgs:
                formatted_messages.append(self._format_message(msg))
        
        # 대화 메시지 추가
        for msg in messages:
            formatted_messages.append(self._format_message(msg))
        
        # API 호출 인자 구성
        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }
        
        # 도구 관련 인자 추가
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        try:
            # API 호출
            response = await openai.ChatCompletion.acreate(**kwargs)
            
            # 응답 파싱
            message = response.choices[0].message
            content = message.get("content")
            
            # 도구 호출 정보 파싱
            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    tool_calls.append(
                        ToolCall(
                            id=tc["id"],
                            type=tc["type"],
                            function=tc["function"],
                        )
                    )
            
            return LLMResponse(content=content, tool_calls=tool_calls)
        
        except Exception as e:
            logger.error(f"OpenAI API 호출 오류: {str(e)}")
            raise
    
    async def _call_claude(
        self,
        messages: List[Message],
        system_msgs: Optional[List[Message]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: TOOL_CHOICE_TYPE = "auto",
    ) -> LLMResponse:
        """Claude API 호출
        
        Args:
            messages: 대화 메시지 목록
            system_msgs: 시스템 메시지 목록 (선택 사항)
            tools: 사용 가능한 도구 정의 목록 (선택 사항)
            tool_choice: 도구 선택 모드
            
        Returns:
            LLMResponse: 응답 및 도구 호출 정보
            
        Raises:
            ValueError: API 키가 없거나 응답이 없는 경우
            NotImplementedError: Claude 도구 호출이 구현되지 않은 경우
        """
        if not self.claude_api_key:
            raise ValueError("Claude API 키가 설정되지 않았습니다")
        
        if tools:
            # Claude API의 도구 호출은 미구현 상태에서는 OpenAI로 폴백
            logger.warning("Claude의 도구 호출 기능은 현재 지원되지 않습니다. OpenAI로 폴백합니다.")
            # OpenAI API 키가 있으면 폴백
            if self.openai_api_key:
                self.provider = "openai"
                temp_model = self.model
                self.model = "gpt-4"
                result = await self._call_openai(messages, system_msgs, tools, tool_choice)
                self.model = temp_model
                self.provider = "anthropic"
                return result
            raise NotImplementedError("Claude의 도구 호출 기능은 현재 지원되지 않습니다")
        
        # 메시지 변환 로직 구현 필요
        # ...
        
        # Claude API 연동 코드 (미구현)
        raise NotImplementedError("Claude API 연동이 아직 구현되지 않았습니다")
    
    def _format_message(self, message: Message) -> Dict[str, Any]:
        """메시지 객체를 API 호출용 형식으로 변환
        
        Args:
            message: 메시지 객체
            
        Returns:
            Dict[str, Any]: API 호출용 메시지 형식
        """
        result = {"role": message.role}
        
        # 내용 추가
        if message.content is not None:
            result["content"] = message.content
        
        # 도구 정보 추가
        if message.tool_calls:
            result["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": tc.function.dict()}
                for tc in message.tool_calls
            ]
        
        # 도구 응답 정보 추가
        if message.role == "tool":
            result["tool_call_id"] = message.tool_call_id
            result["name"] = message.name
        
        return result