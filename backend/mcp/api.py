"""
Model Context Protocol (MCP) API 라우터
"""

from fastapi import APIRouter, Request, HTTPException, File, UploadFile, Form, Body, Query, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import json
import logging
import os
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Union

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
        
        response = await mcp_handler.handle_message(message_data)
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
    
    response = await mcp_handler.handle_message(message)
    return response

# LLM 관련 엔드포인트
@router.post("/v1/llm/sessions")
async def create_llm_session(
    base_url: str = Body("http://localhost:1234/v1", description="LLM API 기본 URL"),
    api_key: str = Body("", description="API 키"),
    model: str = Body("local-model", description="모델 이름"),
    context_length: int = Body(4096, description="컨텍스트 길이"),
    additional_config: Dict[str, Any] = Body(None, description="추가 구성 정보")
):
    """LLM 세션 생성 API 엔드포인트"""
    try:
        from .llm_functions import llm_create_session
        result = await llm_create_session(
            base_url=base_url,
            api_key=api_key,
            model=model,
            context_length=context_length,
            additional_config=additional_config
        )
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create LLM session"))
            
        return result
    except Exception as e:
        logger.error(f"Error creating LLM session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating LLM session: {str(e)}")

@router.get("/v1/llm/sessions")
async def list_llm_sessions():
    """LLM 세션 목록 조회 API 엔드포인트"""
    try:
        from .llm_functions import llm_list_sessions
        result = llm_list_sessions()
        return result
    except Exception as e:
        logger.error(f"Error listing LLM sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing LLM sessions: {str(e)}")

@router.get("/v1/llm/sessions/{session_id}")
async def get_llm_session(session_id: str):
    """LLM 세션 정보 조회 API 엔드포인트"""
    try:
        from .llm_functions import llm_get_session
        result = llm_get_session(session_id)
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", f"Session {session_id} not found"))
            
        return result
    except Exception as e:
        logger.error(f"Error getting LLM session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting LLM session: {str(e)}")

@router.delete("/v1/llm/sessions/{session_id}")
async def delete_llm_session(session_id: str):
    """LLM 세션 삭제 API 엔드포인트"""
    try:
        from .llm_functions import llm_delete_session
        result = llm_delete_session(session_id)
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", f"Session {session_id} not found"))
            
        return result
    except Exception as e:
        logger.error(f"Error deleting LLM session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting LLM session: {str(e)}")

@router.get("/v1/llm/sessions/{session_id}/history")
async def get_llm_session_history(session_id: str, count: int = Query(None, description="조회할 기록 수")):
    """LLM 세션 히스토리 조회 API 엔드포인트"""
    try:
        from .llm_functions import llm_get_history
        result = llm_get_history(session_id, count)
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", f"Session {session_id} not found"))
            
        return result
    except Exception as e:
        logger.error(f"Error getting LLM session history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting LLM session history: {str(e)}")

@router.post("/v1/llm/sessions/{session_id}/test")
async def test_llm_connection(session_id: str):
    """LLM 연결 테스트 API 엔드포인트"""
    try:
        from .llm_functions import llm_test_connection
        result = await llm_test_connection(session_id)
        return result
    except Exception as e:
        logger.error(f"Error testing LLM connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing LLM connection: {str(e)}")

@router.post("/v1/llm/sessions/{session_id}/generate")
async def generate_llm_text(
    session_id: str,
    prompt: Union[str, List[Dict[str, Any]]] = Body(..., description="프롬프트 텍스트 또는 메시지 목록"),
    max_tokens: int = Body(1024, description="최대 생성 토큰 수"),
    temperature: float = Body(0.7, description="온도 (0.0 ~ 2.0)"),
    top_p: float = Body(1.0, description="상위 확률 샘플링 (0.0 ~ 1.0)"),
    frequency_penalty: float = Body(0.0, description="빈도 페널티 (0.0 ~ 2.0)"),
    presence_penalty: float = Body(0.0, description="존재 페널티 (0.0 ~ 2.0)"),
    stop_sequences: List[str] = Body(None, description="정지 시퀀스 목록"),
    stream: bool = Body(False, description="스트리밍 여부")
):
    """LLM 텍스트 생성 API 엔드포인트"""
    try:
        from .llm_functions import llm_generate
        result = await llm_generate(
            session_id=session_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop_sequences=stop_sequences,
            stream=stream
        )
        return result
    except Exception as e:
        logger.error(f"Error generating LLM text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating LLM text: {str(e)}")

@router.post("/v1/llm/sessions/{session_id}/chat")
async def generate_llm_chat(
    session_id: str,
    messages: List[Dict[str, Any]] = Body(..., description="채팅 메시지 목록"),
    max_tokens: int = Body(1024, description="최대 생성 토큰 수"),
    temperature: float = Body(0.7, description="온도 (0.0 ~ 2.0)"),
    top_p: float = Body(1.0, description="상위 확률 샘플링 (0.0 ~ 1.0)"),
    frequency_penalty: float = Body(0.0, description="빈도 페널티 (0.0 ~ 2.0)"),
    presence_penalty: float = Body(0.0, description="존재 페널티 (0.0 ~ 2.0)"),
    stop_sequences: List[str] = Body(None, description="정지 시퀀스 목록"),
    stream: bool = Body(False, description="스트리밍 여부")
):
    """LLM 채팅 완성 API 엔드포인트"""
    try:
        from .llm_functions import llm_chat
        result = await llm_chat(
            session_id=session_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop_sequences=stop_sequences,
            stream=stream
        )
        return result
    except Exception as e:
        logger.error(f"Error generating LLM chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating LLM chat completion: {str(e)}")


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
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
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

# 터미널 관련 API (비활성화됨)
@router.post("/v1/terminal/create")
async def create_terminal_session(
    working_dir: Optional[str] = Body(None, description="초기 작업 디렉토리")
):
    """터미널 세션 생성 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_create
        result = terminal_create(working_dir)
        return result
    except Exception as e:
        logger.error(f"Error creating terminal session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating terminal session: {str(e)}")

@router.delete("/v1/terminal/{session_id}")
async def delete_terminal_session(session_id: str):
    """터미널 세션 삭제 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_delete
        result = terminal_delete(session_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting terminal session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting terminal session: {str(e)}")

@router.post("/v1/terminal/{session_id}/execute")
async def execute_terminal_command(
    session_id: str,
    command: str = Body(..., description="실행할 명령어"),
    timeout: Optional[int] = Body(None, description="실행 제한 시간(초)"),
    working_dir: Optional[str] = Body(None, description="작업 디렉토리")
):
    """터미널 명령어 실행 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_execute
        result = await terminal_execute(session_id, command, timeout, working_dir)
        return result
    except Exception as e:
        logger.error(f"Error executing terminal command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing terminal command: {str(e)}")

@router.get("/v1/terminal/{session_id}/history")
async def get_terminal_history(
    session_id: str,
    count: int = Query(10, description="조회할 기록 수")
):
    """터미널 명령어 실행 기록 조회 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_history
        result = terminal_history(session_id, count)
        return result
    except Exception as e:
        logger.error(f"Error retrieving terminal history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving terminal history: {str(e)}")

@router.get("/v1/terminal/sessions")
async def list_terminal_sessions():
    """터미널 세션 목록 조회 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_sessions
        result = terminal_sessions()
        return result
    except Exception as e:
        logger.error(f"Error listing terminal sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing terminal sessions: {str(e)}")

@router.get("/v1/terminal/{session_id}/workdir")
async def get_terminal_workdir(session_id: str):
    """터미널 작업 디렉토리 조회 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_workdir
        result = terminal_workdir(session_id)
        return result
    except Exception as e:
        logger.error(f"Error retrieving terminal working directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving terminal working directory: {str(e)}")

@router.post("/v1/terminal/{session_id}/workdir")
async def set_terminal_workdir(
    session_id: str,
    working_dir: str = Body(..., description="설정할 작업 디렉토리")
):
    """터미널 작업 디렉토리 설정 API (비활성화됨)"""
    try:
        from .function_implementations import terminal_workdir
        result = terminal_workdir(session_id, working_dir)
        return result
    except Exception as e:
        logger.error(f"Error setting terminal working directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting terminal working directory: {str(e)}")
