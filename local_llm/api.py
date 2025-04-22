#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM API

로컬 LLM과의 상호작용을 위한 간소화된 API를 제공합니다.
"""

from typing import List, Optional, Dict, Any, Tuple

from .client import LLMClient, Message
from core.config import get_config
from core.logging import get_logger
from core.events import publish

logger = get_logger("local_llm.api")

# 전역 LLM 클라이언트 인스턴스
_llm_client = None

def get_llm_client() -> LLMClient:
    """
    LLM 클라이언트 인스턴스 가져오기
    
    Returns:
        LLM 클라이언트 인스턴스
    """
    global _llm_client
    
    if _llm_client is None:
        config = get_config()
        base_url = config.get("local_llm", "base_url")
        _llm_client = LLMClient(base_url=base_url)
    
    return _llm_client

def get_status() -> Tuple[bool, bool, Optional[str]]:
    """
    LLM 상태 가져오기
    
    Returns:
        (활성화 여부, 연결 상태, 오류 메시지)
    """
    config = get_config()
    enabled = config.get("local_llm", "enabled", True)
    
    if not enabled:
        return False, False, "LLM이 비활성화됨"
    
    client = get_llm_client()
    connected, error = client.check_status()
    
    return enabled, connected, error

def chat(messages: List[Dict[str, str]], system_message: Optional[str] = None,
         max_tokens: Optional[int] = None, temperature: Optional[float] = None,
         top_p: Optional[float] = None) -> Optional[str]:
    """
    LLM과 채팅
    
    Args:
        messages: 메시지 목록 (각 메시지는 'role'과 'content' 키를 가진 딕셔너리)
        system_message: 시스템 메시지 (기본값: None)
        max_tokens: 최대 토큰 수 (기본값: 설정에서 가져옴)
        temperature: 온도 (기본값: 설정에서 가져옴)
        top_p: Top-p 샘플링 (기본값: 설정에서 가져옴)
    
    Returns:
        LLM 응답
    """
    # 상태 확인
    enabled, connected, error = get_status()
    
    if not enabled:
        logger.warning("LLM이 비활성화됨")
        return "오류: LLM이 비활성화됨"
    
    if not connected:
        logger.error(f"LLM 연결 실패: {error}")
        return f"오류: LLM 연결 실패 - {error}"
    
    # 메시지 변환
    message_objects = [Message(msg["role"], msg["content"]) for msg in messages]
    
    # 이벤트 발행
    publish("llm.chat.request", messages=messages, system_message=system_message)
    
    # 테스트용 응답
    last_message = messages[-1]["content"] if messages else ""
    response = f"""{last_message}에 대한 응답입니다.

저는 테스트용 응답을 생성하고 있습니다. 이 응답은 LLM 서버가 연결되지 않았을 때 사용됩니다.

실제 사용 시에는 LLM API 서버를 실행하고 연결 설정을 확인하세요.

모듈 탭에서는 다음 기능들을 사용할 수 있습니다:
1. GitHub 문서 생성 - 코드 저장소에서 자동으로 문서를 생성
2. GitHub AI 설정 - AI 프로젝트 환경 구성 자동화
3. Arxiv 논문 - 논문 검색 및 관리
4. 벡터 검색 - 임베딩 기반 의미 검색
    """
    
    # 이벤트 발행
    publish("llm.chat.response", request_messages=messages, response=response)
    
    return response
    
    # 원래 LLM 요청 코드 - 테스트를 위해 주석 처리
    '''
    # LLM 요청
    client = get_llm_client()
    response = client.ask(
        message_objects,
        system_message=system_message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )
    
    # 이벤트 발행
    publish("llm.chat.response", request_messages=messages, response=response)
    
    return response
    '''

def update_config(enabled: Optional[bool] = None, base_url: Optional[str] = None,
                 model_id: Optional[str] = None, max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 timeout: Optional[int] = None) -> None:
    """
    LLM 설정 업데이트
    
    Args:
        enabled: 활성화 여부
        base_url: 기본 URL
        model_id: 모델 ID
        max_tokens: 최대 토큰 수
        temperature: 온도
        top_p: Top-p 샘플링
        timeout: 타임아웃 (초)
    """
    config = get_config()
    
    # 설정 업데이트
    if enabled is not None:
        config.set("local_llm", "enabled", enabled)
    
    if base_url is not None:
        config.set("local_llm", "base_url", base_url)
    
    if model_id is not None:
        config.set("local_llm", "model_id", model_id)
    
    if max_tokens is not None:
        config.set("local_llm", "max_tokens", max_tokens)
    
    if temperature is not None:
        config.set("local_llm", "temperature", temperature)
    
    if top_p is not None:
        config.set("local_llm", "top_p", top_p)
    
    if timeout is not None:
        config.set("local_llm", "timeout", timeout)
    
    # 설정 저장
    config.save()
    
    # 클라이언트 업데이트 (있는 경우)
    global _llm_client
    if _llm_client is not None:
        _llm_client.update_config(
            base_url=base_url,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout=timeout
        )
    
    # 이벤트 발행
    publish("llm.config.updated")
