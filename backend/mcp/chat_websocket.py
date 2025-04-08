"""
WebSocket routes for Chat with MCP and Local LLM integration.
Enables real-time streaming of responses from local LLMs.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
from datetime import datetime
import uuid

from .local_llm import LocalLLMTool
from .server_manager import get_mcp_manager
from .function_registry import get_function_registry
from .handler import MCPHandler
from .message_formatter import MessageFormatter, process_streaming

logger = logging.getLogger("mcp.chat_websocket")

# Router
router = APIRouter(
    prefix="/ws/chat",
    tags=["chat-websocket"],
)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# LLM Tool 인스턴스
llm_tool = LocalLLMTool()

# 함수 레지스트리 인스턴스 가져오기
function_registry = get_function_registry()

# MCP 핸들러 인스턴스 가져오기
mcp_handler = MCPHandler()

@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """LLM 응답을 스트리밍하는 WebSocket 엔드포인트"""
    await websocket.accept()
    
    # 고유 ID 생성
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    logger.info(f"New WebSocket connection established: {connection_id}")
    
    # LLM 세션 초기화
    llm_config = {
        "baseUrl": "http://localhost:1234/v1",  # LM Studio 기본 URL
        "model": "local-model",                 # 실제 모델은 LM Studio에서 자동 선택됨
        "provider": "local"
    }
    
    llm_session_id = await llm_tool.initialize_session(llm_config)
    
    try:
        # 접속 성공 메시지 전송
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id,
            "llm_session_id": llm_session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "available_tools": list(function_registry.list_functions())
        })
        
        # LLM 연결 테스트
        test_result = await llm_tool.test_connection(llm_session_id)
        await websocket.send_json({
            "type": "llm_connection_status",
            "success": test_result.get("success", False),
            "message": test_result.get("error", "Connected successfully")
        })
        
        # 클라이언트 메시지 수신 및 처리
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # 메시지 타입에 따라 처리
                if message.get("type") == "chat_request":
                    await handle_chat_request(
                        websocket, 
                        connection_id, 
                        llm_session_id, 
                        message
                    )
                    
                elif message.get("type") == "tool_call":
                    await handle_tool_call(
                        websocket,
                        connection_id,
                        message
                    )
                    
                elif message.get("type") == "export_chat":
                    await handle_export_chat(
                        websocket,
                        connection_id,
                        message
                    )
                
                elif message.get("type") == "set_prompt_template":
                    await handle_set_prompt_template(
                        websocket,
                        connection_id,
                        llm_session_id,
                        message
                    )
                
                elif message.get("type") == "ping":
                    # Keep-alive ping
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                    logger.debug("Ping-Pong 응답 전송")
                    
                else:
                    logger.warning(f"Unrecognized message type: {message.get('type')}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unrecognized message type: {message.get('type')}"
                    })
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.exception(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {connection_id}")
        
    except Exception as e:
        logger.exception(f"WebSocket error: {str(e)}")
        
    finally:
        # 연결 정리
        if connection_id in active_connections:
            del active_connections[connection_id]
            
        # LLM 세션 정리
        llm_tool.delete_session(llm_session_id)
        
        logger.info(f"WebSocket connection and resources cleaned up: {connection_id}")

async def handle_chat_request(
    websocket: WebSocket,
    connection_id: str,
    llm_session_id: str,
    message: Dict[str, Any]
):
    """채팅 요청 처리"""
    prompt = message.get("prompt", "")
    history = message.get("history", [])
    options = message.get("options", {})
    
    if not prompt:
        await websocket.send_json({
            "type": "error",
            "message": "Empty prompt"
        })
        return
    
    # 메시지 형식 준비
    messages = []
    
    # 시스템 메시지 추가
    messages.append({
        "role": "system",
        "content": (
            "You are an AI assistant with access to various tools through MCP (Model Control Protocol). "
            "You can help users with their tasks by utilizing file operations, code execution, and other tools. "
            "Be specific and concise in your responses. When you need to use tools, describe your reasoning first."
        )
    })
    
    # 대화 기록 추가
    for msg in history:
        if msg.get("role") in ["user", "assistant", "system", "tool"]:
            messages.append({
                "role": msg.get("role"),
                "content": msg.get("content", "")
            })
    
    # 현재 사용자 메시지 추가
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # 메시지 ID 생성
    message_id = str(uuid.uuid4())
    
    # 사용 가능한 도구 정의
    tools = []
    for func_name, func_def in function_registry.list_function_definitions().items():
        tools.append({
            "type": "function",
            "function": {
                "name": func_name,
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {})
            }
        })
    
    # 클라이언트에 요청 접수 알림
    await websocket.send_json({
        "type": "chat_request_received",
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # 포맷 업데이트 사용 여부 확인
    use_message_format = options.get('use_message_format', False)
    
    # 사용자가 새로운 메시지 형식을 지정한 경우
    if use_message_format:
        # 새로운 메시지 포맷터 사용
        formatter = MessageFormatter(websocket, llm_tool, message_id)
        await formatter.process_message(llm_session_id, messages, options, tools)
    else:
        # 기존 단계별 스트리밍 방식
        await process_streaming(websocket, llm_tool, llm_session_id, messages, options, message_id, tools)

async def handle_export_chat(
    websocket: WebSocket,
    connection_id: str,
    message: Dict[str, Any]
):
    """채팅 내역 내보내기 처리"""
    history = message.get("history", [])
    format = message.get("format", "json")
    title = message.get("title")
    
    if not history:
        await websocket.send_json({
            "type": "error",
            "message": "Empty chat history"
        })
        return
    
    try:
        # 내보내기 함수 객체 생성
        from .export_functions import ExportFunctions
        export_functions = ExportFunctions()
        
        # 내보내기 실행
        result = export_functions.export_chat_history(history, format, title)
        
        # 결과 전송
        await websocket.send_json({
            "type": "export_chat_result",
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "error": result.get("error", ""),
            "filename": result.get("filename", ""),
            "format": result.get("format", format),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.exception(f"Error exporting chat: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error exporting chat: {str(e)}"
        })

async def handle_set_prompt_template(
    websocket: WebSocket,
    connection_id: str,
    llm_session_id: str,
    message: Dict[str, Any]
):
    """프롬프트 템플릿 설정 처리"""
    template_id = message.get("template_id")
    
    if not template_id:
        await websocket.send_json({
            "type": "error",
            "message": "Missing template ID"
        })
        return
    
    try:
        # 프롬프트 엔지니어링 객체 생성
        from .prompt_engineering import PromptEngineering
        prompt_engineering = PromptEngineering()
        
        # 템플릿 활성화
        result = prompt_engineering.set_active_template(template_id)
        
        if not result.get("success", False):
            await websocket.send_json({
                "type": "error",
                "message": result.get("error", f"Failed to set template: {template_id}")
            })
            return
        
        # 템플릿 설정 조회
        template_settings = prompt_engineering.get_active_template_settings()
        
        # LLM 세션 업데이트
        if llm_session_id and template_settings.get("success", False):
            llm_options = template_settings.get("llmOptions", {})
            
            # LLM 설정 업데이트 (LLMTool에서 해당 기능 구현 필요)
            try:
                await llm_tool.update_session_settings(llm_session_id, llm_options)
                await websocket.send_json({
                    "type": "prompt_template_applied",
                    "template_id": template_id,
                    "template_name": template_settings.get("template", {}).get("name", ""),
                    "message": f"Prompt template '{template_id}' applied successfully",
                    "settings": llm_options,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error updating LLM session settings: {str(e)}")
                # 오류가 있어도 클라이언트에 템플릿 설정은 알림
                await websocket.send_json({
                    "type": "prompt_template_applied",
                    "template_id": template_id,
                    "template_name": template_settings.get("template", {}).get("name", ""),
                    "message": f"Prompt template '{template_id}' set, but failed to update LLM session: {str(e)}",
                    "settings": llm_options,
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            await websocket.send_json({
                "type": "prompt_template_applied",
                "template_id": template_id,
                "message": f"Prompt template '{template_id}' set successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    except Exception as e:
        logger.exception(f"Error setting prompt template: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error setting prompt template: {str(e)}"
        })

async def handle_tool_call(
    websocket: WebSocket,
    connection_id: str,
    message: Dict[str, Any]
):
    """도구 호출 처리"""
    tool_name = message.get("tool_name")
    tool_args = message.get("arguments", {})
    
    if not tool_name:
        await websocket.send_json({
            "type": "error",
            "message": "Missing tool name"
        })
        return
    
    # 도구 호출 ID 생성
    tool_call_id = str(uuid.uuid4())
    
    # 클라이언트에 도구 호출 시작 알림
    await websocket.send_json({
        "type": "tool_call_started",
        "tool_call_id": tool_call_id,
        "tool_name": tool_name,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        # 함수 실행
        if function_registry.has_function(tool_name):
            func = function_registry.get_function(tool_name)
            
            # 함수가 비동기인지 확인
            import inspect
            if inspect.iscoroutinefunction(func):
                result = await func(**tool_args)
            else:
                # 동기 함수를 별도 스레드에서 실행
                import functools
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor() as pool:
                    result = await asyncio.get_event_loop().run_in_executor(
                        pool, functools.partial(func, **tool_args)
                    )
                
            # 결과 전송
            await websocket.send_json({
                "type": "tool_call_result",
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Tool not found: {tool_name}",
                "tool_call_id": tool_call_id
            })
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error executing tool {tool_name}: {str(e)}",
            "tool_call_id": tool_call_id
        })
