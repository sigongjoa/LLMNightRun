"""
Model Context Protocol (MCP) 기본 트랜스포트 정의

이 모듈은 MCP 표준에 따른 기본 트랜스포트 클래스를 제공합니다.
"""

import abc
import json
import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger("mcp.transport")

MessageHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class BaseTransport(abc.ABC):
    """MCP 기본 트랜스포트
    
    모든 MCP 트랜스포트 구현의 기본 클래스입니다.
    """
    
    @abc.abstractmethod
    async def start(self, message_handler: MessageHandler) -> None:
        """트랜스포트 시작
        
        Args:
            message_handler: 메시지 처리 콜백 함수
        """
        pass
    
    @abc.abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """메시지 전송
        
        Args:
            message: 전송할 메시지
        """
        pass
    
    @abc.abstractmethod
    async def close(self) -> None:
        """트랜스포트 종료"""
        pass
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """JSON-RPC 메시지 유효성 검증
        
        Args:
            message: 검증할 메시지
            
        Returns:
            bool: 메시지 유효 여부
        """
        # JSON-RPC 2.0 필수 필드 확인
        if 'jsonrpc' not in message or message['jsonrpc'] != '2.0':
            return False
        
        # 요청 메시지 확인
        if 'id' in message:
            if 'method' not in message:
                return False
        
        # 응답 메시지 확인
        elif 'result' not in message and 'error' not in message:
            return False
        
        # 알림 메시지 확인
        elif 'method' not in message:
            return False
        
        return True
    
    def _create_parse_error(self, id: Any = None) -> Dict[str, Any]:
        """파싱 오류 메시지 생성
        
        Args:
            id: 요청 ID (알 수 없는 경우 None)
            
        Returns:
            Dict[str, Any]: 오류 메시지
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
