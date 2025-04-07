"""
Model Context Protocol (MCP) 서버 구현

이 모듈은 MCP 표준에 따른 서버 구현을 제공합니다.
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, Awaitable, TypeVar

from .types import (
    MCPResource, MCPTool, MCPPrompt, ToolCallResult, PromptMessage,
    ResourceContent, ReadResourceResult, GetPromptResult, LoggingMessage
)

logger = logging.getLogger("mcp")

T = TypeVar('T')
SyncOrAsyncCallable = Union[Callable[..., T], Callable[..., Awaitable[T]]]


class MCPServer:
    """MCP 서버
    
    Model Context Protocol을 구현하는 서버 클래스입니다.
    리소스, 도구, 프롬프트를 노출하고 관리합니다.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Args:
            name: 서버 이름
            version: 서버 버전
        """
        self.name = name
        self.version = version
        
        # 기능 저장소
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        
        # 핸들러 저장소
        self._resource_handlers: Dict[str, SyncOrAsyncCallable[ReadResourceResult]] = {}
        self._tool_handlers: Dict[str, SyncOrAsyncCallable[ToolCallResult]] = {}
        self._prompt_handlers: Dict[str, SyncOrAsyncCallable[GetPromptResult]] = {}
        
        # 구독 관리
        self._resource_subscriptions: Dict[str, List[str]] = {}  # uri -> [client_id]
        
        # 트랜스포트 및 클라이언트
        self._transport = None
        self._client_capabilities = {}
        
        logger.info(f"Initialized MCP Server: {name} v{version}")
    
    async def connect(self, transport) -> None:
        """트랜스포트에 연결
        
        Args:
            transport: MCP 트랜스포트 인스턴스
        """
        self._transport = transport
        await transport.start(self._handle_message)
        logger.info(f"MCP Server connected to transport: {transport.__class__.__name__}")
    
    async def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리
        
        Args:
            message: JSON-RPC 메시지
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        try:
            if "method" not in message:
                return self._create_error_response(
                    message.get("id"), 
                    -32600, 
                    "Invalid Request",
                    "Method is required"
                )
            
            method = message["method"]
            params = message.get("params", {})
            
            # 초기화 요청
            if method == "initialize":
                return await self._handle_initialize(message["id"], params)
            
            # 리소스 요청
            elif method == "resources/list":
                return await self._handle_resources_list(message["id"], params)
            elif method == "resources/read":
                return await self._handle_resources_read(message["id"], params)
            elif method == "resources/subscribe":
                return await self._handle_resources_subscribe(message["id"], params)
            elif method == "resources/unsubscribe":
                return await self._handle_resources_unsubscribe(message["id"], params)
            
            # 도구 요청
            elif method == "tools/list":
                return await self._handle_tools_list(message["id"], params)
            elif method == "tools/call":
                return await self._handle_tools_call(message["id"], params)
            
            # 프롬프트 요청
            elif method == "prompts/list":
                return await self._handle_prompts_list(message["id"], params)
            elif method == "prompts/get":
                return await self._handle_prompts_get(message["id"], params)
            
            # 알 수 없는 요청
            else:
                return self._create_error_response(
                    message.get("id"), 
                    -32601, 
                    "Method not found",
                    f"Method '{method}' not supported"
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {str(e)}")
            return self._create_error_response(
                message.get("id"),
                -32603,
                "Internal error",
                str(e)
            )
    
    async def _handle_initialize(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """초기화 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        # 클라이언트 기능 저장
        self._client_capabilities = params.get("capabilities", {})
        
        # 서버 정보 및 지원하는 기능 반환
        capabilities = {
            "resources": bool(self.resources),
            "tools": bool(self.tools),
            "prompts": bool(self.prompts),
            "logging": True
        }
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "name": self.name,
                "version": self.version,
                "capabilities": capabilities
            }
        }
    
    async def _handle_resources_list(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """리소스 목록 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "resources": list(self.resources.values())
            }
        }
    
    async def _handle_resources_read(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """리소스 읽기 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        uri = params.get("uri")
        if not uri:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                "URI is required"
            )
        
        # URI에 해당하는 핸들러 찾기
        handler = None
        for resource_uri, resource_handler in self._resource_handlers.items():
            # 정확한 URI 매칭
            if resource_uri == uri:
                handler = resource_handler
                break
            # URI 템플릿 매칭 (간단한 구현)
            elif '{' in resource_uri and '}' in resource_uri:
                template_parts = resource_uri.split('/')
                uri_parts = uri.split('/')
                
                if len(template_parts) == len(uri_parts):
                    match = True
                    for tp, up in zip(template_parts, uri_parts):
                        if not (tp == up or ('{' in tp and '}' in tp)):
                            match = False
                            break
                    
                    if match:
                        handler = resource_handler
                        break
        
        if not handler:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                f"Resource not found: {uri}"
            )
        
        try:
            # 핸들러 호출 (동기 또는 비동기)
            import inspect
            if inspect.iscoroutinefunction(handler):
                result = await handler(uri)
            else:
                result = handler(uri)
            
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": result.dict()
            }
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {str(e)}")
            return self._create_error_response(
                id,
                -32603,
                "Internal error",
                f"Error reading resource: {str(e)}"
            )
    
    async def _handle_resources_subscribe(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """리소스 구독 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        uri = params.get("uri")
        client_id = params.get("clientId", "default")
        
        if not uri:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                "URI is required"
            )
        
        if uri not in self._resource_subscriptions:
            self._resource_subscriptions[uri] = []
        
        if client_id not in self._resource_subscriptions[uri]:
            self._resource_subscriptions[uri].append(client_id)
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "success": True
            }
        }
    
    async def _handle_resources_unsubscribe(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """리소스 구독 해제 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        uri = params.get("uri")
        client_id = params.get("clientId", "default")
        
        if not uri:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                "URI is required"
            )
        
        if uri in self._resource_subscriptions and client_id in self._resource_subscriptions[uri]:
            self._resource_subscriptions[uri].remove(client_id)
            if not self._resource_subscriptions[uri]:
                del self._resource_subscriptions[uri]
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "success": True
            }
        }
    
    async def _handle_tools_list(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 목록 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tools_call(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                "Tool name is required"
            )
        
        if tool_name not in self._tool_handlers:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                f"Tool not found: {tool_name}"
            )
        
        try:
            handler = self._tool_handlers[tool_name]
            
            # 핸들러 호출 (동기 또는 비동기)
            import inspect
            if inspect.iscoroutinefunction(handler):
                result = await handler(arguments)
            else:
                result = handler(arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": result.dict()
            }
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {str(e)}")
            return self._create_error_response(
                id,
                -32603,
                "Internal error",
                f"Error calling tool: {str(e)}"
            )
    
    async def _handle_prompts_list(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 목록 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "prompts": list(self.prompts.values())
            }
        }
    
    async def _handle_prompts_get(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 가져오기 요청 처리
        
        Args:
            id: 요청 ID
            params: 요청 파라미터
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not prompt_name:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                "Prompt name is required"
            )
        
        if prompt_name not in self._prompt_handlers:
            return self._create_error_response(
                id, 
                -32602, 
                "Invalid params",
                f"Prompt not found: {prompt_name}"
            )
        
        try:
            handler = self._prompt_handlers[prompt_name]
            
            # 핸들러 호출 (동기 또는 비동기)
            import inspect
            if inspect.iscoroutinefunction(handler):
                result = await handler(arguments)
            else:
                result = handler(arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": result.dict()
            }
        except Exception as e:
            logger.error(f"Error getting prompt '{prompt_name}': {str(e)}")
            return self._create_error_response(
                id,
                -32603,
                "Internal error",
                f"Error getting prompt: {str(e)}"
            )
    
    def _create_error_response(self, id: str, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """에러 응답 생성
        
        Args:
            id: 요청 ID
            code: 에러 코드
            message: 에러 메시지
            data: 추가 에러 데이터
            
        Returns:
            Dict[str, Any]: 에러 응답 메시지
        """
        error = {
            "code": code,
            "message": message
        }
        
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": error
        }
    
    def add_resource(self, resource: MCPResource, handler: SyncOrAsyncCallable[ReadResourceResult]) -> None:
        """리소스 추가
        
        Args:
            resource: 리소스 정의
            handler: 리소스 핸들러 함수
        """
        resource_id = resource.uri or resource.uriTemplate
        if not resource_id:
            raise ValueError("Resource must have either uri or uriTemplate")
        
        self.resources[resource_id] = resource
        self._resource_handlers[resource_id] = handler
        logger.info(f"Added resource: {resource.name} ({resource_id})")
    
    def add_tool(self, tool: MCPTool, handler: SyncOrAsyncCallable[ToolCallResult]) -> None:
        """도구 추가
        
        Args:
            tool: 도구 정의
            handler: 도구 핸들러 함수
        """
        self.tools[tool.name] = tool
        self._tool_handlers[tool.name] = handler
        logger.info(f"Added tool: {tool.name}")
    
    def add_prompt(self, prompt: MCPPrompt, handler: SyncOrAsyncCallable[GetPromptResult]) -> None:
        """프롬프트 추가
        
        Args:
            prompt: 프롬프트 정의
            handler: 프롬프트 핸들러 함수
        """
        self.prompts[prompt.name] = prompt
        self._prompt_handlers[prompt.name] = handler
        logger.info(f"Added prompt: {prompt.name}")
    
    async def send_resource_updated_notification(self, uri: str) -> None:
        """리소스 업데이트 알림 전송
        
        Args:
            uri: 업데이트된 리소스 URI
        """
        if not self._transport:
            logger.warning("Cannot send notification: transport not connected")
            return
        
        if uri not in self._resource_subscriptions:
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/resources/updated",
            "params": {
                "uri": uri,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self._transport.send(notification)
        logger.debug(f"Sent resource updated notification for {uri}")
    
    async def send_tools_list_changed_notification(self) -> None:
        """도구 목록 변경 알림 전송"""
        if not self._transport:
            logger.warning("Cannot send notification: transport not connected")
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed"
        }
        
        await self._transport.send(notification)
        logger.debug("Sent tools list changed notification")
    
    async def send_prompts_list_changed_notification(self) -> None:
        """프롬프트 목록 변경 알림 전송"""
        if not self._transport:
            logger.warning("Cannot send notification: transport not connected")
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/prompts/list_changed"
        }
        
        await self._transport.send(notification)
        logger.debug("Sent prompts list changed notification")
    
    async def send_resources_list_changed_notification(self) -> None:
        """리소스 목록 변경 알림 전송"""
        if not self._transport:
            logger.warning("Cannot send notification: transport not connected")
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/resources/list_changed"
        }
        
        await self._transport.send(notification)
        logger.debug("Sent resources list changed notification")
    
    async def send_logging_notification(self, message: LoggingMessage) -> None:
        """로깅 알림 전송
        
        Args:
            message: 로깅 메시지
        """
        if not self._transport:
            logger.warning("Cannot send notification: transport not connected")
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/logging",
            "params": message.dict()
        }
        
        await self._transport.send(notification)
    
    async def close(self) -> None:
        """서버 종료"""
        if self._transport:
            await self._transport.close()
            logger.info("MCP Server closed")
