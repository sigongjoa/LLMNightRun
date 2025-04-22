"""
대화 관련 데이터 모델

대화 및 메시지 관련 데이터 구조를 정의합니다.
"""

import datetime
import uuid
from typing import List, Dict, Any, Optional

class Message:
    """대화 메시지 클래스"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime.datetime] = None, 
                 message_id: Optional[str] = None):
        """
        메시지 초기화
        
        Args:
            role: 메시지 역할 ('user', 'assistant', 'system')
            content: 메시지 내용
            timestamp: 메시지 타임스탬프 (기본값: 현재 시간)
            message_id: 메시지 ID (기본값: 자동 생성)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.datetime.now()
        self.message_id = message_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환
        
        Returns:
            메시지 딕셔너리
        """
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        딕셔너리에서 메시지 생성
        
        Args:
            data: 메시지 딕셔너리
        
        Returns:
            메시지 객체
        """
        # 타임스탬프 파싱
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.datetime.now()
        
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            message_id=data.get("message_id", str(uuid.uuid4()))
        )

class Conversation:
    """대화 클래스"""
    
    def __init__(self, title: str, conversation_id: Optional[str] = None, 
                 created_at: Optional[datetime.datetime] = None, 
                 updated_at: Optional[datetime.datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        대화 초기화
        
        Args:
            title: 대화 제목
            conversation_id: 대화 ID (기본값: 자동 생성)
            created_at: 생성 시간 (기본값: 현재 시간)
            updated_at: 업데이트 시간 (기본값: 현재 시간)
            metadata: 메타데이터 (기본값: {})
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.title = title
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()
        self.metadata = metadata or {}
        self.messages: List[Message] = []
    
    def add_message(self, role: str, content: str) -> Message:
        """
        메시지 추가
        
        Args:
            role: 메시지 역할
            content: 메시지 내용
        
        Returns:
            추가된 메시지
        """
        # 메시지 생성
        message = Message(role=role, content=content)
        
        # 메시지 추가
        self.messages.append(message)
        
        # 업데이트 시간 갱신
        self.updated_at = datetime.datetime.now()
        
        return message
    
    def get_messages(self) -> List[Message]:
        """
        모든 메시지 가져오기
        
        Returns:
            메시지 목록
        """
        return self.messages
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """
        ID로 메시지 가져오기
        
        Args:
            message_id: 메시지 ID
        
        Returns:
            메시지 객체 또는 None (없는 경우)
        """
        for message in self.messages:
            if message.message_id == message_id:
                return message
        return None
    
    def clear_messages(self) -> None:
        """모든 메시지 삭제"""
        self.messages = []
        self.updated_at = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환
        
        Returns:
            대화 딕셔너리
        """
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "messages": [message.to_dict() for message in self.messages]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        딕셔너리에서 대화 생성
        
        Args:
            data: 대화 딕셔너리
        
        Returns:
            대화 객체
        """
        # 시간 파싱
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.datetime.now()
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = datetime.datetime.now()
        
        # 대화 객체 생성
        conversation = cls(
            title=data["title"],
            conversation_id=data.get("conversation_id", str(uuid.uuid4())),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )
        
        # 메시지 추가
        for message_data in data.get("messages", []):
            message = Message.from_dict(message_data)
            conversation.messages.append(message)
        
        return conversation
