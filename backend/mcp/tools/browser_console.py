"""
브라우저 개발자 콘솔 MCP 도구

브라우저 개발자 콘솔과 통신하여 자바스크립트 실행 및 로그 수집 기능을 제공합니다.
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger("mcp.tools.browser_console")

class BrowserConsoleTool:
    """브라우저 개발자 콘솔 도구
    
    브라우저 개발자 콘솔과 통신하여 자바스크립트 실행 및 로그 수집 기능을 제공합니다.
    WebSocket을 통해 클라이언트와 양방향 통신을 수행합니다.
    """
    
    def __init__(self):
        """브라우저 콘솔 도구 초기화"""
        self._connections = {}  # session_id -> websocket
        self._logs = {}  # session_id -> log list
        self._pending_executions = {}  # execution_id -> future
        
    async def register_connection(self, session_id: str, websocket):
        """WebSocket 연결 등록
        
        Args:
            session_id: 세션 ID
            websocket: WebSocket 연결 객체
        """
        self._connections[session_id] = websocket
        self._logs.setdefault(session_id, [])
        logger.info(f"Browser console connection registered: {session_id}")
        
        try:
            # 연결 활성화 및 이벤트 처리
            await self._handle_connection(session_id, websocket)
        except Exception as e:
            logger.error(f"Error handling browser console connection: {e}")
        finally:
            # 연결 해제 처리
            await self._unregister_connection(session_id)
    
    async def _unregister_connection(self, session_id: str):
        """WebSocket 연결 해제
        
        Args:
            session_id: 세션 ID
        """
        if session_id in self._connections:
            del self._connections[session_id]
            logger.info(f"Browser console connection unregistered: {session_id}")
    
    async def _handle_connection(self, session_id: str, websocket):
        """WebSocket 연결 처리
        
        클라이언트로부터 메시지를 수신하고 적절히 처리합니다.
        
        Args:
            session_id: 세션 ID
            websocket: WebSocket 연결 객체
        """
        while True:
            try:
                # 클라이언트 메시지 수신
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # 메시지 유형 처리
                if data.get("type") == "log":
                    await self._handle_log(session_id, data)
                elif data.get("type") == "execution_result":
                    await self._handle_execution_result(data)
                elif data.get("type") == "error":
                    await self._handle_error(data)
                elif data.get("type") == "connection_status":
                    await self._handle_connection_status(session_id, data)
                else:
                    logger.warning(f"Unknown message type from browser console: {data.get('type')}")
            
            except Exception as e:
                logger.error(f"Error processing browser console message: {e}")
                break
    
    async def _handle_log(self, session_id: str, data: Dict[str, Any]):
        """콘솔 로그 처리
        
        클라이언트로부터 수신한 콘솔 로그를 저장합니다.
        
        Args:
            session_id: 세션 ID
            data: 로그 데이터
        """
        log_entry = {
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "level": data.get("level", "info"),
            "message": data.get("message", ""),
            "source": data.get("source", "console")
        }
        
        # 로그 저장
        self._logs[session_id].append(log_entry)
        logger.debug(f"Browser console log received: {log_entry}")
    
    async def _handle_execution_result(self, data: Dict[str, Any]):
        """실행 결과 처리
        
        자바스크립트 실행 결과를 처리합니다.
        
        Args:
            data: 실행 결과 데이터
        """
        execution_id = data.get("execution_id")
        if execution_id in self._pending_executions:
            # 실행 결과 반환
            future = self._pending_executions[execution_id]
            future.set_result({
                "result": data.get("result"),
                "error": data.get("error"),
                "status": data.get("status", "success")
            })
            # 처리 완료된 실행 요청 삭제
            del self._pending_executions[execution_id]
    
    async def _handle_error(self, data: Dict[str, Any]):
        """오류 처리
        
        클라이언트에서 발생한 오류를 처리합니다.
        
        Args:
            data: 오류 데이터
        """
        execution_id = data.get("execution_id")
        if execution_id in self._pending_executions:
            # 오류 반환
            future = self._pending_executions[execution_id]
            future.set_result({
                "result": None,
                "error": data.get("message", "Unknown error"),
                "status": "error"
            })
            # 처리 완료된 실행 요청 삭제
            del self._pending_executions[execution_id]
        
        logger.error(f"Browser console error: {data.get('message')}")
    
    async def _handle_connection_status(self, session_id: str, data: Dict[str, Any]):
        """연결 상태 처리
        
        클라이언트 연결 상태 업데이트를 처리합니다.
        
        Args:
            session_id: 세션 ID
            data: 상태 데이터
        """
        status = data.get("status")
        if status == "disconnecting":
            # 클라이언트 연결 해제 요청
            await self._unregister_connection(session_id)
    
    async def execute_javascript(self, session_id: str, code: str, timeout: int = 30) -> Dict[str, Any]:
        """자바스크립트 코드 실행
        
        브라우저 콘솔에서 자바스크립트 코드를 실행합니다.
        
        Args:
            session_id: 세션 ID
            code: 실행할 자바스크립트 코드
            timeout: 실행 제한 시간 (초)
            
        Returns:
            Dict[str, Any]: 실행 결과
            
        Raises:
            ValueError: 잘못된 세션 ID 또는 코드인 경우
            TimeoutError: 실행 시간 초과인 경우
        """
        if session_id not in self._connections:
            raise ValueError(f"Browser console session not found: {session_id}")
        
        if not code or not code.strip():
            raise ValueError("JavaScript code is empty")
        
        # 실행 요청 ID 생성
        execution_id = f"exec_{datetime.utcnow().timestamp()}"
        
        # 결과를 받을 Future 객체 생성
        future = asyncio.get_event_loop().create_future()
        self._pending_executions[execution_id] = future
        
        # 실행 요청 전송
        websocket = self._connections[session_id]
        await websocket.send_text(json.dumps({
            "type": "execute",
            "execution_id": execution_id,
            "code": code
        }))
        
        try:
            # 결과 대기
            result = await asyncio.wait_for(future, timeout)
            return result
        except asyncio.TimeoutError:
            # 시간 초과 처리
            if execution_id in self._pending_executions:
                del self._pending_executions[execution_id]
            raise TimeoutError(f"JavaScript execution timed out after {timeout} seconds")
    
    def get_logs(self, session_id: str, count: int = None, level: str = None, source: str = None) -> List[Dict[str, Any]]:
        """콘솔 로그 조회
        
        브라우저 콘솔에서 수집된 로그를 조회합니다.
        
        Args:
            session_id: 세션 ID
            count: 조회할 로그 수 (None인 경우 모두 조회)
            level: 로그 레벨 필터 (info, warn, error 등)
            source: 로그 소스 필터 (console, network 등)
            
        Returns:
            List[Dict[str, Any]]: 로그 항목 목록
        """
        if session_id not in self._logs:
            return []
        
        logs = self._logs[session_id]
        
        # 필터 적용
        if level:
            logs = [log for log in logs if log.get("level") == level]
        if source:
            logs = [log for log in logs if log.get("source") == source]
        
        # 개수 제한
        if count is not None and count > 0:
            logs = logs[-count:]
        
        return logs
    
    def clear_logs(self, session_id: str) -> bool:
        """콘솔 로그 초기화
        
        브라우저 콘솔에서 수집된 로그를 초기화합니다.
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 초기화 성공 여부
        """
        if session_id in self._logs:
            self._logs[session_id] = []
            return True
        return False
    
    def get_active_sessions(self) -> List[str]:
        """활성 세션 조회
        
        현재 활성 상태인 브라우저 콘솔 세션 목록을 조회합니다.
        
        Returns:
            List[str]: 활성 세션 ID 목록
        """
        return list(self._connections.keys())
