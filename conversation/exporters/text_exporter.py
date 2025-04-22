"""
텍스트 내보내기

대화를 일반 텍스트 형식으로 내보내는 기능을 제공합니다.
"""

from typing import Dict, Any, Optional

from .base import Exporter
from ..models import Conversation, Message

class TextExporter(Exporter):
    """텍스트 내보내기 클래스"""
    
    def __init__(self, include_headers: bool = True, separator: str = "\n----------\n", **kwargs):
        """
        텍스트 내보내기 초기화
        
        Args:
            include_headers: 헤더 포함 여부
            separator: 메시지 구분자
            **kwargs: 추가 옵션
        """
        super().__init__(**kwargs)
        self.include_headers = include_headers
        self.separator = separator
    
    def export(self, conversation: Conversation) -> str:
        """
        대화를 텍스트로 내보내기
        
        Args:
            conversation: 대화 객체
        
        Returns:
            텍스트 문자열
        """
        result = []
        
        # 제목 및 기본 정보
        if self.include_headers:
            result.append(f"제목: {conversation.title}")
            result.append(f"대화 ID: {conversation.conversation_id}")
            result.append(f"생성 시간: {conversation.created_at.isoformat()}")
            result.append(f"업데이트 시간: {conversation.updated_at.isoformat()}")
            
            # 메타데이터 (옵션)
            if self.include_metadata and conversation.metadata:
                result.append("\n메타데이터:")
                for key, value in conversation.metadata.items():
                    result.append(f"{key}: {value}")
            
            result.append(self.separator)
        
        # 메시지
        for message in conversation.messages:
            # 역할 표시
            if message.role == "user":
                result.append("사용자:")
            elif message.role == "assistant":
                result.append("어시스턴트:")
            elif message.role == "system":
                result.append("시스템:")
            else:
                result.append(f"{message.role}:")
            
            # 타임스탬프 (옵션)
            if self.include_timestamps:
                result.append(f"[{message.timestamp.isoformat()}]")
            
            # 메시지 내용
            result.append(message.content)
            
            # 구분자
            result.append(self.separator)
        
        return "\n".join(result)
    
    @property
    def format_name(self) -> str:
        """
        내보내기 형식 이름
        
        Returns:
            형식 이름
        """
        return "Text"
