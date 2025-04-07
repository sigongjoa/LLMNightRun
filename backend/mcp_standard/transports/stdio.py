"""
Model Context Protocol (MCP) Stdio 트랜스포트 구현

이 모듈은 표준 입출력을 사용하는 MCP 트랜스포트를 제공합니다.
"""

import json
import sys
import asyncio
import logging
from typing import Dict, Any, Optional

from .base import BaseTransport, MessageHandler

logger = logging.getLogger("mcp.transport.stdio")


class StdioServerTransport(BaseTransport):
    """Stdio 서버 트랜스포트
    
    표준 입출력을 통해 MCP 메시지를 주고받는 트랜스포트입니다.
    로컬 프로세스 통신에 적합합니다.
    """
    
    def __init__(self):
        self._message_handler: Optional[MessageHandler] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._send_lock = asyncio.Lock()
    
    async def start(self, message_handler: MessageHandler) -> None:
        """트랜스포트 시작
        
        Args:
            message_handler: 메시지 처리 콜백 함수
        """
        self._message_handler = message_handler
        self._running = True
        
        # stdin 리더 태스크 시작
        self._reader_task = asyncio.create_task(self._read_stdin())
        logger.info("Stdio transport started")
    
    async def _read_stdin(self) -> None:
        """표준 입력에서 메시지 읽기"""
        # stdin 스트림 래핑
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        # 메시지 읽기 루프
        while self._running:
            try:
                # 헤더와 본문 구분을 위한 개행 문자 확인
                line = await reader.readline()
                if not line:
                    logger.warning("Stdin closed, stopping transport")
                    self._running = False
                    break
                
                # JSON 메시지 파싱
                try:
                    message = json.loads(line.decode('utf-8'))
                    
                    # 메시지 유효성 검증
                    if not self._validate_message(message):
                        response = self._create_parse_error(message.get('id'))
                        await self.send(response)
                        continue
                    
                    # 메시지 처리 및 응답
                    if 'id' in message:
                        response = await self._message_handler(message)
                        await self.send(response)
                    else:
                        # 알림 메시지 처리 (응답 없음)
                        await self._message_handler(message)
                
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON message")
                    response = self._create_parse_error()
                    await self.send(response)
                
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    if 'id' in message:
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get('id'),
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": str(e)
                            }
                        }
                        await self.send(response)
            
            except Exception as e:
                logger.error(f"Stdin read error: {str(e)}")
                await asyncio.sleep(0.1)  # 에러 발생 시 잠시 대기
    
    async def send(self, message: Dict[str, Any]) -> None:
        """메시지 전송
        
        Args:
            message: 전송할 메시지
        """
        if not self._running:
            logger.warning("Transport not running, cannot send message")
            return
        
        try:
            # 메시지 직렬화
            json_str = json.dumps(message)
            
            # 동시 쓰기 방지를 위한 잠금
            async with self._send_lock:
                # 표준 출력으로 메시지 전송 (개행 문자 포함)
                sys.stdout.write(json_str + '\n')
                sys.stdout.flush()
                
                logger.debug(f"Sent message: {json_str[:100]}...")
        
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def close(self) -> None:
        """트랜스포트 종료"""
        self._running = False
        
        # 리더 태스크 취소
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stdio transport closed")
