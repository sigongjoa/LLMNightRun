"""
LLM 연동 모듈

다양한 LLM API와의 통신을 처리하는 클래스를 제공합니다.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from backend.services.llm_service import LLMService  # Re-export LLMService class

from backend.models.agent import Message, ToolCall
from backend.models.enums import ToolChoice, LLMType
from backend.llm_studio import call_lm_studio, extract_content, extract_tool_calls
from backend.config.settings import settings
from backend.services.memory_service import get_memory_service
import httpx
import json

logger = logging.getLogger(__name__)


async def generate_from_openai(prompt: str, **kwargs) -> str:
    """
    OpenAI API를 사용하여 텍스트를 생성합니다.
    
    Args:
        prompt: 프롬프트 텍스트
        **kwargs: 추가 매개변수
        
    Returns:
        생성된 텍스트
    """
    try:
        from backend.config.settings import settings
        
        # API 키 확인
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
        
        # 모델 설정 (기본값: gpt-3.5-turbo)
        model = kwargs.get("model", "gpt-3.5-turbo")
        
        # API 요청 데이터 구성
        request_data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        
        # OpenAI API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 응답 컨텐츠 추출
            if (
                "choices" in data 
                and len(data["choices"]) > 0 
                and "message" in data["choices"][0]
                and "content" in data["choices"][0]["message"]
            ):
                return data["choices"][0]["message"]["content"]
            
            logger.error(f"OpenAI API 응답 형식 오류: {data}")
            return "OpenAI API 응답을 처리할 수 없습니다."
    
    except Exception as e:
        logger.error(f"OpenAI API 호출 오류: {str(e)}")
        return f"OpenAI API 오류: {str(e)}"


async def generate_from_claude(prompt: str, **kwargs) -> str:
    """
    Claude API를 사용하여 텍스트를 생성합니다.
    
    Args:
        prompt: 프롬프트 텍스트
        **kwargs: 추가 매개변수
        
    Returns:
        생성된 텍스트
    """
    try:
        from backend.config.settings import settings
        
        # API 키 확인
        api_key = settings.claude_api_key
        if not api_key:
            raise ValueError("Claude API 키가 설정되지 않았습니다")
        
        # 모델 설정 (기본값: claude-3-opus-20240229)
        model = kwargs.get("model", "claude-3-opus-20240229")
        
        # API 요청 데이터 구성
        request_data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        
        # Claude API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=request_data,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 응답 컨텐츠 추출
            if (
                "content" in data
                and len(data["content"]) > 0
                and "text" in data["content"][0]
            ):
                return data["content"][0]["text"]
            
            logger.error(f"Claude API 응답 형식 오류: {data}")
            return "Claude API 응답을 처리할 수 없습니다."
    
    except Exception as e:
        logger.error(f"Claude API 호출 오류: {str(e)}")
        return f"Claude API 오류: {str(e)}"


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
        base_url: Optional[str] = None,
        use_memory: bool = False
    ):
        """
        LLM 인스턴스 초기화
        
        Args:
            config_name: 설정 프로필 이름
            llm_type: LLM 유형 (OPENAI_API, CLAUDE_API, LOCAL_LLM 등)
            base_url: LLM API 기본 URL (로컬 LLM의 경우)
            use_memory: 메모리 기능 사용 여부
        """
        self.config_name = config_name
        self.llm_type = llm_type
        self.use_memory = use_memory
        
        # 로컬 LLM인 경우 기본 URL 설정
        if self.llm_type == LLMType.LOCAL_LLM and base_url is None:
            self.base_url = settings.llm.local_llm_url
        else:
            self.base_url = base_url
            
        # 메모리 서비스 초기화 (사용하는 경우에만)
        self.memory_service = get_memory_service() if use_memory else None
            
        logger.info(f"LLM({config_name}, {llm_type}) 인스턴스 초기화됨 [API URL: {self.base_url}, Memory: {use_memory}]")
    
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
        
        # 메모리 기능이 활성화된 경우 메모리 컨텍스트 추가
        if self.use_memory and self.memory_service:
            # 시스템 메시지가 있는 경우 첫 시스템 메시지에 메모리 컨텍스트 추가
            if system_msgs and len(system_msgs) > 0:
                # 마지막 대화 메시지의 내용으로 관련 메모리 검색
                original_system = system_msgs[0].content
                query = last_msg.content if last_msg.content else ""
                
                # 메모리 컨텍스트를 시스템 메시지에 추가
                system_msgs[0].content = self.memory_service.attach_context_to_prompt(
                    original_system, query, top_k=3
                )
                
                logger.info("메모리 컨텍스트가 시스템 메시지에 추가되었습니다.")
            
            # 대화 내용을 메모리에 저장 (비동기로 처리하지 않음)
            try:
                self.memory_service.add_memory({
                    "content": f"User: {last_msg.content}",
                    "type": "conversation",
                    "metadata": {
                        "role": "user",
                        "message": last_msg.content,
                        "tags": ["user-query"]
                    }
                })
            except Exception as e:
                logger.error(f"대화 메모리 저장 오류: {str(e)}")
                
        logger.info(f"LLM 요청: {len(messages)}개 메시지")
        
        # LM Studio 로컬 LLM 처리
        if self.llm_type == LLMType.LOCAL_LLM and self.base_url:
            try:
                # 설정에서 모델 ID 가져오지 않고, kwargs에서 가져온다
                model_id = kwargs.pop("model_id", None)  # pop으로 파라미터 제거
                
                # model_id가 없으면 설정에서 가져오기
                if not model_id:
                    if hasattr(settings, "llm") and hasattr(settings.llm, "local_llm_model_id"):
                        model_id = settings.llm.local_llm_model_id
                
                # LM Studio API 호출
                response_data = await call_lm_studio(
                    messages=messages,
                    system_msgs=system_msgs,
                    base_url=self.base_url,
                    model_id=model_id,  # 여기서만 모델 ID 전달
                    **kwargs
                )
                
                # 응답 컨텐츠 추출
                content = extract_content(response_data)
                
                # 응답을 메모리에 저장 (메모리 기능이 활성화된 경우)
                if self.use_memory and self.memory_service and content:
                    try:
                        self.memory_service.add_memory({
                            "content": f"Assistant: {content}",
                            "type": "conversation",
                            "metadata": {
                                "role": "assistant",
                                "message": content,
                                "tags": ["assistant-response"]
                            }
                        })
                    except Exception as e:
                        logger.error(f"응답 메모리 저장 오류: {str(e)}")
                
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
        
        # 메모리 기능이 활성화된 경우 메모리 컨텍스트 추가
        if self.use_memory and self.memory_service:
            # 시스템 메시지가 있는 경우 첫 시스템 메시지에 메모리 컨텍스트 추가
            if system_msgs and len(system_msgs) > 0:
                # 마지막 대화 메시지의 내용으로 관련 메모리 검색
                original_system = system_msgs[0].content
                query = last_msg.content if last_msg.content else ""
                
                # 메모리 컨텍스트를 시스템 메시지에 추가
                system_msgs[0].content = self.memory_service.attach_context_to_prompt(
                    original_system, query, top_k=3
                )
                
                logger.info("메모리 컨텍스트가 시스템 메시지에 추가되었습니다.")
            
            # 대화 내용을 메모리에 저장
            try:
                self.memory_service.add_memory({
                    "content": f"User: {last_msg.content}",
                    "type": "conversation",
                    "metadata": {
                        "role": "user",
                        "message": last_msg.content,
                        "tags": ["user-query"]
                    }
                })
            except Exception as e:
                logger.error(f"대화 메모리 저장 오류: {str(e)}")
        
        logger.info(f"LLM 도구 요청: {len(messages)}개 메시지, {len(tools) if tools else 0}개 도구")
        
        # LM Studio 로컬 LLM 처리
        if self.llm_type == LLMType.LOCAL_LLM and self.base_url:
            try:
                # 도구 선택 모드 문자열 변환
                tool_choice_str = None
                if tool_choice:
                    tool_choice_str = tool_choice.value
                
                # 설정에서 모델 ID 가져오지 않고, kwargs에서 가져온다
                model_id = kwargs.pop("model_id", None)  # pop으로 파라미터 제거
                
                # model_id가 없으면 설정에서 가져오기
                if not model_id:
                    if hasattr(settings, "llm") and hasattr(settings.llm, "local_llm_model_id"):
                        model_id = settings.llm.local_llm_model_id
                
                # LM Studio API 호출
                response_data = await call_lm_studio(
                    messages=messages,
                    system_msgs=system_msgs,
                    base_url=self.base_url,
                    tools=tools,
                    tool_choice=tool_choice_str,
                    model_id=model_id,  # 여기서만 모델 ID 전달
                    **kwargs
                )
                
                # 응답 컨텐츠와 도구 호출 추출
                content = extract_content(response_data)
                tool_calls = extract_tool_calls(response_data)
                
                # 응답을 메모리에 저장 (메모리 기능이 활성화된 경우)
                if self.use_memory and self.memory_service and content:
                    try:
                        # 도구 호출이 있는 경우 포함하여 저장
                        tool_calls_str = ""
                        if tool_calls:
                            tool_calls_str = f"\nTool Calls: {json.dumps([t.model_dump() for t in tool_calls])}"
                            
                        self.memory_service.add_memory({
                            "content": f"Assistant: {content}{tool_calls_str}",
                            "type": "conversation",
                            "metadata": {
                                "role": "assistant",
                                "message": content,
                                "has_tool_calls": bool(tool_calls),
                                "tags": ["assistant-response", "tool-call"] if tool_calls else ["assistant-response"]
                            }
                        })
                    except Exception as e:
                        logger.error(f"응답 메모리 저장 오류: {str(e)}")
                
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
    
    def store_experiment_memory(self, experiment_data: Dict[str, Any]) -> Optional[str]:
        """실험 결과를 메모리에 저장합니다.
        
        Args:
            experiment_data: 실험 데이터
            
        Returns:
            저장된 메모리 ID 또는 None (메모리 기능이 비활성화된 경우)
        """
        if not self.use_memory or not self.memory_service:
            logger.warning("메모리 기능이 활성화되지 않았습니다.")
            return None
            
        try:
            memory_id = self.memory_service.store_experiment_memory(experiment_data)
            logger.info(f"실험 메모리가 저장되었습니다. ID: {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"실험 메모리 저장 오류: {str(e)}")
            return None