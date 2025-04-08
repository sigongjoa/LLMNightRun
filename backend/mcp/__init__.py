"""
MCP (Model Context Protocol) integration for LLMNightRun.
"""

from fastapi import APIRouter

from .routes import router
from .websocket import router as websocket_router, start_background_tasks
from .api import router as api_router
from .chat_websocket import router as chat_ws_router

# Start the WebSocket background tasks
start_background_tasks()

__all__ = ['router', 'websocket_router', 'api_router', 'chat_ws_router']
