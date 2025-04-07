"""
Model Context Protocol (MCP) 패키지
"""

from .api import router, mcp_handler
from .handler import MCPHandler
from .function_registry import register_all_functions

# 초기화 시 모든 MCP 함수 등록
register_all_functions(mcp_handler)

__all__ = ['router', 'mcp_handler', 'MCPHandler']
