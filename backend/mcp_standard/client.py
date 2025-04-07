"""
Model Context Protocol (MCP) 클라이언트 구현

이 모듈은 MCP 표준에 따른 클라이언트 구현을 제공합니다.
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, Awaitable, TypeVar

from .types import (
    MCPResource, MCPTool, MCPPrompt, ReadResourceResult, ToolCallResult,
    GetPromptResult, SamplingCreateMessageRequest, LoggingMessage, LogLevel
)

logger = logging.getLogger("mcp.client")

T = TypeVar('T')


class MCPClient:
    """MCP 클라이언트
    
    Model Context Protocol을 구현하는 클라이언트 클래스입니다.
    서버에 연결하여 리소스, 도구, 프롬프트 등의 기능을 사용할 수 있습니다.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Args:
            name: 클라이언트 이름
            version: 클라이언트 버전
        """
        self.name = name
        self.version = version
        
        # 서버 정보
        self.server_name: Optional[str] = None
        self.server_version: Optional[str] = None
        self.server_capabilities: Dict[str, Any] = {}
        
        # 클라이언트 기능
        self.capabilities = {
            "logging": {
                "minLevel": LogLevel.INFO
            },
            "roots": True,
            "sampling": True
        }
        
        # 기능 저장소
        self.resources: List[MCPResource] = []
        self.tools: List[MCPTool] = []
        self.prompts: List[MCPPrompt] = []
        
        # 트랜스포트 및 상태
        self._transport = None
        self._initialized = False
        self._message_handlers: Dict[str, Callable] = {}
        self._request_futures: Dict[str, asyncio.Future] = {}
        
        # 이벤트 콜백
        self._on_resource_updated: Optional[Callable[[str], Awaitable[None]]] = None
        self._on_resources_changed: Optional[Callable[[], Awaitable[None]]] = None
        self._on_tools_changed: Optional[Callable[[], Awaitable[None]]] = None
        self._on_prompts_changed: Optional[Callable[[], Awaitable[None]]] = None
        self._on_logging: Optional[Callable[[LoggingMessage], Awaitable[None]]] = None
        
        # 기본 알림 핸들러 등록
        self._register_notification_handlers()
        
        logger.info(f"Initialized MCP Client: {name} v{version}")
    
    def _register_notification_handlers(self) -> None:
        """기본 알림 핸들러 등록"""
        self._message_handlers["notifications/resources/list_changed"] = self._handle_resources_list_changed
        self._message_handlers["notifications/resources/updated"] = self._handle_resource_updated
        self._message_handlers["notifications/tools/list_changed"] = self._handle_tools_list_changed
        self._message_handlers["notifications/prompts/list_changed"] = self._handle_prompts_list_changed
        self._message_handlers["notifications/logging"] = self._handle_logging_notification
    
    async def connect(self, transport) -> None:
        """트랜스포트에 연결
        
        Args:
            transport: MCP 트랜스포트 인스턴스
        """
        self._transport = transport
        await transport.start(self._handle_message)
        logger.info(f"MCP Client connected to transport: {transport.__class__.__name__}")
    
    async def initialize(self) -> Dict[str, Any]:
        """서버 초기화
        
        서버에 초기화 요청을 보내고 기능 협상을 수행합니다.
        
        Returns:
            Dict[str, Any]: 초기화 결과
        """
        if self._initialized:
            logger.warning("MCP Client already initialized")
            return {
                "name": self.server_name,
                "version": self.server_version,
                "capabilities": self.server_capabilities
            }
        
        # 초기화 요청 전송
        response = await self._send_request(
            "initialize",
            {
                "name": self.name,
                "version": self.version,
                "capabilities": self.capabilities
            }
        )
        
        # 서버 정보 저장
        result = response.get("result", {})
        self.server_name = result.get("name")
        self.server_version = result.get("version")
        self.server_capabilities = result.get("capabilities", {})
        
        # 초기화 완료 알림 전송
        await self._send_notification("initialized", {})
        
        self._initialized = True
        logger.info(f"MCP Client initialized, connected to server: {self.server_name} v{self.server_version}")
        
        # 리소스, 도구, 프롬프트 목록 가져오기
        await self._refresh_resources()
        await self._refresh_tools()
        await self._refresh_prompts()
        
        return result
    
    async def _handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """메시지 처리
        
        Args:
            message: JSON-RPC 메시지
            
        Returns:
            Optional[Dict[str, Any]]: 응답 메시지 (필요한 경우)
        """
        try:
            # 응답 메시지 처리
            if "id" in message and ("result" in message or "error" in message):
                request_id = message["id"]
                if request_id in self._request_futures:
                    future = self._request_futures.pop(request_id)
                    if not future.done():
                        future.set_result(message)
                    return None
            
            # 요청 메시지 처리
            elif "method" in message and "id" in message:
                method = message["method"]
                params = message.get("params", {})
                
                # 요청 메서드 처리기가 있는 경우 호출
                if method in self._message_handlers:
                    handler = self._message_handlers[method]
                    result = await handler(params) if asyncio.iscoroutinefunction(handler) else handler(params)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": result
                    }
                
                # 지원하지 않는 메서드
                return {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Method '{method}' not supported"
                    }
                }
            
            # 알림 메시지 처리
            elif "method" in message:
                method = message["method"]
                params = message.get("params", {})
                
                # 알림 메서드 처리기가 있는 경우 호출
                if method in self._message_handlers:
                    handler = self._message_handlers[method]
                    await handler(params) if asyncio.iscoroutinefunction(handler) else handler(params)
                
                return None
            
            # 알 수 없는 메시지 형식
            logger.warning(f"Unknown message format: {message}")
            return None
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            # 요청에 대한 오류 응답 반환
            if "id" in message:
                return {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
            return None
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """요청 전송
        
        Args:
            method: 요청 메서드
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
            
        Raises:
            RuntimeError: 트랜스포트가 연결되지 않은 경우
            asyncio.TimeoutError: 응답 대기 시간 초과
            Exception: 기타 오류
        """
        if not self._transport:
            raise RuntimeError("Transport not connected")
        
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 요청 메시지 생성
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        
        if params is not None:
            request["params"] = params
        
        # 응답을 기다릴 Future 생성
        future = asyncio.get_event_loop().create_future()
        self._request_futures[request_id] = future
        
        try:
            # 요청 전송
            await self._transport.send(request)
            
            # 응답 대기 (30초 타임아웃)
            response = await asyncio.wait_for(future, 30.0)
            
            # 오류 응답 처리
            if "error" in response:
                error = response["error"]
                raise Exception(f"Server error: {error.get('message', 'Unknown error')} ({error.get('code')})")
            
            return response
            
        except asyncio.TimeoutError:
            # 타임아웃 시 Future 제거
            if request_id in self._request_futures:
                del self._request_futures[request_id]
            
            raise asyncio.TimeoutError(f"Request timed out: {method}")
            
        except Exception as e:
            # 오류 발생 시 Future 제거
            if request_id in self._request_futures:
                del self._request_futures[request_id]
            
            logger.error(f"Error sending request '{method}': {str(e)}")
            raise
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """알림 전송
        
        Args:
            method: 알림 메서드
            params: 알림 파라미터
            
        Raises:
            RuntimeError: 트랜스포트가 연결되지 않은 경우
        """
        if not self._transport:
            raise RuntimeError("Transport not connected")
        
        # 알림 메시지 생성
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            notification["params"] = params
        
        # 알림 전송
        await self._transport.send(notification)
    
    async def _refresh_resources(self) -> None:
        """리소스 목록 갱신"""
        if not self._initialized:
            logger.warning("Cannot refresh resources: client not initialized")
            return
        
        if not self.server_capabilities.get("resources"):
            logger.info("Server does not support resources")
            return
        
        try:
            response = await self._send_request("resources/list")
            self.resources = response.get("result", {}).get("resources", [])
            logger.info(f"Refreshed resources: {len(self.resources)} available")
        except Exception as e:
            logger.error(f"Error refreshing resources: {str(e)}")
    
    async def _refresh_tools(self) -> None:
        """도구 목록 갱신"""
        if not self._initialized:
            logger.warning("Cannot refresh tools: client not initialized")
            return
        
        if not self.server_capabilities.get("tools"):
            logger.info("Server does not support tools")
            return
        
        try:
            response = await self._send_request("tools/list")
            self.tools = response.get("result", {}).get("tools", [])
            logger.info(f"Refreshed tools: {len(self.tools)} available")
        except Exception as e:
            logger.error(f"Error refreshing tools: {str(e)}")
    
    async def _refresh_prompts(self) -> None:
        """프롬프트 목록 갱신"""
        if not self._initialized:
            logger.warning("Cannot refresh prompts: client not initialized")
            return
        
        if not self.server_capabilities.get("prompts"):
            logger.info("Server does not support prompts")
            return
        
        try:
            response = await self._send_request("prompts/list")
            self.prompts = response.get("result", {}).get("prompts", [])
            logger.info(f"Refreshed prompts: {len(self.prompts)} available")
        except Exception as e:
            logger.error(f"Error refreshing prompts: {str(e)}")
    
    async def _handle_resources_list_changed(self, params: Dict[str, Any]) -> None:
        """리소스 목록 변경 알림 처리"""
        await self._refresh_resources()
        
        # 콜백 호출
        if self._on_resources_changed:
            await self._on_resources_changed()
    
    async def _handle_resource_updated(self, params: Dict[str, Any]) -> None:
        """리소스 업데이트 알림 처리"""
        uri = params.get("uri")
        if not uri:
            return
        
        # 콜백 호출
        if self._on_resource_updated:
            await self._on_resource_updated(uri)
    
    async def _handle_tools_list_changed(self, params: Dict[str, Any]) -> None:
        """도구 목록 변경 알림 처리"""
        await self._refresh_tools()
        
        # 콜백 호출
        if self._on_tools_changed:
            await self._on_tools_changed()
    
    async def _handle_prompts_list_changed(self, params: Dict[str, Any]) -> None:
        """프롬프트 목록 변경 알림 처리"""
        await self._refresh_prompts()
        
        # 콜백 호출
        if self._on_prompts_changed:
            await self._on_prompts_changed()
    
    async def _handle_logging_notification(self, params: Dict[str, Any]) -> None:
        """로깅 알림 처리"""
        message = LoggingMessage(**params)
        
        # 로깅 레벨 확인
        min_level = self.capabilities.get("logging", {}).get("minLevel", LogLevel.INFO)
        if LogLevel[message.level].value < LogLevel[min_level].value:
            return
        
        # 파이썬 로깅
        log_level = getattr(logging, message.level.upper(), logging.INFO)
        logger.log(log_level, f"[Server] {message.data}")
        
        # 콜백 호출
        if self._on_logging:
            await self._on_logging(message)
    
    async def set_logging_level(self, level: LogLevel) -> None:
        """로깅 레벨 설정
        
        Args:
            level: 로깅 레벨
        """
        self.capabilities["logging"]["minLevel"] = level
    
    def on_resource_updated(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """리소스 업데이트 이벤트 콜백 설정
        
        Args:
            callback: 콜백 함수 (resource_uri)
        """
        self._on_resource_updated = callback
    
    def on_resources_changed(self, callback: Callable[[], Awaitable[None]]) -> None:
        """리소스 목록 변경 이벤트 콜백 설정
        
        Args:
            callback: 콜백 함수
        """
        self._on_resources_changed = callback
    
    def on_tools_changed(self, callback: Callable[[], Awaitable[None]]) -> None:
        """도구 목록 변경 이벤트 콜백 설정
        
        Args:
            callback: 콜백 함수
        """
        self._on_tools_changed = callback
    
    def on_prompts_changed(self, callback: Callable[[], Awaitable[None]]) -> None:
        """프롬프트 목록 변경 이벤트 콜백 설정
        
        Args:
            callback: 콜백 함수
        """
        self._on_prompts_changed = callback
    
    def on_logging(self, callback: Callable[[LoggingMessage], Awaitable[None]]) -> None:
        """로깅 이벤트 콜백 설정
        
        Args:
            callback: 콜백 함수 (logging_message)
        """
        self._on_logging = callback
    
    # 리소스 API
    
    async def list_resources(self) -> List[MCPResource]:
        """리소스 목록 조회
        
        Returns:
            List[MCPResource]: 리소스 목록
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("resources"):
            raise RuntimeError("Server does not support resources")
        
        await self._refresh_resources()
        return self.resources
    
    async def read_resource(self, uri: str) -> ReadResourceResult:
        """리소스 읽기
        
        Args:
            uri: 리소스 URI
            
        Returns:
            ReadResourceResult: 리소스 내용
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 리소스를 지원하지 않는 경우
            Exception: 리소스 읽기 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("resources"):
            raise RuntimeError("Server does not support resources")
        
        try:
            response = await self._send_request("resources/read", {"uri": uri})
            result = response.get("result", {})
            return ReadResourceResult(**result)
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {str(e)}")
            raise
    
    async def subscribe_resource(self, uri: str) -> bool:
        """리소스 구독
        
        Args:
            uri: 리소스 URI
            
        Returns:
            bool: 구독 성공 여부
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 리소스를 지원하지 않는 경우
            Exception: 리소스 구독 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("resources"):
            raise RuntimeError("Server does not support resources")
        
        try:
            response = await self._send_request("resources/subscribe", {"uri": uri})
            result = response.get("result", {})
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Error subscribing to resource '{uri}': {str(e)}")
            raise
    
    async def unsubscribe_resource(self, uri: str) -> bool:
        """리소스 구독 해제
        
        Args:
            uri: 리소스 URI
            
        Returns:
            bool: 구독 해제 성공 여부
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 리소스를 지원하지 않는 경우
            Exception: 리소스 구독 해제 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("resources"):
            raise RuntimeError("Server does not support resources")
        
        try:
            response = await self._send_request("resources/unsubscribe", {"uri": uri})
            result = response.get("result", {})
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Error unsubscribing from resource '{uri}': {str(e)}")
            raise
    
    # 도구 API
    
    async def list_tools(self) -> List[MCPTool]:
        """도구 목록 조회
        
        Returns:
            List[MCPTool]: 도구 목록
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("tools"):
            raise RuntimeError("Server does not support tools")
        
        await self._refresh_tools()
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> ToolCallResult:
        """도구 호출
        
        Args:
            name: 도구 이름
            arguments: 도구 인자
            
        Returns:
            ToolCallResult: 도구 호출 결과
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 도구를 지원하지 않는 경우
            Exception: 도구 호출 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("tools"):
            raise RuntimeError("Server does not support tools")
        
        if arguments is None:
            arguments = {}
        
        try:
            response = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            result = response.get("result", {})
            return ToolCallResult(**result)
        except Exception as e:
            logger.error(f"Error calling tool '{name}': {str(e)}")
            raise
    
    # 프롬프트 API
    
    async def list_prompts(self) -> List[MCPPrompt]:
        """프롬프트 목록 조회
        
        Returns:
            List[MCPPrompt]: 프롬프트 목록
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("prompts"):
            raise RuntimeError("Server does not support prompts")
        
        await self._refresh_prompts()
        return self.prompts
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> GetPromptResult:
        """프롬프트 가져오기
        
        Args:
            name: 프롬프트 이름
            arguments: 프롬프트 인자
            
        Returns:
            GetPromptResult: 프롬프트 결과
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 프롬프트를 지원하지 않는 경우
            Exception: 프롬프트 가져오기 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.server_capabilities.get("prompts"):
            raise RuntimeError("Server does not support prompts")
        
        if arguments is None:
            arguments = {}
        
        try:
            response = await self._send_request("prompts/get", {
                "name": name,
                "arguments": arguments
            })
            result = response.get("result", {})
            return GetPromptResult(**result)
        except Exception as e:
            logger.error(f"Error getting prompt '{name}': {str(e)}")
            raise
    
    # Sampling API
    
    async def create_message(self, request: SamplingCreateMessageRequest) -> Dict[str, Any]:
        """샘플링 메시지 생성
        
        Args:
            request: 샘플링 요청
            
        Returns:
            Dict[str, Any]: 샘플링 결과
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 샘플링을 지원하지 않는 경우
            Exception: 샘플링 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.capabilities.get("sampling"):
            raise RuntimeError("Client does not support sampling")
        
        # 추후 구현 예정 (현재는 더미 응답 반환)
        logger.warning("Sampling API not implemented, returning dummy response")
        return {
            "model": "dummy-model",
            "content": {
                "type": "text",
                "text": "This is a dummy response. Sampling API not implemented."
            },
            "stopReason": "dummy"
        }
    
    # Roots API
    
    async def add_root(self, uri: str, name: str = None) -> bool:
        """루트 추가
        
        Args:
            uri: 루트 URI
            name: 루트 이름
            
        Returns:
            bool: 추가 성공 여부
            
        Raises:
            RuntimeError: 클라이언트가 초기화되지 않았거나 서버가 루트를 지원하지 않는 경우
            Exception: 루트 추가 중 오류 발생
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        if not self.capabilities.get("roots"):
            raise RuntimeError("Client does not support roots")
        
        # 추후 구현 예정 (현재는 더미 응답 반환)
        logger.warning("Roots API not implemented, returning dummy response")
        return True
    
    async def close(self) -> None:
        """클라이언트 종료"""
        try:
            if self._transport:
                await self._transport.close()
                logger.info("MCP Client closed")
        except Exception as e:
            logger.error(f"Error closing client: {str(e)}")
