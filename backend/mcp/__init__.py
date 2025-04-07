"""
Model Context Protocol (MCP) 패키지
"""

from .api import router, mcp_handler
from .handler import MCPHandler
from .register import register_mcp_functions, create_function_context
from .websocket import router as websocket_router
from .function_registry import register_all_functions

# 초기화 시 모든 MCP 함수 등록
register_all_functions(mcp_handler)

# 브라우저 콘솔 및 터미널 함수 등록
register_mcp_functions(mcp_handler)
create_function_context(mcp_handler)

__all__ = ['router', 'websocket_router', 'mcp_handler', 'MCPHandler']
