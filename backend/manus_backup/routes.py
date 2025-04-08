from fastapi import APIRouter, Body, Depends, BackgroundTasks
from typing import Dict, Any, Optional
import asyncio

from .mcp_server import ManusMCPServer
from .models import MCPInitializeRequest
from .mcp_agent_integration import ManusAgentMCPIntegration
from backend.models.enums import LLMType

router = APIRouter(prefix="/manus/mcp", tags=["Manus MCP"])

# 싱글톤 인스턴스 제공 함수
_manus_mcp_server = None
_manus_agent_integration = None

def get_manus_mcp_server():
    global _manus_mcp_server
    if _manus_mcp_server is None:
        _manus_mcp_server = ManusMCPServer()
    return _manus_mcp_server

def get_manus_agent_integration():
    global _manus_agent_integration
    if _manus_agent_integration is None:
        _manus_agent_integration = ManusAgentMCPIntegration(
            llm_type=LLMType.LOCAL_LLM,
            # 기본 설정은 config에서 가져옴
            llm_base_url=None,
            model_id=None
        )
    return _manus_agent_integration

@router.post("/initialize")
async def initialize(request: MCPInitializeRequest, server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.initialize(request)

@router.post("/resources/list")
async def list_resources(server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.list_resources()

@router.post("/resources/read")
async def read_resource(data: Dict[str, Any] = Body(...), server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.read_resource(data.get("uri"))

@router.post("/tools/list")
async def list_tools(server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.list_tools()

@router.post("/tools/call")
async def call_tool(data: Dict[str, Any] = Body(...), server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.call_tool(data.get("name"), data.get("arguments", {}))

@router.post("/prompts/list")
async def list_prompts(server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.list_prompts()

@router.post("/prompts/get")
async def get_prompt(data: Dict[str, Any] = Body(...), server: ManusMCPServer = Depends(get_manus_mcp_server)):
    return server.get_prompt(data.get("name"), data.get("arguments", {}))

# 에이전트 관련 라우트
@router.post("/agent/query")
async def agent_query(data: Dict[str, Any] = Body(...), integration: ManusAgentMCPIntegration = Depends(get_manus_agent_integration)):
    query = data.get("query", "")
    with_tools = data.get("with_tools", True)
    model_id = data.get("model_id", None)
    
    # 모델 ID가 제공된 경우 업데이트
    if model_id:
        integration.set_model_id(model_id)
    
    # 비동기 처리
    result = await integration.process_query(query, with_tools=with_tools)
    return result

@router.post("/agent/file_operation")
async def agent_file_operation(data: Dict[str, Any] = Body(...), integration: ManusAgentMCPIntegration = Depends(get_manus_agent_integration)):
    operation = data.get("operation", "")
    path = data.get("path", "")
    content = data.get("content", None)
    
    result = await integration.process_file_operation(operation, path, content)
    return result

@router.post("/agent/history/clear")
async def agent_clear_history(integration: ManusAgentMCPIntegration = Depends(get_manus_agent_integration)):
    integration.clear_conversation_history()
    return {"success": True, "message": "대화 기록이 초기화되었습니다."}

@router.get("/agent/history")
async def agent_get_history(integration: ManusAgentMCPIntegration = Depends(get_manus_agent_integration)):
    history = integration.get_conversation_history()
    return {"history": history}

@router.post("/agent/set_model")
async def agent_set_model(data: Dict[str, Any] = Body(...), integration: ManusAgentMCPIntegration = Depends(get_manus_agent_integration)):
    model_id = data.get("model_id", "")
    if not model_id:
        return {"success": False, "error": "모델 ID가 제공되지 않았습니다."}
    
    integration.set_model_id(model_id)
    return {"success": True, "message": f"모델 ID가 {model_id}로 설정되었습니다."}