"""
WebSocket routes for MCP server integration.
Enables real-time communication between LLMNightRun and MCP servers.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
from datetime import datetime

from .server_manager import get_mcp_manager, MCPServerManager

logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/ws/mcp",
    tags=["mcp-websocket"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Dependency to get MCP manager
def get_manager() -> MCPServerManager:
    """Dependency to get MCP manager."""
    return get_mcp_manager()

async def broadcast_server_status():
    """Broadcast server status to all connected clients."""
    if not active_connections:
        return
        
    manager = get_mcp_manager()
    servers = manager.list_servers()
    
    message = {
        "type": "server_status",
        "timestamp": datetime.utcnow().isoformat(),
        "servers": servers
    }
    
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to connection: {e}")

@router.websocket("/status")
async def websocket_status(websocket: WebSocket, manager: MCPServerManager = Depends(get_manager)):
    """WebSocket endpoint for real-time MCP server status updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial server status
        servers = manager.list_servers()
        await websocket.send_json({
            "type": "server_status",
            "timestamp": datetime.utcnow().isoformat(),
            "servers": servers
        })
        
        # Listen for messages (could be used for commands)
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                command = message.get("command")
                
                if command == "refresh":
                    # Manual refresh request
                    servers = manager.list_servers()
                    await websocket.send_json({
                        "type": "server_status",
                        "timestamp": datetime.utcnow().isoformat(),
                        "servers": servers
                    })
                    
                elif command == "start" and "server_id" in message:
                    # Start a specific server
                    server_id = message["server_id"]
                    success, msg = manager.start_server(server_id)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": command,
                        "server_id": server_id,
                        "success": success,
                        "message": msg
                    })
                    # Broadcast updated status
                    await broadcast_server_status()
                    
                elif command == "stop" and "server_id" in message:
                    # Stop a specific server
                    server_id = message["server_id"]
                    success, msg = manager.stop_server(server_id)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": command,
                        "server_id": server_id,
                        "success": success,
                        "message": msg
                    })
                    # Broadcast updated status
                    await broadcast_server_status()
                    
                elif command == "restart" and "server_id" in message:
                    # Restart a specific server
                    server_id = message["server_id"]
                    success, msg = manager.restart_server(server_id)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": command,
                        "server_id": server_id,
                        "success": success,
                        "message": msg
                    })
                    # Broadcast updated status
                    await broadcast_server_status()
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# Status polling background task
async def status_polling_task():
    """Background task to periodically poll and broadcast server status."""
    while True:
        await broadcast_server_status()
        await asyncio.sleep(5)  # Poll every 5 seconds

# Start the background task when the module is imported
background_task = None

def start_background_tasks():
    """Start background tasks for status polling."""
    global background_task
    if background_task is None or background_task.done():
        try:
            loop = asyncio.get_event_loop()
            background_task = loop.create_task(status_polling_task())
            logger.info("Started MCP status polling background task")
        except Exception as e:
            logger.error(f"Error starting background task: {e}")

def stop_background_tasks():
    """Stop background tasks."""
    global background_task
    if background_task:
        background_task.cancel()
        background_task = None
