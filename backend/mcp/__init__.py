"""
MCP (Model Context Protocol) integration for LLMNightRun.
"""

from fastapi import APIRouter

from .routes import router
from .websocket import router as websocket_router, start_background_tasks

# Start the WebSocket background tasks
start_background_tasks()

__all__ = ['router', 'websocket_router']
