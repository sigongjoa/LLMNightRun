"""
내보내기 기본 클래스

대화 내보내기의 기본이 되는 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..models import Conversation

class Exporter(ABC):
    """대화 내보내기 추상 클래스"""
    
    def __init__(self, include_metadata: bool = True, include_timestamps: bool = True, **kwargs):
        """
        내보내기 초기화
        
        Args:
            include_metadata: 메타데이터 포함 여부
            include_timestamps: 타임스탬프 포함 여부
            **kwargs: 추가 옵션
        """
        self.include_metadata = include_metadata
        self.include_timestamps = include_timestamps
        self.options = kwargs
    
    @abstractmethod
    def export(self, conversation: Conversation) -> str:
        """
        대화 내보내기
        
        Args:
            conversation: 대화 객체
        
        Returns:
            내보내기 결과 문자열
        """
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """
        내보내기 형식 이름
        
        Returns:
            형식 이름
        """
        pass
