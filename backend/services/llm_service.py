"""
LLM 서비스 모듈

LLM API와의 통신을 관리하는 서비스를 제공합니다.
"""

import os
import logging
import json
import asyncio
from typing import Optional, Dict, Any, List, Union

import openai
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..models.enums import LLMType
from ..models.response import LLMRequest
from ..exceptions import LLMError, TokenLimitExceeded
from ..models.agent import Message
from ..llm_studio import call_lm_studio, extract_content


logger = logging.getLogger(__name__)


class LLMService:
    """LLM API와 통신하는 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.openai_api_key = settings.llm.openai_api_key
        self.claude_api_key = settings.llm.claude_api_key
        
        # OpenAI API 키 설정
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def get_openai_response(self, prompt: str, **kwargs) -> str:
        """
        OpenAI API를 사용하여 응답을 가져옵니다.
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
            
        Returns:
            OpenAI의 응답 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
            TokenLimitExceeded: 토큰 제한 초과 시
        """
        if not self.openai_api_key:
            raise LLMError("OpenAI API 키가 설정되지 않았습니다.")
        
        # 기본 파라미터
        params = {
            "model": kwargs.get("model", settings.llm.model_name),
            "messages": [
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", settings.llm.temperature),
            "max_tokens": kwargs.get("max_tokens", settings.llm.max_tokens),
            "top_p": kwargs.get("top_p", 0.95),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "presence_penalty": kwargs.get("presence_penalty", 0)
        }
        
        try:
            # 비동기로 API 호출
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.chat.completions.create(**params)
            
            return response.choices[0].message.content
        except openai.APIError as e:
            if "maximum context length" in str(e).lower():
                raise TokenLimitExceeded("OpenAI 최대 토큰 제한 초과")
            logger.error(f"OpenAI API 호출 중 오류 발생: {str(e)}")
            raise LLMError(f"OpenAI API 호출 실패: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def get_claude_response(self, prompt: str, **kwargs) -> str:
        """
        Claude API를 사용하여 응답을 가져옵니다.
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
            
        Returns:
            Claude의 응답 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
            TokenLimitExceeded: 토큰 제한 초과 시
        """
        if not self.claude_api_key:
            raise LLMError("Claude API 키가 설정되지 않았습니다.")
        
        headers = {
            "x-api-key": self.claude_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": kwargs.get("model", "claude-2"),
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": kwargs.get("max_tokens", settings.llm.max_tokens),
            "temperature": kwargs.get("temperature", settings.llm.temperature),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40)
        }
        
        try:
            async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/complete",
                    headers=headers,
                    json=data
                )
                
                if response.status_code != 200:
                    logger.error(f"Claude API 오류: {response.status_code}, {response.text}")
                    raise LLMError(f"Claude API 호출 실패: {response.status_code}")
                
                result = response.json()
                return result.get("completion", "").strip()
        except httpx.ReadTimeout:
            raise LLMError("Claude API 요청 시간 초과")
        except Exception as e:
            if "maximum context length" in str(e).lower() or "token limit" in str(e).lower():
                raise TokenLimitExceeded("Claude 최대 토큰 제한 초과")
            logger.error(f"Claude API 호출 중 오류 발생: {str(e)}")
            raise LLMError(f"Claude API 호출 실패: {str(e)}")

    async def get_local_llm_response(self, prompt: str, **kwargs) -> str:
        """
        로컬 LLM을 사용하여 응답을 가져옵니다.
        
        Args:
            prompt: 질문 내용
            **kwargs: 추가 옵션
            
        Returns:
            로컬 LLM의 응답 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
        """
        try:
            # 메시지 구성
            messages = [Message(role="user", content=prompt)]
            system_msgs = [Message(role="system", content="당신은 도움이 되는 AI 어시스턴트입니다.")]
            
            # 옵션 설정
            base_url = kwargs.get("base_url", "http://127.0.0.1:1234")
            
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
                
            return content
        
        except Exception as e:
            logger.error(f"로컬 LLM 호출 중 오류 발생: {str(e)}")
            raise LLMError(f"로컬 LLM 호출 실패: {str(e)}")
    
    async def get_response(self, llm_type: LLMType, prompt: str, **kwargs) -> str:
        """
        지정된 LLM에 프롬프트를 전송하고 응답을 받아옵니다.
        
        Args:
            llm_type: LLM 유형
            prompt: 질문 내용
            **kwargs: 추가 옵션
            
        Returns:
            LLM의 응답 텍스트
            
        Raises:
            LLMError: 지원되지 않는 LLM 유형이거나 API 호출 실패 시
        """
        if llm_type == LLMType.OPENAI_API:
            return await self.get_openai_response(prompt, **kwargs)
        elif llm_type == LLMType.CLAUDE_API:
            return await self.get_claude_response(prompt, **kwargs)
        elif llm_type == LLMType.LOCAL_LLM:
            return await self.get_local_llm_response(prompt, **kwargs)
        else:
            raise LLMError(f"API를 통한 요청이 지원되지 않는 LLM 유형입니다: {llm_type}")
    
    async def get_custom_llm_response(
        self,
        prompt: str, 
        api_url: str, 
        api_key: str, 
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        커스텀 LLM API를 호출하는 함수
        
        Args:
            prompt: 질문 내용
            api_url: API 엔드포인트 URL
            api_key: API 키
            headers: 요청 헤더 (선택 사항)
            payload_template: 요청 본문 템플릿 (선택 사항)
            
        Returns:
            LLM의 응답 텍스트
            
        Raises:
            LLMError: API 호출 실패 시
        """
        if not headers:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        
        if not payload_template:
            payload_template = {
                "prompt": prompt,
                "max_tokens": settings.llm.max_tokens,
                "temperature": settings.llm.temperature
            }
        else:
            # 프롬프트를 템플릿에 삽입
            for key, value in payload_template.items():
                if isinstance(value, str) and "{prompt}" in value:
                    payload_template[key] = value.format(prompt=prompt)
        
        try:
            async with httpx.AsyncClient(timeout=settings.llm.timeout) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload_template
                )
                
                if response.status_code != 200:
                    logger.error(f"API 오류: {response.status_code}, {response.text}")
                    raise LLMError(f"API 호출 실패: {response.status_code}")
                
                result = response.json()
                
                # 응답 구조에 따라 결과 추출 방법 커스터마이징 필요
                if "text" in result:
                    return result["text"]
                elif "output" in result:
                    return result["output"]
                elif "content" in result:
                    return result["content"]
                else:
                    logger.warning(f"응답에서 결과를 추출할 수 없습니다: {result}")
                    return json.dumps(result)
                    
        except Exception as e:
            logger.error(f"API 호출 중 오류 발생: {str(e)}")
            raise LLMError(f"API 호출 실패: {str(e)}")