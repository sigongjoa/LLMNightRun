"""
MCP 서버 상태 API 모듈

MCP 서버 상태를 제공하는 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from backend.mcp.server_manager import get_mcp_manager

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(
    prefix="/mcp-status",
    tags=["mcp-status"],
    responses={404: {"description": "해당 정보를 찾을 수 없음"}},
)

@router.get("/servers")
async def get_mcp_servers():
    """
    등록된 MCP 서버 목록과 현재 상태를 반환합니다.
    
    Returns:
        등록된 MCP 서버 정보
    """
    try:
        mcp_manager = get_mcp_manager()
        servers = mcp_manager.list_servers()
        
        return {
            "success": True,
            "servers": servers
        }
    except Exception as e:
        logger.error(f"MCP 서버 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"MCP 서버 정보 조회 실패: {str(e)}")


@router.get("/servers/{server_id}")
async def get_mcp_server_status(server_id: str):
    """
    특정 MCP 서버의 상세 상태를 반환합니다.
    
    Args:
        server_id: 서버 ID
        
    Returns:
        MCP 서버 상세 정보
    """
    try:
        mcp_manager = get_mcp_manager()
        status = mcp_manager.get_server_status(server_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"서버 '{server_id}'를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "server": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP 서버 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"MCP 서버 상태 조회 실패: {str(e)}")


@router.get("/config")
async def get_mcp_config():
    """
    현재 MCP 설정을 반환합니다.
    
    Returns:
        MCP 설정 정보
    """
    try:
        mcp_manager = get_mcp_manager()
        config = mcp_manager.load_config()
        
        # 민감한 정보(예: API 키)를 제외한 설정 반환
        safe_config = {
            "mcpServers": {}
        }
        
        # 서버마다 안전한 정보 복사
        for server_id, server_config in config.get("mcpServers", {}).items():
            safe_server_config = server_config.copy()
            
            # 환경변수에서 민감한 정보 제거
            if "env" in safe_server_config:
                safe_env = {}
                for key, value in safe_server_config["env"].items():
                    if any(secret_key in key.lower() for secret_key in ["key", "token", "secret", "password", "auth"]):
                        safe_env[key] = "********"  # 민감한 정보 마스킹
                    else:
                        safe_env[key] = value
                
                safe_server_config["env"] = safe_env
            
            safe_config["mcpServers"][server_id] = safe_server_config
        
        return {
            "success": True,
            "config": safe_config
        }
    except Exception as e:
        logger.error(f"MCP 설정 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"MCP 설정 조회 실패: {str(e)}")


@router.get("/tools")
async def get_mcp_tools():
    """
    사용 가능한 MCP 도구 목록을 반환합니다.
    
    Returns:
        사용 가능한 MCP 도구 목록
    """
    # 이 부분은 실제 MCP 서버에 연결하여 도구 목록을 가져와야 합니다.
    # 지금은 더미 데이터로 구현합니다.
    try:
        tools = [
            {
                "name": "read_file",
                "description": "파일 내용 읽기",
                "server": "filesystem"
            },
            {
                "name": "write_file",
                "description": "파일에 내용 쓰기",
                "server": "filesystem"
            },
            {
                "name": "list_directory",
                "description": "디렉토리 내용 나열",
                "server": "filesystem"
            },
            {
                "name": "memory_store",
                "description": "메모리에 정보 저장",
                "server": "memory"
            },
            {
                "name": "memory_retrieve",
                "description": "메모리에서 정보 검색",
                "server": "memory"
            }
        ]
        
        return {
            "success": True,
            "tools": tools
        }
    except Exception as e:
        logger.error(f"MCP 도구 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"MCP 도구 목록 조회 실패: {str(e)}")
