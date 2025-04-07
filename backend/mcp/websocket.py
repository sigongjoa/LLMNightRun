"""
MCP WebSocket 모듈

브라우저 콘솔과 터미널 도구를 위한 WebSocket 연결을 관리합니다.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse

from .tools.browser_console import BrowserConsoleTool
from .tools.terminal import TerminalTool
from .function_implementations import browser_console_tool

logger = logging.getLogger("mcp.websocket")

router = APIRouter(prefix="/mcp/ws", tags=["MCP WebSocket"])

# 활성 WebSocket 연결 관리
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/console/{session_id}")
async def websocket_browser_console(websocket: WebSocket, session_id: str):
    """브라우저 개발자 콘솔 WebSocket 엔드포인트
    
    Args:
        websocket: WebSocket 연결
        session_id: 세션 ID
    """
    await websocket.accept()
    
    try:
        # 콘솔 도구에 WebSocket 연결 등록
        await browser_console_tool.register_connection(session_id, websocket)
    except Exception as e:
        logger.error(f"Error in browser console websocket: {e}")
        await websocket.close(code=1011)


@router.websocket("/terminal/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    """터미널 WebSocket 엔드포인트
    
    Args:
        websocket: WebSocket 연결
        session_id: 세션 ID
    """
    await websocket.accept()
    
    try:
        active_connections[session_id] = websocket
        
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "Terminal WebSocket connection established"
        })
        
        # 연결이 활성화되어 있는 동안 메시지 처리
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 메시지 유형에 따른 처리
            message_type = message.get("type")
            
            if message_type == "ping":
                # 핑-퐁 메시지 처리
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
            elif message_type == "output":
                # 터미널 출력 메시지 처리 (향후 구현)
                pass
            elif message_type == "disconnect":
                # 연결 해제 요청
                break
            else:
                # 알 수 없는 메시지 유형
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Terminal WebSocket client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Error in terminal websocket: {e}")
    finally:
        # 연결 해제 처리
        if session_id in active_connections:
            del active_connections[session_id]


@router.post("/notify/{session_id}")
async def notify_terminal(session_id: str, data: Dict[str, Any]):
    """터미널 세션에 알림 전송
    
    Args:
        session_id: 세션 ID
        data: 알림 데이터
        
    Returns:
        JSONResponse: 응답
    """
    if session_id not in active_connections:
        raise HTTPException(status_code=404, detail=f"Terminal session not found: {session_id}")
    
    try:
        websocket = active_connections[session_id]
        await websocket.send_json({
            "type": "notification",
            **data
        })
        
        return JSONResponse(
            status_code=200,
            content={"message": "Notification sent successfully"}
        )
    except Exception as e:
        logger.error(f"Error sending notification to terminal session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending notification: {str(e)}"
        )
