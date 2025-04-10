"""
API routes for MCP server management in LLMNightRun.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

from .server_manager import get_mcp_manager, MCPServerManager

logger = logging.getLogger(__name__)

# Models
class ServerConfig(BaseModel):
    command: str
    args: List[str]
    env: Dict[str, str] = {}

class ServerInfo(BaseModel):
    id: str
    command: str
    args: List[str]
    running: bool

class ServerStatus(BaseModel):
    id: str
    exists: bool
    running: bool
    config: Optional[Dict] = None
    pid: Optional[int] = None
    uptime: Optional[float] = None

class ServerActionResponse(BaseModel):
    success: bool
    message: str

class MCPConfigUpdate(BaseModel):
    mcpServers: Dict[str, Dict[str, Any]]

# Router
router = APIRouter(
    prefix="/api/mcp",
    tags=["mcp"],
    responses={404: {"description": "Not found"}},
)

def get_manager() -> MCPServerManager:
    """Dependency to get MCP manager."""
    return get_mcp_manager()

@router.get("/servers", response_model=List[ServerInfo])
async def list_servers(manager: MCPServerManager = Depends(get_manager)):
    """List all configured MCP servers."""
    return manager.list_servers()

@router.get("/servers/{server_id}", response_model=ServerStatus)
async def get_server_status(server_id: str, manager: MCPServerManager = Depends(get_manager)):
    """Get status of a specific MCP server."""
    return manager.get_server_status(server_id)

@router.post("/servers/{server_id}", response_model=ServerActionResponse)
async def update_server(
    server_id: str, 
    config: ServerConfig, 
    manager: MCPServerManager = Depends(get_manager)
):
    """Create or update an MCP server configuration."""
    success = manager.update_server_config(server_id, config.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update server configuration")
    return {"success": True, "message": f"Server '{server_id}' configuration updated"}

@router.delete("/servers/{server_id}", response_model=ServerActionResponse)
async def delete_server(server_id: str, manager: MCPServerManager = Depends(get_manager)):
    """Delete an MCP server configuration."""
    # Stop the server if it's running
    if server_id in [s["id"] for s in manager.list_servers() if s["running"]]:
        manager.stop_server(server_id)
        
    success = manager.remove_server_config(server_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
    return {"success": True, "message": f"Server '{server_id}' deleted"}

@router.post("/servers/{server_id}/start", response_model=ServerActionResponse)
async def start_server(server_id: str, manager: MCPServerManager = Depends(get_manager)):
    """Start a specific MCP server."""
    try:
        logger.info(f"Received request to start server {server_id}")
        success, message = manager.start_server(server_id)
        if not success:
            logger.error(f"Failed to start server {server_id}: {message}")
            raise HTTPException(status_code=500, detail=message)
        logger.info(f"Successfully started server {server_id}")
        return {"success": True, "message": message}
    except Exception as e:
        logger.exception(f"Unhandled exception when starting server {server_id}")
        raise HTTPException(status_code=500, detail=f"Unhandled error: {str(e)}")

@router.post("/servers/{server_id}/stop", response_model=ServerActionResponse)
async def stop_server(server_id: str, manager: MCPServerManager = Depends(get_manager)):
    """Stop a specific MCP server."""
    success, message = manager.stop_server(server_id)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}

@router.post("/servers/{server_id}/restart", response_model=ServerActionResponse)
async def restart_server(server_id: str, manager: MCPServerManager = Depends(get_manager)):
    """Restart a specific MCP server."""
    success, message = manager.restart_server(server_id)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}

@router.post("/start-all", response_model=Dict[str, ServerActionResponse])
async def start_all_servers(manager: MCPServerManager = Depends(get_manager)):
    """Start all configured MCP servers."""
    results = manager.start_all_servers()
    response = {}
    for server_id, (success, message) in results.items():
        response[server_id] = {"success": success, "message": message}
    return response

@router.post("/stop-all", response_model=Dict[str, ServerActionResponse])
async def stop_all_servers(manager: MCPServerManager = Depends(get_manager)):
    """Stop all running MCP servers."""
    results = manager.stop_all_servers()
    response = {}
    for server_id, (success, message) in results.items():
        response[server_id] = {"success": success, "message": message}
    return response

@router.get("/config", response_model=Dict[str, Any])
async def get_config(manager: MCPServerManager = Depends(get_manager)):
    """Get the full MCP configuration."""
    return manager.config

@router.get("/status", response_model=Dict[str, Any])
async def get_status(manager: MCPServerManager = Depends(get_manager)):
    """Get MCP server status including LM Studio connection status."""
    try:
        # LM Studio 연결 상태 확인
        from .local_llm import LocalLLMTool
        
        llm_tool = LocalLLMTool()
        llm_config = {
            "baseUrl": "http://localhost:1234/v1",  # LM Studio 기본 URL
            "model": "local-model",                 # 실제 모델은 LM Studio에서 선택
            "provider": "local"
        }
        
        try:
            # 세션 생성
            session_id = await llm_tool.initialize_session(llm_config)
            # 연결 테스트
            test_result = await llm_tool.test_connection(session_id)
            # 세션 삭제
            llm_tool.delete_session(session_id)
            
            connected = test_result.get("success", False)
            message = "연결됨" if connected else test_result.get("error", "알 수 없는 오류")
        except Exception as e:
            logger.error(f"LM Studio 연결 테스트 오류: {str(e)}")
            connected = False
            message = f"연결 오류: {str(e)}"
        
        # 서버 목록 가져오기
        servers = manager.list_servers()
        
        return {
            "success": True,
            "llm_studio": {
                "connected": connected,
                "message": message
            },
            "servers_count": len(servers),
            "running_servers": sum(1 for s in servers if s["running"])
        }
    except Exception as e:
        logger.exception(f"Error getting MCP status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/config", response_model=ServerActionResponse)
async def update_config(
    config: MCPConfigUpdate = Body(...), 
    manager: MCPServerManager = Depends(get_manager)
):
    """Update the complete MCP configuration."""
    # Stop all running servers first
    manager.stop_all_servers()
    
    # Update the config
    manager.config = config.dict()
    success = manager.save_config()
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save configuration")
        
    return {"success": True, "message": "MCP configuration updated"}
