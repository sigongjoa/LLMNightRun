"""
Model Context Protocol (MCP) Stdio 클라이언트 트랜스포트 구현

이 모듈은 표준 입출력을 사용하는 MCP 클라이언트 트랜스포트를 제공합니다.
"""

import json
import sys
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List

from ..base import BaseTransport, MessageHandler

logger = logging.getLogger("mcp.transport.stdio")


class StdioClientTransport(BaseTransport):
    """Stdio 클라이언트 트랜스포트
    
    표준 입출력을 통해 MCP 메시지를 주고받는 트랜스포트입니다.
    자식 프로세스와의 통신에 적합합니다.
    """
    
    def __init__(self, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """
        Args:
            command: 실행할 명령어
            args: 명령행 인자 목록
            env: 환경 변수 딕셔너리
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        
        self._process = None
        self._stdout_reader = None
        self._stderr_reader = None
        self._message_handler: Optional[MessageHandler] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._send_lock = asyncio.Lock()
    
    async def start(self, message_handler: MessageHandler) -> None:
        """트랜스포트 시작
        
        Args:
            message_handler: 메시지 처리 콜백 함수
        """
        self._message_handler = message_handler
        
        try:
            # 자식 프로세스 시작
            command_args = [self.command] + self.args
            self._process = await asyncio.create_subprocess_exec(
                *command_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env
            )
            
            if not self._process:
                raise RuntimeError(f"Failed to start process: {self.command} {' '.join(self.args)}")
            
            logger.info(f"Started process: {self.command} {' '.join(self.args)}")
            
            # 스트림 리더 생성
            self._stdout_reader = asyncio.StreamReader()
            self._stderr_reader = asyncio.StreamReader()
            
            # 표준 출력/오류에 리더 연결
            stdout_protocol = asyncio.StreamReaderProtocol(self._stdout_reader)
            stderr_protocol = asyncio.StreamReaderProtocol(self._stderr_reader)
            
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: stdout_protocol, self._process.stdout)
            await loop.connect_read_pipe(lambda: stderr_protocol, self._process.stderr)
            
            # 메시지 읽기 태스크 시작
            self._running = True
            self._reader_task = asyncio.create_task(self._read_messages())
            self._stderr_task = asyncio.create_task(self._read_stderr())
            
            logger.info("Stdio client transport started")
            
        except Exception as e:
            logger.error(f"Error starting Stdio client transport: {str(e)}")
            await self.close()
            raise
    
    async def _read_messages(self) -> None:
        """표준 출력에서 메시지 읽기"""
        try:
            while self._running and not self._stdout_reader.at_eof():
                # 한 줄 읽기
                line = await self._stdout_reader.readline()
                if not line:
                    logger.warning("Server stdout closed")
                    break
                
                line_str = line.decode('utf-8').rstrip()
                if not line_str:
                    continue
                
                # JSON 메시지 파싱
                try:
                    message = json.loads(line_str)
                    
                    # 메시지 유효성 검증
                    if not self._validate_message(message):
                        logger.warning(f"Invalid message format: {line_str}")
                        continue
                    
                    # 메시지 처리
                    if 'id' in message and 'method' in message:
                        # 요청 메시지
                        response = await self._message_handler(message)
                        if response:
                            await self.send(response)
                            
                    elif 'method' in message:
                        # 알림 메시지
                        await self._message_handler(message)
                        
                    elif 'id' in message:
                        # 응답 메시지
                        await self._message_handler(message)
                        
                    else:
                        logger.warning(f"Unknown message type: {line_str}")
                
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON message: {line_str}")
                
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
            
            logger.info("Message reader task finished")
            
        except asyncio.CancelledError:
            logger.debug("Message reader task cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Error in message reader task: {str(e)}")
            
        finally:
            if self._running:
                await self.close()
    
    async def _read_stderr(self) -> None:
        """표준 오류에서 로그 읽기"""
        try:
            while self._running and not self._stderr_reader.at_eof():
                line = await self._stderr_reader.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8').rstrip()
                if line_str:
                    logger.info(f"Server stderr: {line_str}")
            
            logger.info("Stderr reader task finished")
            
        except asyncio.CancelledError:
            logger.debug("Stderr reader task cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Error in stderr reader task: {str(e)}")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """메시지 전송
        
        Args:
            message: 전송할 메시지
        """
        if not self._running or not self._process or not self._process.stdin:
            logger.warning("Cannot send message: process not running")
            return
        
        try:
            # 메시지 직렬화
            json_str = json.dumps(message) + "\n"
            data = json_str.encode('utf-8')
            
            # 동시 쓰기 방지를 위한 잠금
            async with self._send_lock:
                self._process.stdin.write(data)
                await self._process.stdin.drain()
                
            logger.debug(f"Sent message: {json_str[:100]}...")
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            await self.close()
    
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
        
        if self._stderr_task:
            self._stderr_task.cancel()
            try:
                await self._stderr_task
            except asyncio.CancelledError:
                pass
        
        # 프로세스 종료
        if self._process:
            if self._process.stdin:
                self._process.stdin.close()
                try:
                    await self._process.stdin.wait_closed()
                except Exception:
                    pass
            
            try:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), 2.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()
            except Exception:
                pass
            
            self._process = None
        
        logger.info("Stdio client transport closed")
