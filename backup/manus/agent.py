"""
Manus 에이전트

LM Studio와 Model Context Protocol(MCP)을 사용하여 로컬 LLM 기반 에이전트를 구현합니다.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import asyncio

from backend.models.agent import Message, ToolCall, ToolCallFunction
from backend.models.enums import LLMType, ToolChoice
from backend.llm import LLM, ChatCompletionResponse

logger = logging.getLogger(__name__)

class ManusAgent:
    """
    Manus 에이전트 클래스
    
    LLM과 MCP를 연동하여 지능형 에이전트 기능을 제공합니다.
    """
    
    def __init__(
        self, 
        llm_type: LLMType = LLMType.LOCAL_LLM,
        llm_base_url: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        """
        Manus 에이전트 초기화
        
        Args:
            llm_type: LLM 유형 (기본값: LOCAL_LLM)
            llm_base_url: LLM API 서버 URL (기본값: None, 설정에서 가져옴)
            model_id: 사용할 모델 ID (기본값: None, 설정에서 가져옴)
        """
        self.llm = LLM(config_name="manus", llm_type=llm_type, base_url=llm_base_url)
        self.model_id = model_id
        self.conversation_history = []
        self.system_messages = []
        
        logger.info(f"Manus 에이전트 초기화됨 - LLM 타입: {llm_type}, URL: {llm_base_url}, 모델 ID: {model_id}")
        
        # 기본 시스템 메시지 설정
        self._set_default_system_message()
    
    def _set_default_system_message(self):
        """기본 시스템 메시지 설정"""
        self.system_messages = [
            Message(
                role="system",
                content=(
                    "당신은 Manus라는 이름의 AI 에이전트입니다. "
                    "개발자를 돕는 역할을 합니다. "
                    "코드 작성, 디버깅, 오류 해결 등의 개발 관련 작업을 지원합니다.\n\n"
                    "제공된 파일 시스템 도구를 활용하여 파일을 읽고 쓸 수 있습니다:\n"
                    "1. read_file: 파일 내용을 읽습니다.\n"
                    "2. write_file: 파일에 내용을 씁니다.\n"
                    "3. list_directory: 디렉토리 내용을 나열합니다.\n\n"
                    "사용자의 요청에 성실하게 응답하세요."
                )
            )
        ]
    
    async def process_message(
        self, 
        user_message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_turns: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        사용자 메시지를 처리하고 응답 생성
        
        Args:
            user_message: 사용자 입력 메시지
            tools: 사용 가능한 도구 목록 (기본값: None)
            max_turns: 최대 도구 호출 회수 (기본값: 5)
            
        Returns:
            응답 텍스트와 도구 호출 기록
        """
        # 사용자 메시지 추가
        self.conversation_history.append(Message(role="user", content=user_message))
        
        # 도구 없이 처리해야 할 경우
        if not tools:
            response = await self.llm.ask(
                messages=self.conversation_history,
                system_msgs=self.system_messages,
                model_id=self.model_id
            )
            
            self.conversation_history.append(Message(role="assistant", content=response))
            return response, []
        
        # 도구 사용 처리
        tool_calls_history = []
        current_turn = 0
        final_response = None
        
        while current_turn < max_turns:
            # 로그에 현재 턴과 대화 기록 길이 기록
            logger.info(f"도구 처리 턴 {current_turn+1}/{max_turns}, 대화 길이: {len(self.conversation_history)}")
            
            # LLM에 도구 사용 요청
            response: ChatCompletionResponse = await self.llm.ask_tool(
                messages=self.conversation_history,
                system_msgs=self.system_messages,
                tools=tools,
                tool_choice=ToolChoice.AUTO,
                model_id=self.model_id
            )
            
            # 도구 호출 없으면 완료
            if not response.tool_calls:
                final_response = response.content
                break
            
            # 도구 호출 있으면 처리
            tool_calls = response.tool_calls
            
            # 로그에 도구 호출 정보 기록
            logger.info(f"도구 호출: {len(tool_calls)}개")
            
            # 도구 호출 응답 메시지 생성
            assistant_message = Message(
                role="assistant",
                content=response.content,
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            )
            self.conversation_history.append(assistant_message)
            
            # 각 도구 호출 처리
            for tc in tool_calls:
                # 도구 호출 정보 기록
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                
                tool_call_record = {
                    "name": tool_name,
                    "arguments": tool_args,
                    "result": None
                }
                tool_calls_history.append(tool_call_record)
                
                logger.info(f"도구 호출 세부 정보 - 이름: {tool_name}, 인자: {tool_args}")
                
                # 도구 호출 결과 메시지 생성
                tool_result = await self._execute_tool(tool_name, tool_args)
                tool_call_record["result"] = tool_result
                
                tool_result_message = Message(
                    role="tool",
                    content=tool_result,
                    tool_call_id=tc.id,
                    name=tool_name
                )
                self.conversation_history.append(tool_result_message)
            
            # 다음 턴으로
            current_turn += 1
        
        # 최종 응답이 없으면 (도구 호출 최대치에 도달한 경우)
        if final_response is None:
            # 추가 응답 요청
            final_response = await self.llm.ask(
                messages=self.conversation_history,
                system_msgs=self.system_messages,
                model_id=self.model_id
            )
        
        # 최종 응답 추가
        self.conversation_history.append(Message(role="assistant", content=final_response))
        return final_response, tool_calls_history
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        도구 호출 실행 (여기서는 더미 구현, 실제로는 MCP 서버로 전달)
        
        Args:
            tool_name: 도구 이름
            tool_args: 도구 인자
            
        Returns:
            도구 호출 결과
        """
        # 실제 구현에서는 MCP 서버로 도구 호출 요청을 전달하고 결과를 받아옴
        # 이 예제에서는 간단한 더미 구현만 제공
        
        logger.info(f"도구 호출 실행 (더미) - {tool_name}: {tool_args}")
        
        # 도구 이름에 따라 다른 응답
        if tool_name == "read_file":
            return f"파일 내용: 이것은 {tool_args.get('path')}의 내용입니다."
        elif tool_name == "write_file":
            return f"파일 작성 성공: {tool_args.get('path')}"
        elif tool_name == "list_directory":
            return f"디렉토리 목록: {tool_args.get('path')}의 파일 목록입니다. [file1.txt, file2.py, dir1/]"
        else:
            return f"알 수 없는 도구: {tool_name}"
    
    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """대화 기록 반환"""
        return [msg.dict() for msg in self.conversation_history]
    
    def get_system_messages(self) -> List[Dict[str, Any]]:
        """시스템 메시지 반환"""
        return [msg.dict() for msg in self.system_messages]
    
    def add_system_message(self, content: str):
        """시스템 메시지 추가"""
        self.system_messages.append(Message(role="system", content=content))
    
    def set_model_id(self, model_id: str):
        """모델 ID 설정"""
        self.model_id = model_id
        logger.info(f"모델 ID 변경됨: {model_id}")
