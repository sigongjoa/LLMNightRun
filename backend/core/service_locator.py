"""
서비스 로케이터 모듈

애플리케이션에서 사용되는 서비스 인스턴스를 초기화하고 등록합니다.
"""

from typing import TypeVar, Type, Dict, Any, Optional, cast

from .di import container
from ..interfaces.llm_service import ILLMService
from ..services.llm_service import LLMService

T = TypeVar('T')


def setup_services():
    """
    모든 서비스를 초기화하고 DI 컨테이너에 등록합니다.
    """
    # LLM 서비스 등록
    container.register(ILLMService, LLMService)
    
    # 추가 서비스 등록은 여기에...


def get_service(service_type: Type[T]) -> T:
    """
    특정 유형의 서비스 인스턴스를 가져옵니다.
    
    Args:
        service_type: 가져올 서비스 유형
    
    Returns:
        서비스 인스턴스
    """
    return container.resolve(service_type)


# 편의 함수
def get_llm_service() -> ILLMService:
    """
    LLM 서비스 인스턴스를 가져옵니다.
    
    Returns:
        LLM 서비스 인스턴스
    """
    return get_service(ILLMService)
