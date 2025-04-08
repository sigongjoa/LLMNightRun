"""
MCP API routes for function definitions and other MCP-related operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from .function_registry import get_function_registry
from .function_defs import MCP_FUNCTIONS

logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/api/mcp/functions",
    tags=["mcp-api"],
    responses={404: {"description": "Not found"}},
)

# Models
class FunctionResponse(BaseModel):
    functions: Dict[str, Any]

@router.get("", response_model=FunctionResponse)
async def get_functions():
    """Get available MCP functions and their definitions."""
    try:
        # 기본적으로 미리 정의된 함수 정의 반환
        functions = MCP_FUNCTIONS.copy()
        
        # 함수 레지스트리에서 추가 함수 가져오기
        registry = get_function_registry()
        registered_functions = registry.list_function_definitions()
        
        # 두 소스 병합
        functions.update(registered_functions)
        
        return {"functions": functions}
    except Exception as e:
        logger.exception(f"Error retrieving MCP functions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{function_name}")
async def get_function(function_name: str):
    """Get a specific MCP function definition."""
    try:
        # 기본 함수 확인
        if function_name in MCP_FUNCTIONS:
            return {"function": MCP_FUNCTIONS[function_name]}
        
        # 레지스트리 확인
        registry = get_function_registry()
        if registry.has_function_definition(function_name):
            return {"function": registry.get_function_definition(function_name)}
        
        # 함수를 찾지 못한 경우
        raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving function '{function_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
