"""
LLM 서비스 모듈

다양한 LLM API와의 통신을 관리하는 서비스를 제공합니다.
호환되는 LLM 모델들:
- OpenAI (GPT 모델)
- Anthropic (Claude 모델)
- Local LLM (LM Studio 등)
- 커스텀 API 엔드포인트
"""

import os
import json
from typing import Optional, Dict, Any, List, Union, Callable, Awaitable, cast
from abc import ABC, abstractmethod

import openai
import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)

from ..config import settings
from ..models.enums import LLMType
from ..models.agent import Message
from ..exceptions import LLMError, TokenLimitExceeded
from ..llm_studio import call_lm_studio, extract_content
from ..logger import get_logger, log_execution_time, LogContext
from ..interfaces.llm_service import ILLMProvider, ILLMService


# 로거 설정
logger = get_logger(__name__)


class OpenAIProvider(ILLMProvider):
    """OpenAI API 제공자"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        OpenAI API 제공자 초기화
        
        Args:
            api_key: OpenAI API 키 (None인 경우 환경 변수에서 로드)
        """
        self.api_key = api_key or settings.llm.openai_api_key
        if not self.api_key:
            raise LLMError("OpenAI API 키가 설정되지 않았습니다.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(LLMError),
        reraise=True
    )
    @log_execution_time(level="INFO", operation_name="OpenAI API 호출")
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        OpenAI API를 사용하여 텍스트 생성
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - model: 사용할 모델 이름
                - temperature: 온도 (창의성 조절)
                - max_tokens: 최대 생성 토큰 수
                - system_prompt: 시스템 프롬프트
            
        Returns:
            생성된 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
            TokenLimitExceeded: 토큰 제한 초과 시
        """
        try:
            with LogContext(llm_provider="openai", model=kwargs.get("model", "gpt-3.5-turbo")):
                # 기본 파라미터
                params = {
                    "model": kwargs.get("model", settings.llm.model_name),
                    "messages": [
                        {"role": "system", "content": kwargs.get("system_prompt", "당신은 도움이 되는 AI 어시스턴트입니다.")},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": kwargs.get("temperature", settings.llm.temperature),
                    "max_tokens": kwargs.get("max_tokens", settings.llm.max_tokens),
                    "top_p": kwargs.get("top_p", 0.95),
                    "frequency_penalty": kwargs.get("frequency_penalty", 0),
                    "presence_penalty": kwargs.get("presence_penalty", 0)
                }
                
                # 메시지 로깅
                logger.debug(f"OpenAI API 요청: {params['model']}, 프롬프트 길이: {len(prompt)}자")
                
                # 비동기로 API 호출
                client = openai.AsyncOpenAI(api_key=self.api_key)
                response = await client.chat.completions.create(**params)
                
                # 응답 로깅
                content = response.choices[0].message.content
                logger.debug(f"OpenAI API 응답 받음: {len(content)}자")
                
                return content
        
        except openai.APIError as e:
            if "maximum context length" in str(e).lower():
                logger.warning(f"OpenAI 토큰 제한 초과: {str(e)}")
                raise TokenLimitExceeded(f"OpenAI 최대 토큰 제한 초과: {str(e)}")
            
            logger.error(f"OpenAI API 호출 중 오류 발생: {str(e)}")
            raise LLMError(f"OpenAI API 호출 실패: {str(e)}")
        
        except Exception as e:
            logger.error(f"OpenAI 호출 중 예기치 않은 오류: {str(e)}", exc_info=True)
            raise LLMError(f"OpenAI API 호출 중 예기치 않은 오류: {str(e)}")


class ClaudeProvider(ILLMProvider):
    """Anthropic Claude API 제공자"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Claude API 제공자 초기화
        
        Args:
            api_key: Claude API 키 (None인 경우 환경 변수에서 로드)
        """
        self.api_key = api_key or settings.llm.claude_api_key
        if not self.api_key:
            raise LLMError("Claude API 키가 설정되지 않았습니다.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(LLMError),
        reraise=True
    )
    @log_execution_time(level="INFO", operation_name="Claude API 호출")
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Claude API를 사용하여 텍스트 생성
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - model: 사용할 모델 이름
                - temperature: 온도 (창의성 조절)
                - max_tokens: 최대 생성 토큰 수
                - system_prompt: 시스템 프롬프트
            
        Returns:
            생성된 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
            TokenLimitExceeded: 토큰 제한 초과 시
        """
        try:
            with LogContext(llm_provider="anthropic", model=kwargs.get("model", "claude-2")):
                # 요청 헤더 설정
                headers = {
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                
                # 시스템 프롬프트가 있는 경우 Claude의 형식으로 추가
                system_prompt = kwargs.get("system_prompt", "")
                formatted_prompt = prompt
                
                if system_prompt:
                    formatted_prompt = f"{system_prompt}\n\n{prompt}"
                
                # 요청 본문 구성
                data = {
                    "model": kwargs.get("model", "claude-2"),
                    "prompt": f"\n\nHuman: {formatted_prompt}\n\nAssistant:",
                    "max_tokens_to_sample": kwargs.get("max_tokens", settings.llm.max_tokens),
                    "temperature": kwargs.get("temperature", settings.llm.temperature),
                    "top_p": kwargs.get("top_p", 0.95),
                    "top_k": kwargs.get("top_k", 40)
                }
                
                # 메시지 로깅
                logger.debug(f"Claude API 요청: {data['model']}, 프롬프트 길이: {len(formatted_prompt)}자")
                
                # API 호출
                async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
                    response = await client.post(
                        "https://api.anthropic.com/v1/complete",
                        headers=headers,
                        json=data
                    )
                    
                    # 응답 확인
                    if response.status_code != 200:
                        logger.error(f"Claude API 오류: {response.status_code}, {response.text}")
                        raise LLMError(f"Claude API 호출 실패: {response.status_code}, {response.text}")
                    
                    # 응답 처리
                    result = response.json()
                    content = result.get("completion", "").strip()
                    
                    # 응답 로깅
                    logger.debug(f"Claude API 응답 받음: {len(content)}자")
                    
                    return content
                
        except httpx.ReadTimeout:
            logger.error("Claude API 요청 시간 초과")
            raise LLMError("Claude API 요청 시간 초과")
        
        except Exception as e:
            if "maximum context length" in str(e).lower() or "token limit" in str(e).lower():
                logger.warning(f"Claude 토큰 제한 초과: {str(e)}")
                raise TokenLimitExceeded(f"Claude 최대 토큰 제한 초과: {str(e)}")
            
            logger.error(f"Claude API 호출 중 오류 발생: {str(e)}", exc_info=True)
            raise LLMError(f"Claude API 호출 실패: {str(e)}")


class LocalLLMProvider(ILLMProvider):
    """로컬 LLM 제공자 (LM Studio 등)"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        로컬 LLM 제공자 초기화
        
        Args:
            base_url: 로컬 LLM API URL (None인 경우 기본값 사용)
        """
        self.base_url = base_url or "http://127.0.0.1:1234"
    
    @log_execution_time(level="INFO", operation_name="로컬 LLM 호출")
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        로컬 LLM을 사용하여 텍스트 생성
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - base_url: API 기본 URL (기본값: http://127.0.0.1:1234)
                - temperature: 온도 (창의성 조절)
                - max_tokens: 최대 생성 토큰 수
                - system_prompt: 시스템 프롬프트
            
        Returns:
            생성된 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
        """
        try:
            # 로컬 LLM은 모델 이름 대신 기본 URL을 사용
            model_name = "local-llm"
            if "model" in kwargs:
                model_name = kwargs["model"]
            
            with LogContext(llm_provider="local", model=model_name):
                # 메시지 구성
                messages = [Message(role="user", content=prompt)]
                
                # 시스템 프롬프트 설정
                system_prompt = kwargs.get("system_prompt", "당신은 도움이 되는 AI 어시스턴트입니다.")
                system_msgs = [Message(role="system", content=system_prompt)]
                
                # 옵션 설정
                base_url = kwargs.get("base_url", self.base_url)
                
                # 메시지 로깅
                logger.debug(f"로컬 LLM 요청: {base_url}, 프롬프트 길이: {len(prompt)}자")
                
                # LM Studio API 호출
                response_data = await call_lm_studio(
                    messages=messages,
                    system_msgs=system_msgs,
                    base_url=base_url,
                    max_tokens=kwargs.get("max_tokens", settings.llm.max_tokens),
                    temperature=kwargs.get("temperature", settings.llm.temperature),
                    top_p=kwargs.get("top_p", 0.95)
                )
                
                # 응답 추출
                content = extract_content(response_data)
                if content is None:
                    raise LLMError("로컬 LLM에서 응답을 받을 수 없습니다.")
                
                # 응답 로깅
                logger.debug(f"로컬 LLM 응답 받음: {len(content)}자")
                
                return content
        
        except Exception as e:
            logger.error(f"로컬 LLM 호출 중 오류 발생: {str(e)}", exc_info=True)
            raise LLMError(f"로컬 LLM 호출 실패: {str(e)}")


class CustomAPIProvider(ILLMProvider):
    """커스텀 LLM API 제공자"""
    
    def __init__(
        self, 
        api_url: str, 
        api_key: str, 
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None,
        response_extractor: Optional[Callable[[Dict[str, Any]], str]] = None
    ):
        """
        커스텀 LLM API 제공자 초기화
        
        Args:
            api_url: API 엔드포인트 URL
            api_key: API 키
            headers: 요청 헤더 (선택 사항)
            payload_template: 요청 본문 템플릿 (선택 사항)
            response_extractor: 응답에서 텍스트를 추출하는 함수 (선택 사항)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.headers = headers or {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.payload_template = payload_template or {}
        self.response_extractor = response_extractor or self._default_extractor
    
    def _default_extractor(self, response_data: Dict[str, Any]) -> str:
        """
        기본 응답 추출기
        
        Args:
            response_data: API 응답 데이터
            
        Returns:
            추출된 텍스트
        """
        if "text" in response_data:
            return response_data["text"]
        elif "output" in response_data:
            return response_data["output"]
        elif "content" in response_data:
            return response_data["content"]
        elif "completion" in response_data:
            return response_data["completion"]
        elif "result" in response_data:
            return response_data["result"]
        else:
            logger.warning(f"응답에서 결과를 추출할 수 없습니다: {response_data}")
            return json.dumps(response_data)
    
    @log_execution_time(level="INFO", operation_name="커스텀 LLM API 호출")
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        커스텀 LLM API를 사용하여 텍스트 생성
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - headers: 커스텀 헤더 (선택 사항)
                - payload: 커스텀 요청 본문 (선택 사항)
            
        Returns:
            생성된 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
        """
        try:
            with LogContext(llm_provider="custom", api_url=self.api_url):
                # 헤더 설정
                headers = kwargs.get("headers", self.headers)
                
                # 페이로드 구성
                payload = kwargs.get("payload", self.payload_template.copy())
                
                # 프롬프트 추가
                if "prompt" not in payload:
                    payload["prompt"] = prompt
                
                # 페이로드에 프롬프트 형식화
                for key, value in payload.items():
                    if isinstance(value, str) and "{prompt}" in value:
                        payload[key] = value.format(prompt=prompt)
                
                # 기본 설정 적용
                if "max_tokens" not in payload and "max_tokens" in kwargs:
                    payload["max_tokens"] = kwargs["max_tokens"]
                elif "max_tokens" not in payload:
                    payload["max_tokens"] = settings.llm.max_tokens
                
                if "temperature" not in payload and "temperature" in kwargs:
                    payload["temperature"] = kwargs["temperature"]
                elif "temperature" not in payload:
                    payload["temperature"] = settings.llm.temperature
                
                # 요청 로깅
                logger.debug(f"커스텀 API 요청: {self.api_url}, 프롬프트 길이: {len(prompt)}자")
                
                # API 호출
                async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=payload
                    )
                    
                    # 응답 확인
                    if response.status_code != 200:
                        logger.error(f"커스텀 API 오류: {response.status_code}, {response.text}")
                        raise LLMError(f"커스텀 API 호출 실패: {response.status_code}, {response.text}")
                    
                    # 응답 처리
                    result = response.json()
                    content = self.response_extractor(result)
                    
                    # 응답 로깅
                    logger.debug(f"커스텀 API 응답 받음: {len(content)}자")
                    
                    return content
        
        except Exception as e:
            logger.error(f"커스텀 API 호출 중 오류 발생: {str(e)}", exc_info=True)
            raise LLMError(f"커스텀 API 호출 실패: {str(e)}")


class LLMService(ILLMService):
    """LLM API와 통신하는 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.providers: Dict[LLMType, ILLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """기본 제공자 초기화"""
        # OpenAI 제공자
        if settings.llm.openai_api_key:
            try:
                self.providers[LLMType.openai_api] = OpenAIProvider(settings.llm.openai_api_key)
                logger.info("OpenAI 제공자 초기화 완료")
            except Exception as e:
                logger.error(f"OpenAI 제공자 초기화 실패: {str(e)}")
        
        # Claude 제공자
        if settings.llm.claude_api_key:
            try:
                self.providers[LLMType.claude_api] = ClaudeProvider(settings.llm.claude_api_key)
                logger.info("Claude 제공자 초기화 완료")
            except Exception as e:
                logger.error(f"Claude 제공자 초기화 실패: {str(e)}")
        
        # 로컬 LLM 제공자
        try:
            self.providers[LLMType.local_llm] = LocalLLMProvider()
            logger.info("로컬 LLM 제공자 초기화 완료")
        except Exception as e:
            logger.error(f"로컬 LLM 제공자 초기화 실패: {str(e)}")
    
    def register_provider(self, llm_type: LLMType, provider: ILLMProvider):
        """
        새 LLM 제공자 등록
        
        Args:
            llm_type: LLM 유형
            provider: LLM 제공자 인스턴스
        """
        self.providers[llm_type] = provider
        logger.info(f"{llm_type.value} 제공자 등록 완료")
    
    def register_custom_provider(
        self, 
        name: str, 
        api_url: str, 
        api_key: str, 
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None
    ):
        """
        커스텀 LLM 제공자 등록
        
        Args:
            name: 제공자 이름 (LLMType에 등록되지 않은 경우 새로 추가)
            api_url: API 엔드포인트 URL
            api_key: API 키
            headers: 요청 헤더 (선택 사항)
            payload_template: 요청 본문 템플릿 (선택 사항)
        """
        # 커스텀 제공자 생성
        provider = CustomAPIProvider(
            api_url=api_url,
            api_key=api_key,
            headers=headers,
            payload_template=payload_template
        )
        
        # LLMType에 존재하는지 확인
        try:
            llm_type = LLMType(name)
        except ValueError:
            # 새 유형 추가 (런타임에는 불가능하므로 기존 유형 사용)
            llm_type = LLMType.CUSTOM_API
        
        # 제공자 등록
        self.register_provider(llm_type, provider)
    
    async def get_response(self, llm_type: LLMType, prompt: str, **kwargs) -> str:
        """
        지정된 LLM에 프롬프트를 전송하고 응답을 받아옵니다.
        
        Args:
            llm_type: LLM 유형
            prompt: 질문 내용
            **kwargs: 추가 옵션
                - model: 모델 이름
                - temperature: 온도
                - max_tokens: 최대 토큰 수
                - system_prompt: 시스템 프롬프트
            
        Returns:
            LLM의 응답 텍스트
            
        Raises:
            LLMError: 지원되지 않는 LLM 유형이거나 API 호출 실패 시
        """
        # 제공자 확인
        if llm_type not in self.providers:
            raise LLMError(f"지원되지 않는 LLM 유형입니다: {llm_type}")
        
        # 프롬프트 로깅 
        logger.info(
            f"LLM 요청: {llm_type.value}", 
            extra={"prompt_length": len(prompt), "model": kwargs.get("model", "default")}
        )
        
        # 제공자 호출
        provider = self.providers[llm_type]
        response = await provider.generate(prompt, **kwargs)
        
        # 응답 로깅
        logger.info(
            f"LLM 응답 받음: {llm_type.value}",
            extra={"response_length": len(response)}
        )
        
        return response
