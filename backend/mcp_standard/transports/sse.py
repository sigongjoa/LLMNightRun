"""
Model Context Protocol (MCP) SSE 트랜스포트 구현

이 모듈은 Server-Sent Events를 사용하는 MCP 트랜스포트를 제공합니다.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
import uuid

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel

from .base import BaseTransport, MessageHandler

logger = logging.getLogger("mcp.transport.sse")


class JsonRpcRequest(BaseModel):
    """JSON-RPC 요청 모델"""
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class SSEServerTransport(BaseTransport):
    """SSE 서버 트랜스포트
    
    HTTP와 Server-Sent Events를 사용하여 MCP 메시지를 주고받는 트랜스포트입니다.
    웹 애플리케이션 통합에 적합합니다.
    """
    
    def __init__(
        self, 
        app: FastAPI,
        sse_endpoint: str = "/mcp/sse",
        message_endpoint: str = "/mcp/message"
    ):
        """
        Args:
            app: FastAPI 애플리케이션 인스턴스
            sse_endpoint: SSE 연결 엔드포인트 경로
            message_endpoint: 메시지 전송 엔드포인트 경로
        """
        self.app = app
        self.sse_endpoint = sse_endpoint
        self.message_endpoint = message_endpoint
        
        self._message_handler: Optional[MessageHandler] = None
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._running: bool = False
    
    async def start(self, message_handler: MessageHandler) -> None:
        """트랜스포트 시작
        
        Args:
            message_handler: 메시지 처리 콜백 함수
        """
        self._message_handler = message_handler
        self._running = True
        
        # SSE 엔드포인트 등록
        self.app.get(self.sse_endpoint)(self._handle_sse_connection)
        
        # 메시지 엔드포인트 등록
        self.app.post(self.message_endpoint)(self._handle_message)
        
        logger.info(f"SSE transport started with endpoints: SSE={self.sse_endpoint}, Message={self.message_endpoint}")
    
    async def _handle_sse_connection(self, request: Request) -> StreamingResponse:
        """SSE 연결 처리
        
        Args:
            request: FastAPI 요청 객체
            
        Returns:
            StreamingResponse: SSE 스트리밍 응답
        """
        client_id = str(uuid.uuid4())
        
        # 클라이언트 정보 저장
        queue = asyncio.Queue()
        self._clients[client_id] = {
            "queue": queue,
            "connected": True
        }
        
        logger.info(f"New SSE client connected: {client_id}")
        
        # SSE 스트림 생성
        async def event_generator():
            try:
                while self._running and self._clients.get(client_id, {}).get("connected", False):
                    # 메시지 대기
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30)
                        
                        # 메시지 인코딩 및 전송
                        yield f"data: {json.dumps(message)}\n\n"
                        
                        # 큐 태스크 완료 표시
                        queue.task_done()
                    
                    except asyncio.TimeoutError:
                        # Keep-alive 메시지 전송
                        yield ": keep-alive\n\n"
            
            except asyncio.CancelledError:
                pass
            
            finally:
                # 연결 종료 시 클라이언트 정보 삭제
                if client_id in self._clients:
                    self._clients[client_id]["connected"] = False
                    del self._clients[client_id]
                    logger.info(f"SSE client disconnected: {client_id}")
        
        # 클라이언트 연결 종료 시 정리 작업
        async def on_disconnect():
            if client_id in self._clients:
                self._clients[client_id]["connected"] = False
                del self._clients[client_id]
                logger.info(f"SSE client disconnected: {client_id}")
        
        # SSE 응답 반환
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            background=BackgroundTask(on_disconnect)
        )
    
    async def _handle_message(self, request: Request) -> Response:
        """클라이언트 메시지 처리
        
        Args:
            request: FastAPI 요청 객체
            
        Returns:
            Response: JSON 응답
        """
        try:
            # 요청 본문 파싱
            body = await request.json()
            
            # JSON-RPC 요청 검증
            json_rpc_request = JsonRpcRequest.parse_obj(body)
            
            # 메시지 처리 및 응답
            response = await self._message_handler(json_rpc_request.dict())
            
            return Response(
                content=json.dumps(response),
                media_type="application/json"
            )
        
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON request")
            error_response = self._create_parse_error()
            
            return Response(
                content=json.dumps(error_response),
                media_type="application/json",
                status_code=400
            )
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_response = {
                "jsonrpc": "2.0",
                "id": body.get("id") if "id" in body else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            
            return Response(
                content=json.dumps(error_response),
                media_type="application/json",
                status_code=500
            )
    
    async def send(self, message: Dict[str, Any]) -> None:
        """메시지 전송
        
        클라이언트에 메시지를 전송합니다.
        
        Args:
            message: 전송할 메시지
        """
        if not self._running:
            logger.warning("Transport not running, cannot send message")
            return
        
        try:
            # 알림 메시지는 SSE로 전송, 응답 메시지는 POST 응답으로 전송됨
            if "method" in message and "id" not in message:
                # 모든 클라이언트에게 알림 전송
                for client_id, client in list(self._clients.items()):
                    if client.get("connected", False):
                        try:
                            await client["queue"].put(message)
                            logger.debug(f"Sent notification to client {client_id}: {json.dumps(message)[:100]}...")
                        except Exception as e:
                            logger.error(f"Error sending notification to client {client_id}: {str(e)}")
                            # 연결에 문제가 있는 클라이언트 제거
                            client["connected"] = False
            
            # "id"가 있는 메시지는 POST 요청에 대한 응답이므로 여기서 처리하지 않음
        
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def close(self) -> None:
        """트랜스포트 종료"""
        self._running = False
        
        # 모든 클라이언트 연결 종료
        for client_id, client in list(self._clients.items()):
            client["connected"] = False
        
        self._clients.clear()
        logger.info("SSE transport closed")
