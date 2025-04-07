"""
간단한 MCP 클라이언트 예제

이 예제는 MCP 서버에 연결하여 리소스를 읽고 도구를 호출하는 간단한 클라이언트를 구현합니다.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# 부모 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.mcp_standard import MCPClient
from backend.mcp_standard.transports.client import StdioClientTransport

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("mcp.example")


class SimpleClient:
    """간단한 MCP 클라이언트 예제"""
    
    def __init__(self, server_command: str, server_args: List[str] = None):
        """
        Args:
            server_command: 서버 실행 명령어
            server_args: 서버 명령행 인자 목록
        """
        self.server_command = server_command
        self.server_args = server_args or []
        
        # MCP 클라이언트 생성
        self.client = MCPClient("simple-client", "1.0.0")
        
        # 이벤트 콜백 등록
        self.client.on_resources_changed(self._on_resources_changed)
        self.client.on_tools_changed(self._on_tools_changed)
        self.client.on_resource_updated(self._on_resource_updated)
        self.client.on_logging(self._on_logging)
    
    async def _on_resources_changed(self) -> None:
        """리소스 목록 변경 이벤트 콜백"""
        logger.info(f"Resources changed: {len(self.client.resources)} available")
        
        for resource in self.client.resources:
            if resource.uri:
                logger.info(f"  - {resource.name}: {resource.uri}")
            elif resource.uriTemplate:
                logger.info(f"  - {resource.name}: {resource.uriTemplate}")
    
    async def _on_tools_changed(self) -> None:
        """도구 목록 변경 이벤트 콜백"""
        logger.info(f"Tools changed: {len(self.client.tools)} available")
        
        for tool in self.client.tools:
            logger.info(f"  - {tool.name}: {tool.description}")
    
    async def _on_resource_updated(self, uri: str) -> None:
        """리소스 업데이트 이벤트 콜백"""
        logger.info(f"Resource updated: {uri}")
    
    async def _on_logging(self, message) -> None:
        """로깅 이벤트 콜백"""
        log_level = getattr(logging, message.level.upper(), logging.INFO)
        logger.log(log_level, f"Server log: [{message.logger}] {message.data}")
    
    async def connect_and_initialize(self) -> None:
        """서버 연결 및 초기화"""
        # 트랜스포트 생성
        transport = StdioClientTransport(
            command=self.server_command,
            args=self.server_args
        )
        
        # 클라이언트 연결
        await self.client.connect(transport)
        
        # 서버 초기화
        result = await self.client.initialize()
        logger.info(f"Connected to server: {result['name']} v{result['version']}")
        logger.info(f"Server capabilities: {result['capabilities']}")
    
    async def run_demo(self) -> None:
        """데모 실행"""
        # 현재 디렉토리 리소스 읽기
        try:
            logger.info("Reading current directory...")
            result = await self.client.read_resource("dir:///")
            logger.info(f"Directory contents:\n{result.contents[0].text}")
        except Exception as e:
            logger.error(f"Error reading directory: {str(e)}")
        
        # 계산기 도구 호출
        try:
            logger.info("Calling calculator tool...")
            result = await self.client.call_tool("calculator", {
                "operation": "add",
                "a": 10,
                "b": 20
            })
            logger.info(f"Calculator result: {result.content[0].text}")
        except Exception as e:
            logger.error(f"Error calling calculator tool: {str(e)}")
        
        # 파일 검색 도구 호출
        try:
            logger.info("Calling file search tool...")
            result = await self.client.call_tool("file_search", {
                "pattern": "*.py",
                "path": ".",
                "recursive": False
            })
            logger.info(f"Search result:\n{result.content[0].text}")
        except Exception as e:
            logger.error(f"Error calling file search tool: {str(e)}")
    
    async def run(self) -> None:
        """클라이언트 실행"""
        try:
            # 서버 연결 및 초기화
            await self.connect_and_initialize()
            
            # 데모 실행
            await self.run_demo()
            
            # 대화형 모드 (Ctrl+C로 중단될 때까지)
            logger.info("Client is running. Press Ctrl+C to exit.")
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Client cancelled")
        except KeyboardInterrupt:
            logger.info("Client interrupted")
        finally:
            # 클라이언트 종료
            await self.client.close()
            logger.info("Client closed")


async def main():
    """메인 함수"""
    # 서버 명령어 설정
    # 서버 예제를 Python으로 실행
    server_command = sys.executable
    server_args = [os.path.join(os.path.dirname(__file__), "simple_server.py")]
    
    # 명령행 인자가 있는 경우 기본 디렉토리 추가
    if len(sys.argv) > 1:
        server_args.append(sys.argv[1])
    
    # 클라이언트 생성 및 실행
    client = SimpleClient(server_command, server_args)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
