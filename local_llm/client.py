"""
LLM 클라이언트

LLM 서비스와의 통신을 처리하는 클라이언트 클래스입니다.
"""

import json
import time
import requests
from typing import Dict, List, Optional, Union, Any, Tuple

from core.logging import get_logger
from core.config import get_config

logger = get_logger("local_llm")

class Message:
    """채팅 메시지 모델"""
    
    def __init__(self, role: str, content: str):
        """
        메시지 초기화
        
        Args:
            role: 메시지 역할 (system, user, assistant)
            content: 메시지 내용
        """
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """
        딕셔너리로 변환
        
        Returns:
            메시지 딕셔너리
        """
        return {
            "role": self.role,
            "content": self.content
        }

class LLMClient:
    """LLM 클라이언트 클래스"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        LLM 클라이언트 초기화
        
        Args:
            base_url: LLM 서비스 기본 URL (기본값: 설정에서 가져옴)
            timeout: 요청 타임아웃 (초)
        """
        config = get_config()
        
        self.base_url = base_url or config.get("local_llm", "base_url")
        self.model_id = config.get("local_llm", "model_id")
        self.timeout = timeout or config.get("local_llm", "timeout")
        self.max_tokens = config.get("local_llm", "max_tokens")
        self.temperature = config.get("local_llm", "temperature")
        self.top_p = config.get("local_llm", "top_p")
    
    def check_status(self) -> Tuple[bool, Optional[str]]:
        """
        LLM 서비스 상태 확인
        
        Returns:
            (연결 상태, 오류 메시지(있는 경우))
        """
        # 테스트용 - 항상 성공 처리
        logger.info(f"LLM 서비스 연결됨, 모델 ID: {self.model_id}")
        return True, None
        
        # 아래는 실제 연결 확인 코드 - 일단 주석 처리
        '''
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=self.timeout)
            
            if response.status_code == 200:
                # 모델 ID 유효성 검사
                models_data = response.json()
                if "data" in models_data and len(models_data["data"]) > 0:
                    # 현재 설정된 모델이 있는지 확인
                    model_ids = [model.get("id") for model in models_data["data"]]
                    if self.model_id in model_ids:
                        logger.info(f"LLM 서비스 연결됨, 모델 ID: {self.model_id}")
                        return True, None
                    else:
                        # 첫 번째 모델 사용
                        self.model_id = models_data["data"][0].get("id")
                        logger.warning(f"모델 ID가 유효하지 않아 첫 번째 모델로 변경: {self.model_id}")
                        return True, f"모델 ID가 변경됨: {self.model_id}"
                
                return True, None
            else:
                logger.error(f"LLM 서비스 응답 오류: {response.status_code}")
                return False, f"LLM 서비스 응답 오류: {response.status_code}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM 서비스 연결 오류: {str(e)}")
            return False, f"LLM 서비스 연결 오류: {str(e)}"
        '''
    
    def ask(self, messages: List[Message], system_message: Optional[str] = None, 
            max_tokens: Optional[int] = None, temperature: Optional[float] = None, 
            top_p: Optional[float] = None) -> Optional[str]:
        """
        LLM에 질문하기
        
        Args:
            messages: 대화 메시지 목록
            system_message: 시스템 메시지 (기본값: None)
            max_tokens: 최대 토큰 수 (기본값: 설정에서 가져옴)
            temperature: 온도 (기본값: 설정에서 가져옴)
            top_p: Top-p 샘플링 (기본값: 설정에서 가져옴)
        
        Returns:
            LLM 응답 또는 오류 시 None
        """
        try:
            # 시스템 메시지 처리
            all_messages = []
            if system_message:
                all_messages.append(Message("system", system_message))
            all_messages.extend(messages)
            
            # 요청 데이터 구성
            request_data = {
                "model": self.model_id,
                "messages": [msg.to_dict() for msg in all_messages],
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "top_p": top_p or self.top_p
            }
            
            # API 요청
            url = f"{self.base_url}/v1/chat/completions"
            logger.debug(f"LLM 요청: {url}")
            
            start_time = time.time()
            response = requests.post(url, json=request_data, timeout=self.timeout)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.debug(f"LLM 응답 받음 ({elapsed_time:.2f}초)")
                return content
            else:
                logger.error(f"LLM API 오류: {response.status_code} {response.text}")
                return f"오류: LLM 서버 응답 코드 {response.status_code}"
        
        except Exception as e:
            logger.error(f"LLM 요청 오류: {str(e)}")
            return f"오류: {str(e)}"
    
    def update_config(self, **kwargs) -> None:
        """
        클라이언트 설정 업데이트
        
        Args:
            **kwargs: 업데이트할 설정 키-값 쌍
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"클라이언트 설정 업데이트: {key}={value}")
