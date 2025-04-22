"""
JSON 내보내기

대화를 JSON 형식으로 내보내는 기능을 제공합니다.
"""

import json
import datetime
from typing import Dict, Any, Optional

from .base import Exporter
from ..models import Conversation, Message

class JsonExporter(Exporter):
    """JSON 내보내기 클래스"""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False, **kwargs):
        """
        JSON 내보내기 초기화
        
        Args:
            indent: JSON 들여쓰기 수준
            ensure_ascii: ASCII 문자만 사용할지 여부
            **kwargs: 추가 옵션
        """
        super().__init__(**kwargs)
        self.indent = indent
        self.ensure_ascii = ensure_ascii
    
    def export(self, conversation: Conversation) -> str:
        """
        대화를 JSON으로 내보내기
        
        Args:
            conversation: 대화 객체
        
        Returns:
            JSON 문자열
        """
        # 기본 정보
        result = {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
        
        # 메타데이터 추가 (옵션)
        if self.include_metadata:
            result["metadata"] = conversation.metadata
        
        # 메시지 변환
        messages = []
        for message in conversation.messages:
            msg_data = {
                "role": message.role,
                "content": message.content,
                "message_id": message.message_id
            }
            
            # 타임스탬프 추가 (옵션)
            if self.include_timestamps:
                msg_data["timestamp"] = message.timestamp.isoformat()
            
            messages.append(msg_data)
        
        result["messages"] = messages
        
        # JSON 직렬화
        return json.dumps(result, indent=self.indent, ensure_ascii=self.ensure_ascii)
    
    @property
    def format_name(self) -> str:
        """
        내보내기 형식 이름
        
        Returns:
            형식 이름
        """
        return "JSON"
