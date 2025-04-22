"""
Markdown 내보내기

대화를 Markdown 형식으로 내보내는 기능을 제공합니다.
"""

from typing import Dict, Any, Optional

from .base import Exporter
from ..models import Conversation, Message

class MarkdownExporter(Exporter):
    """Markdown 내보내기 클래스"""
    
    def __init__(self, code_block: bool = True, **kwargs):
        """
        Markdown 내보내기 초기화
        
        Args:
            code_block: 코드 블록 형식 사용 여부
            **kwargs: 추가 옵션
        """
        super().__init__(**kwargs)
        self.code_block = code_block
    
    def export(self, conversation: Conversation) -> str:
        """
        대화를 Markdown으로 내보내기
        
        Args:
            conversation: 대화 객체
        
        Returns:
            Markdown 문자열
        """
        result = []
        
        # 제목
        result.append(f"# {conversation.title}")
        result.append("")
        
        # 메타데이터
        if self.include_metadata and conversation.metadata:
            result.append("## 메타데이터")
            result.append("")
            for key, value in conversation.metadata.items():
                result.append(f"- **{key}**: {value}")
            result.append("")
        
        # 대화 정보
        result.append("## 대화 정보")
        result.append("")
        result.append(f"- **대화 ID**: {conversation.conversation_id}")
        result.append(f"- **생성 시간**: {conversation.created_at.isoformat()}")
        result.append(f"- **업데이트 시간**: {conversation.updated_at.isoformat()}")
        result.append(f"- **메시지 수**: {len(conversation.messages)}")
        result.append("")
        
        # 메시지
        result.append("## 대화 내용")
        result.append("")
        
        for message in conversation.messages:
            # 역할에 따른 서식
            if message.role == "user":
                result.append("### 사용자")
            elif message.role == "assistant":
                result.append("### 어시스턴트")
            elif message.role == "system":
                result.append("### 시스템")
            else:
                result.append(f"### {message.role}")
            
            # 타임스탬프 (옵션)
            if self.include_timestamps:
                result.append(f"*{message.timestamp.isoformat()}*")
            
            result.append("")
            
            # 코드 블록 사용 여부에 따라 내용 포맷
            if self.code_block:
                result.append("```")
                result.append(message.content)
                result.append("```")
            else:
                # 들여쓰기로 표시
                lines = message.content.splitlines()
                for line in lines:
                    result.append(f"> {line}")
            
            result.append("")
        
        return "\n".join(result)
    
    @property
    def format_name(self) -> str:
        """
        내보내기 형식 이름
        
        Returns:
            형식 이름
        """
        return "Markdown"
