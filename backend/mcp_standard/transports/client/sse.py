"""
Model Context Protocol (MCP) SSE 클라이언트 트랜스포트 구현

이 모듈은 Server-Sent Events를 사용하는 MCP 클라이언트 트랜스포트를 제공합니다.
"""

import json
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable
import re
import ssl

import aiohttp
from aiohttp import ClientSession, ClientResponse, ClientTimeout

from ..base import BaseTransport, MessageHandler

logger = logging.getLogger("mcp.transport.sse")


class SSEClientTransport(BaseTransport):
    """SSE 클라이언트 트랜스포트
    
    Server-Sent Events를 통해 MCP 메시지를 주고받는 트랜스포트입니다.
    HTTP 기반 원격 서버와의 통신에 적합합니다.
    """
    
    def __init__(
        self, 
        server_url: str,
        verify_ssl: bool = True,
        timeout: float = 30.0,
        headers: Dict[str, str] = None
    ):
        """
        Args:
            server_url: 서버 기본 URL (예: "http://localhost:8000")
            verify_ssl: SSL 인증서 확인 여부
            timeout: 요청 타임아웃 (초)
            headers: 추가 HTTP 헤더
        """
        self.server_url = server_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.headers = headers or {}
        
        self._session: Optional[ClientSession] = None
        self._message_handler: Optional[MessageHandler] = None
        self._sse_response: Optional[ClientResponse] = None
        self._sse_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._client_id: str = str(uuid.uuid4())
    
    async def start(self, message_handler: MessageHandler) -> None:
        """트랜스포트 시작
        
        Args:
            message_handler: 메시지 처리 콜백 함수
        """
        self._message_handler = message_handler
        
        try:
            # SSL 컨텍스트 설정
            ssl_context = None if self.verify_ssl else ssl.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # aiohttp 세션 생성
            timeout = ClientTimeout(total=None, sock_connect=10.0, sock_read=None)
            self._session = ClientSession(
                timeout=timeout,
                headers={
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Client-ID': self._client_id,
                    **self.headers
                }
            )
            
            # SSE 연결 설정
            sse_url = f"{self.server_url}/mcp/sse"
            self._sse_response = await self._session.get(
                sse_url,
                ssl=ssl_context,
                timeout=ClientTimeout(total=None)  # SSE 연결은 타임아웃 없음
            )
            
            if self._sse_response.status != 200:
                error_text = await self._sse_response.text()
                raise RuntimeError(f"SSE connection failed: {self._sse_response.status} - {error_text}")
            
            # SSE 이벤트 처리 태스크 시작
            self._running = True
            self._sse_task = asyncio.create_task(self._process_sse_events())
            
            logger.info(f"SSE client transport started, connected to {sse_url}")
            
        except Exception as e:
            logger.error(f"Error starting SSE client transport: {str(e)}")
            await self.close()
            raise
    
    async def _process_sse_events(self) -> None:
        """SSE 이벤트 처리"""
        try:
            if not self._sse_response:
                return
            
            # 이벤트 버퍼
            buffer = ""
            event_data = ""
            event_id = None
            
            # 라인 단위로 읽기
            async for line_bytes in self._sse_response.content.iter_chunks():
                if not self._running:
                    break
                
                line = line_bytes[0].decode('utf-8')
                buffer += line
                
                # 완전한 이벤트 검사
                lines = buffer.split('\n')
                buffer = lines.pop()  # 마지막 라인은 불완전할 수 있음
                
                for line in lines:
                    line = line.rstrip()
                    
                    # 빈 라인은 이벤트 종료
                    if not line:
                        if event_data:
                            try:
                                # JSON 이벤트 데이터 파싱
                                message = json.loads(event_data)
                                
                                # 메시지 유효성 검증
                                if self._validate_message(message):
                                    # 메시지 처리
                                    await self._handle_sse_message(message)
                                else:
                                    logger.warning(f"Invalid SSE message format: {event_data}")
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse SSE JSON message: {event_data}")
                            except Exception as e:
                                logger.error(f"Error processing SSE message: {str(e)}")
                            
                            # 이벤트 데이터 초기화
                            event_data = ""
                            event_id = None
                        continue
                    
                    # 이벤트 필드 파싱
                    if line.startswith('data: '):
                        event_data = line[6:]
                    elif line.startswith('id: '):
                        event_id = line[4:]
                    elif line.startswith(':'):
                        # 주석 또는 키핑 얼라이브 메시지
                        pass
            
            logger.info("SSE event stream closed")
            
        except asyncio.CancelledError:
            logger.debug("SSE event processor task cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Error in SSE event processor: {str(e)}")
            
        finally:
            if self._running:
                await self.close()
    
    async def _handle_sse_message(self, message: Dict[str, Any]) -> None:
        """SSE 메시지 처리
        
        Args:
            message: 수신한 메시지
        """
        try:
            # 메시지 유형에 따라 처리
            if 'method' in message:
                # 알림 메시지
                await self._message_handler(message)
            else:
                logger.warning(f"Unexpected SSE message format: {message}")
        
        except Exception as e:
            logger.error(f"Error handling SSE message: {str(e)}")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """메시지 전송
        
        Args:
            message: 전송할 메시지
        """
        if not self._running or not self._session:
            logger.warning("Cannot send message: transport not running")
            return
        
        try:
            # JSON-RPC 요청/응답 구분
            if 'method' in message and 'id' in message:
                # 요청 메시지 (POST)
                await self._send_request(message)
            elif 'id' in message:
                # 응답 메시지 (POST)
                await self._send_request(message)
            elif 'method' in message:
                # 알림 메시지 (POST)
                await self._send_request(message)
            else:
                logger.warning(f"Unknown message format for sending: {message}")
        
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def _send_request(self, message: Dict[str, Any]) -> None:
        """HTTP POST 요청 전송
        
        Args:
            message: 전송할 메시지
        """
        if not self._session:
            return
        
        # 메시지 엔드포인트
        url = f"{self.server_url}/mcp/message"
        
        try:
            # HTTP POST 요청
            async with self._session.post(
                url,
                json=message,
                headers={
                    'Content-Type': 'application/json',
                    'Client-ID': self._client_id
                },
                timeout=ClientTimeout(total=self.timeout)
            ) as response:
                # 응답 확인
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error sending request: {response.status} - {error_text}")
                    return
                
                # 응답 본문 파싱
                response_data = await response.json()
                
                # 응답 처리 (id가 있는 요청에 대한 응답)
                if 'id' in message and 'id' in response_data:
                    await self._message_handler(response_data)
        
        except asyncio.TimeoutError:
            logger.error(f"Request timed out after {self.timeout} seconds")
        
        except Exception as e:
            logger.error(f"Error sending request: {str(e)}")
    
    async def close(self) -> None:
        """트랜스포트 종료"""
        self._running = False
        
        # SSE 태스크 취소
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None
        
        # SSE 응답 종료
        if self._sse_response:
            self._sse_response.close()
            self._sse_response = None
        
        # HTTP 세션 종료
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("SSE client transport closed")
