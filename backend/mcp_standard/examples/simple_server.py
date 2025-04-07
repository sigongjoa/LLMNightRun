"""
간단한 MCP 서버 예제

이 예제는 파일 시스템 리소스와 계산기 도구를 제공하는 간단한 MCP 서버를 구현합니다.
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

from backend.mcp_standard import (
    MCPServer, StdioServerTransport, MCPResource, MCPTool, 
    ReadResourceResult, ToolCallResult, LogLevel
)
from backend.mcp_standard.types import ResourceContent, TextContent, ToolContent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("mcp.example")


class SimpleServer:
    """간단한 MCP 서버 예제"""
    
    def __init__(self, base_dir: str = None):
        """
        Args:
            base_dir: 기본 디렉토리 경로 (None인 경우 현재 디렉토리)
        """
        # 기본 디렉토리 설정
        self.base_dir = Path(base_dir or os.getcwd())
        logger.info(f"Base directory: {self.base_dir}")
        
        # MCP 서버 생성
        self.server = MCPServer("simple-server", "1.0.0")
        
        # 리소스 등록
        self._register_resources()
        
        # 도구 등록
        self._register_tools()
    
    def _register_resources(self) -> None:
        """리소스 등록"""
        # 파일 리소스
        file_resource = MCPResource(
            uriTemplate="file:///{path}",
            name="File",
            description="Access files in the server's file system"
        )
        self.server.add_resource(file_resource, self._handle_file_resource)
        
        # 디렉토리 리소스
        dir_resource = MCPResource(
            uriTemplate="dir:///{path}",
            name="Directory",
            description="Access directories in the server's file system"
        )
        self.server.add_resource(dir_resource, self._handle_dir_resource)
    
    def _register_tools(self) -> None:
        """도구 등록"""
        # 계산기 도구
        calculator_tool = MCPTool(
            name="calculator",
            description="Perform basic arithmetic operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "The first operand"
                    },
                    "b": {
                        "type": "number",
                        "description": "The second operand"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        )
        self.server.add_tool(calculator_tool, self._handle_calculator_tool)
        
        # 파일 검색 도구
        search_tool = MCPTool(
            name="file_search",
            description="Search for files in the server's file system",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The search pattern"
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory path to search in"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to search recursively"
                    }
                },
                "required": ["pattern", "path"]
            }
        )
        self.server.add_tool(search_tool, self._handle_search_tool)
    
    async def _handle_file_resource(self, uri: str) -> ReadResourceResult:
        """파일 리소스 핸들러
        
        Args:
            uri: 리소스 URI
            
        Returns:
            ReadResourceResult: 리소스 내용
        """
        # URI에서 경로 추출
        path_match = uri.split("file:///", 1)
        if len(path_match) != 2:
            raise ValueError(f"Invalid file URI: {uri}")
        
        path_str = path_match[1]
        path = (self.base_dir / path_str).resolve()
        
        # 경로 검증 (기본 디렉토리 외부 접근 방지)
        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Access denied: {path}")
        
        # 파일 존재 확인
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # 파일 내용 읽기
        try:
            content = path.read_text(encoding='utf-8')
            
            # MIME 타입 추정
            mime_type = "text/plain"
            if path.suffix == ".json":
                mime_type = "application/json"
            elif path.suffix == ".html":
                mime_type = "text/html"
            elif path.suffix == ".md":
                mime_type = "text/markdown"
            elif path.suffix == ".css":
                mime_type = "text/css"
            elif path.suffix == ".js":
                mime_type = "text/javascript"
            elif path.suffix == ".py":
                mime_type = "text/x-python"
            
            # 리소스 내용 반환
            return ReadResourceResult(
                contents=[
                    ResourceContent(
                        uri=uri,
                        text=content,
                        mimeType=mime_type
                    )
                ]
            )
            
        except UnicodeDecodeError:
            # 바이너리 파일로 처리 (base64 인코딩)
            try:
                import base64
                content = base64.b64encode(path.read_bytes()).decode('ascii')
                
                # MIME 타입 추정
                mime_type = "application/octet-stream"
                if path.suffix in [".png", ".jpg", ".jpeg", ".gif"]:
                    mime_type = f"image/{path.suffix[1:]}"
                elif path.suffix == ".pdf":
                    mime_type = "application/pdf"
                
                # 리소스 내용 반환
                return ReadResourceResult(
                    contents=[
                        ResourceContent(
                            uri=uri,
                            blob=content,
                            mimeType=mime_type
                        )
                    ]
                )
                
            except Exception as e:
                raise ValueError(f"Failed to read binary file: {path} - {str(e)}")
            
        except Exception as e:
            raise ValueError(f"Failed to read file: {path} - {str(e)}")
    
    async def _handle_dir_resource(self, uri: str) -> ReadResourceResult:
        """디렉토리 리소스 핸들러
        
        Args:
            uri: 리소스 URI
            
        Returns:
            ReadResourceResult: 리소스 내용
        """
        # URI에서 경로 추출
        path_match = uri.split("dir:///", 1)
        if len(path_match) != 2:
            raise ValueError(f"Invalid directory URI: {uri}")
        
        path_str = path_match[1]
        path = (self.base_dir / path_str).resolve()
        
        # 경로 검증 (기본 디렉토리 외부 접근 방지)
        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Access denied: {path}")
        
        # 디렉토리 존재 확인
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        # 디렉토리 내용 읽기
        try:
            # 파일 및 디렉토리 목록 생성
            files = []
            directories = []
            
            for item in path.iterdir():
                if item.is_file():
                    files.append(f"[FILE] {item.name}")
                elif item.is_dir():
                    directories.append(f"[DIR] {item.name}")
            
            # 정렬
            files.sort()
            directories.sort()
            
            # 목록 텍스트 생성
            content = "\n".join(directories + files)
            
            # 리소스 내용 반환
            return ReadResourceResult(
                contents=[
                    ResourceContent(
                        uri=uri,
                        text=content,
                        mimeType="text/plain"
                    )
                ]
            )
            
        except Exception as e:
            raise ValueError(f"Failed to read directory: {path} - {str(e)}")
    
    async def _handle_calculator_tool(self, arguments: Dict[str, Any]) -> ToolCallResult:
        """계산기 도구 핸들러
        
        Args:
            arguments: 도구 인자
            
        Returns:
            ToolCallResult: 도구 실행 결과
        """
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")
        
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text="Both operands must be numbers"
                    )
                ],
                isError=True
            )
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolCallResult(
                        content=[
                            ToolContent(
                                type="text",
                                text="Division by zero is not allowed"
                            )
                        ],
                        isError=True
                    )
                result = a / b
            else:
                return ToolCallResult(
                    content=[
                        ToolContent(
                            type="text",
                            text=f"Unknown operation: {operation}"
                        )
                    ],
                    isError=True
                )
            
            # 결과 반환
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Result: {result}"
                    )
                ]
            )
            
        except Exception as e:
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ],
                isError=True
            )
    
    async def _handle_search_tool(self, arguments: Dict[str, Any]) -> ToolCallResult:
        """파일 검색 도구 핸들러
        
        Args:
            arguments: 도구 인자
            
        Returns:
            ToolCallResult: 도구 실행 결과
        """
        pattern = arguments.get("pattern")
        path_str = arguments.get("path")
        recursive = arguments.get("recursive", False)
        
        if not pattern or not path_str:
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text="Pattern and path are required"
                    )
                ],
                isError=True
            )
        
        # 경로 검증
        path = (self.base_dir / path_str).resolve()
        
        # 경로 검증 (기본 디렉토리 외부 접근 방지)
        if not str(path).startswith(str(self.base_dir)):
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Access denied: {path}"
                    )
                ],
                isError=True
            )
        
        # 디렉토리 존재 확인
        if not path.exists():
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Directory not found: {path}"
                    )
                ],
                isError=True
            )
        
        if not path.is_dir():
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Not a directory: {path}"
                    )
                ],
                isError=True
            )
        
        # 파일 검색
        try:
            import fnmatch
            
            matches = []
            
            if recursive:
                for root, dirnames, filenames in os.walk(path):
                    for filename in fnmatch.filter(filenames, pattern):
                        relative_path = os.path.relpath(os.path.join(root, filename), path)
                        matches.append(relative_path)
            else:
                for item in path.iterdir():
                    if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                        matches.append(item.name)
            
            # 결과 정렬
            matches.sort()
            
            # 결과 텍스트 생성
            if matches:
                result_text = f"Found {len(matches)} matching files:\n" + "\n".join(matches)
            else:
                result_text = f"No files matching '{pattern}' found in {path_str}"
            
            # 결과 반환
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=result_text
                    )
                ]
            )
            
        except Exception as e:
            return ToolCallResult(
                content=[
                    ToolContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ],
                isError=True
            )
    
    async def run(self) -> None:
        """서버 실행"""
        # 로깅 알림 전송 (샘플)
        await self.server.send_logging_notification({
            "level": LogLevel.INFO,
            "logger": "simple-server",
            "data": "Simple server started"
        })
        
        # 트랜스포트 생성 및 연결
        transport = StdioServerTransport()
        await self.server.connect(transport)
        
        try:
            # 서버 실행 유지 (Ctrl+C로 중단될 때까지)
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Server cancelled")
        except KeyboardInterrupt:
            logger.info("Server interrupted")
        finally:
            # 서버 종료
            await self.server.close()
            logger.info("Server closed")


async def main():
    """메인 함수"""
    # 명령행 인자에서 기본 디렉토리 설정
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.getcwd()
    
    # 서버 생성 및 실행
    server = SimpleServer(base_dir)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
