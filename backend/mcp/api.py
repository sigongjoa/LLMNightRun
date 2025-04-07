"""
Model Context Protocol (MCP) API 라우터
"""

from fastapi import APIRouter, Request, HTTPException, File, UploadFile, Form, Body, Query
from fastapi.responses import JSONResponse, FileResponse
import json
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional

from .handler import MCPHandler

router = APIRouter(prefix="/mcp", tags=["MCP"])
mcp_handler = MCPHandler()
logger = logging.getLogger("mcp.api")

@router.post("/v1/process")
async def process_mcp_message(request: Request):
    """MCP 메시지 처리 API 엔드포인트"""
    try:
        message_data = await request.json()
        logger.info(f"Received MCP message: {json.dumps(message_data)[:200]}...")
        
        response = mcp_handler.handle_message(message_data)
        return response
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing MCP message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# 함수 관련 엔드포인트
@router.get("/v1/functions")
async def list_functions():
    """등록된 MCP 함수 목록 조회"""
    return {
        "functions": list(mcp_handler.registered_functions.keys())
    }

# 컨텍스트 관련 엔드포인트
@router.get("/v1/contexts")
async def list_contexts():
    """사용 가능한 컨텍스트 목록 조회"""
    contexts = mcp_handler.list_contexts()
    return {
        "contexts": contexts
    }

@router.get("/v1/contexts/{context_id}")
async def get_context(context_id: str):
    """컨텍스트 조회"""
    context = mcp_handler.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context ID {context_id} not found")
    return context

@router.post("/v1/contexts")
async def create_context(data: Dict[str, Any] = Body({}, description="초기 컨텍스트 데이터")):
    """새 컨텍스트 생성"""
    context_id = mcp_handler.create_context(data)
    return {
        "context_id": context_id,
        "message": "Context created successfully"
    }

@router.delete("/v1/contexts/{context_id}")
async def delete_context(context_id: str):
    """컨텍스트 삭제"""
    success = mcp_handler.delete_context(context_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Context ID {context_id} not found or could not be deleted")
    return {
        "message": f"Context {context_id} deleted successfully"
    }

@router.post("/v1/contexts/{context_id}")
async def update_context(
    context_id: str, 
    data: Dict[str, Any] = Body(..., description="업데이트할 컨텍스트 데이터"),
    merge: bool = Query(True, description="기존 데이터와 병합 여부")
):
    """컨텍스트 업데이트"""
    # 컨텍스트 업데이트 메시지 생성
    message = {
        "type": "context_update",
        "content": {
            "context_id": context_id,
            "data": data
        },
        "request_id": context_id
    }
    
    response = mcp_handler.handle_message(message)
    return response

# 함수 그룹 관련 엔드포인트
@router.get("/v1/function-groups")
async def list_function_groups():
    """함수 그룹 목록 조회"""
    groups = mcp_handler.list_function_groups()
    return {
        "function_groups": groups
    }

@router.get("/v1/function-groups/{group_name}")
async def get_function_group(group_name: str):
    """함수 그룹 조회"""
    group = mcp_handler.get_function_group(group_name)
    if not group:
        raise HTTPException(status_code=404, detail=f"Function group {group_name} not found")
    return group

@router.post("/v1/function-groups/{group_name}")
async def save_function_group(
    group_name: str,
    functions: Dict[str, Any] = Body(..., description="함수 그룹 데이터")
):
    """함수 그룹 저장"""
    success = mcp_handler.save_function_group(group_name, functions)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to save function group {group_name}")
    return {
        "message": f"Function group {group_name} saved successfully"
    }

# 구성 내보내기/가져오기
@router.get("/v1/export")
async def export_config():
    """모든 MCP 구성 내보내기"""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name
        
        # 구성 내보내기
        success = mcp_handler.export_config(tmp_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to export configuration")
        
        # 파일 응답
        return FileResponse(
            path=tmp_path,
            filename="mcp_config_export.json",
            media_type="application/json",
            background=lambda: os.unlink(tmp_path)  # 파일 다운로드 후 삭제
        )
    except Exception as e:
        logger.error(f"Error exporting configuration: {str(e)}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error exporting configuration: {str(e)}")

@router.post("/v1/import")
async def import_config(
    file: UploadFile = File(...),
    overwrite: bool = Form(False, description="기존 항목 덮어쓰기 여부")
):
    """MCP 구성 가져오기"""
    try:
        # 임시 파일로 업로드 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # 구성 가져오기
        success = mcp_handler.import_config(tmp_path, overwrite)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import configuration")
        
        # 임시 파일 삭제
        os.unlink(tmp_path)
        
        return {
            "message": "Configuration imported successfully"
        }
    except Exception as e:
        logger.error(f"Error importing configuration: {str(e)}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error importing configuration: {str(e)}")
