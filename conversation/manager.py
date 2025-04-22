"""
대화 관리자

대화 생성, 저장, 로드 및 내보내기 기능을 제공합니다.
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple

from .models import Conversation, Message
from .exporters import export_conversation
from core.logging import get_logger
from core.config import get_config
from core.events import publish

logger = get_logger("conversation")

class ConversationManager:
    """대화 관리자 클래스"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        대화 관리자 초기화
        
        Args:
            storage_dir: 대화 저장 디렉토리 (기본값: 설정에서 가져옴)
        """
        config = get_config()
        
        # 저장 디렉토리 설정
        self.storage_dir = storage_dir or config.get("conversation", "storage_dir")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 현재 활성 대화
        self.active_conversation: Optional[Conversation] = None
        
        logger.info(f"대화 관리자 초기화됨: {self.storage_dir}")
    
    def create_conversation(self, title: str, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        새 대화 생성
        
        Args:
            title: 대화 제목
            metadata: 메타데이터 (기본값: {})
        
        Returns:
            생성된 대화 객체
        """
        conversation = Conversation(title=title, metadata=metadata or {})
        self.active_conversation = conversation
        
        # 이벤트 발행
        publish("conversation.created", conversation_id=conversation.conversation_id, title=title)
        
        logger.debug(f"새 대화 생성됨: {conversation.conversation_id} ({title})")
        return conversation
    
    def set_active_conversation(self, conversation: Conversation) -> None:
        """
        활성 대화 설정
        
        Args:
            conversation: 대화 객체
        """
        self.active_conversation = conversation
        
        # 이벤트 발행
        publish("conversation.activated", conversation_id=conversation.conversation_id)
        
        logger.debug(f"활성 대화 설정됨: {conversation.conversation_id}")
    
    def get_active_conversation(self) -> Optional[Conversation]:
        """
        현재 활성 대화 가져오기
        
        Returns:
            활성 대화 객체 또는 None (없는 경우)
        """
        return self.active_conversation
    
    def add_message(self, role: str, content: str) -> Optional[Message]:
        """
        활성 대화에 메시지 추가
        
        Args:
            role: 메시지 역할
            content: 메시지 내용
        
        Returns:
            추가된 메시지 또는 None (활성 대화가 없는 경우)
        """
        if not self.active_conversation:
            logger.warning("활성 대화가 없어 메시지를 추가할 수 없습니다.")
            return None
        
        # 메시지 추가
        message = self.active_conversation.add_message(role=role, content=content)
        
        # 이벤트 발행
        publish("conversation.message.added", 
               conversation_id=self.active_conversation.conversation_id,
               message_id=message.message_id, 
               role=role)
        
        logger.debug(f"메시지 추가됨: {role} ({len(content)} 글자)")
        return message
    
    def save_conversation(self, conversation: Optional[Conversation] = None) -> bool:
        """
        대화 저장
        
        Args:
            conversation: 저장할 대화 (기본값: 활성 대화)
        
        Returns:
            성공 여부
        """
        conversation = conversation or self.active_conversation
        
        if not conversation:
            logger.warning("저장할 대화가 없습니다.")
            return False
        
        try:
            # 파일 경로
            file_path = os.path.join(self.storage_dir, f"{conversation.conversation_id}.json")
            
            # 대화 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 이벤트 발행
            publish("conversation.saved", conversation_id=conversation.conversation_id)
            
            logger.debug(f"대화 저장됨: {conversation.conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"대화 저장 중 오류 발생: {str(e)}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        ID로 대화 로드
        
        Args:
            conversation_id: 대화 ID
        
        Returns:
            대화 객체 또는 None (로드 실패 시)
        """
        try:
            # 파일 경로
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"대화 파일을 찾을 수 없음: {file_path}")
                return None
            
            # 파일 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 대화 객체 생성
            conversation = Conversation.from_dict(data)
            
            # 이벤트 발행
            publish("conversation.loaded", conversation_id=conversation_id)
            
            logger.debug(f"대화 로드됨: {conversation_id}")
            return conversation
        
        except Exception as e:
            logger.error(f"대화 로드 중 오류 발생: {str(e)}")
            return None
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        저장된 모든 대화 목록 가져오기
        
        Returns:
            대화 요약 목록
        """
        conversations = []
        
        try:
            # 모든 JSON 파일 찾기
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    
                    try:
                        # 파일에서 기본 정보만 로드
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 대화 요약 정보
                        conversation_info = {
                            "conversation_id": data.get("conversation_id"),
                            "title": data.get("title"),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "message_count": len(data.get("messages", [])),
                            "file_path": file_path
                        }
                        
                        conversations.append(conversation_info)
                    
                    except Exception as e:
                        logger.error(f"대화 파일 로드 중 오류 발생: {file_path} - {str(e)}")
        
        except Exception as e:
            logger.error(f"대화 목록 로드 중 오류 발생: {str(e)}")
        
        # 최신 업데이트 순으로 정렬
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        대화 삭제
        
        Args:
            conversation_id: 대화 ID
        
        Returns:
            성공 여부
        """
        try:
            # 파일 경로
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"삭제할 대화 파일을 찾을 수 없음: {file_path}")
                return False
            
            # 파일 삭제
            os.remove(file_path)
            
            # 활성 대화인 경우 초기화
            if (self.active_conversation and 
                self.active_conversation.conversation_id == conversation_id):
                self.active_conversation = None
            
            # 이벤트 발행
            publish("conversation.deleted", conversation_id=conversation_id)
            
            logger.debug(f"대화 삭제됨: {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"대화 삭제 중 오류 발생: {str(e)}")
            return False
    
    def export_conversation(self, conversation: Optional[Conversation] = None, 
                          format: str = "json", **kwargs) -> Optional[str]:
        """
        대화 내보내기
        
        Args:
            conversation: 내보낼 대화 (기본값: 활성 대화)
            format: 내보내기 형식 ('json', 'markdown', 'text')
            **kwargs: 추가 옵션
        
        Returns:
            내보내기 결과 문자열 또는 None (실패 시)
        """
        conversation = conversation or self.active_conversation
        
        if not conversation:
            logger.warning("내보낼 대화가 없습니다.")
            return None
        
        try:
            # 내보내기 실행
            result = export_conversation(conversation, format=format, **kwargs)
            
            # 이벤트 발행
            publish("conversation.exported", 
                   conversation_id=conversation.conversation_id, 
                   format=format)
            
            logger.debug(f"대화 내보내기 완료: {conversation.conversation_id} ({format})")
            return result
        
        except Exception as e:
            logger.error(f"대화 내보내기 중 오류 발생: {str(e)}")
            return None
    
    def save_export(self, conversation: Optional[Conversation] = None, 
                   format: str = "json", file_path: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        대화를 내보내고 파일로 저장
        
        Args:
            conversation: 내보낼 대화 (기본값: 활성 대화)
            format: 내보내기 형식
            file_path: 저장할 파일 경로 (기본값: 자동 생성)
            **kwargs: 추가 옵션
        
        Returns:
            저장된 파일 경로 또는 None (실패 시)
        """
        conversation = conversation or self.active_conversation
        
        if not conversation:
            logger.warning("내보낼 대화가 없습니다.")
            return None
        
        try:
            # 내보내기 실행
            result = export_conversation(conversation, format=format, **kwargs)
            
            if not result:
                logger.warning("내보내기 결과가 없습니다.")
                return None
            
            # 파일 경로 설정
            if not file_path:
                # 현재 시간 포맷 (YYYYMMDD_HHMMSS)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 확장자 설정
                ext = ".json" if format == "json" else ".md" if format == "markdown" else ".txt"
                
                # 파일명 설정
                filename = f"{conversation.title}_{timestamp}{ext}".replace(" ", "_")
                
                # 파일 경로 설정
                export_dir = os.path.join(self.storage_dir, "exports")
                os.makedirs(export_dir, exist_ok=True)
                file_path = os.path.join(export_dir, filename)
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            # 이벤트 발행
            publish("conversation.export.saved", 
                   conversation_id=conversation.conversation_id, 
                   format=format, file_path=file_path)
            
            logger.debug(f"대화 내보내기 저장됨: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"대화 내보내기 저장 중 오류 발생: {str(e)}")
            return None
