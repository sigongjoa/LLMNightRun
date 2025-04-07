"""
MCP 함수 등록 모듈

브라우저 개발자 콘솔, 윈도우 터미널, 로컬 LLM 함수를 MCP 핸들러에 등록합니다.
"""

import logging
from typing import Dict, Any

from .handler import MCPHandler
from .function_defs import MCP_FUNCTIONS
from .function_implementations import MCP_FUNCTION_IMPLEMENTATIONS
from .llm_functions import MCP_LLM_FUNCTION_IMPLEMENTATIONS

logger = logging.getLogger("mcp.register")

def register_mcp_functions(handler: MCPHandler) -> None:
    """MCP 함수 등록
    
    모든 MCP 함수를 핸들러에 등록합니다.
    
    Args:
        handler: MCP 핸들러 인스턴스
    """
    # 모든 함수 정의 가져오기
    function_defs = MCP_FUNCTIONS
    
    # 모든 함수 구현 가져오기
    function_impls = {}
    function_impls.update(MCP_FUNCTION_IMPLEMENTATIONS)
    function_impls.update(MCP_LLM_FUNCTION_IMPLEMENTATIONS)
    
    # 모든 MCP 함수 등록
    for func_name, func_impl in function_impls.items():
        if func_name in function_defs:
            # 로깅
            logger.info(f"Registering MCP function: {func_name}")
            
            # 함수 등록
            handler.register_function(func_name, func_impl)
        else:
            # 함수 정의가 없는 경우에도 등록 (LLM 함수는 직접 추가했으므로)
            logger.info(f"Registering MCP function without definition: {func_name}")
            handler.register_function(func_name, func_impl)
    
    # 함수 그룹 저장
    browser_console_functions = {
        name: func for name, func in function_defs.items() 
        if name.startswith("console_")
    }
    
    terminal_functions = {
        name: func for name, func in function_defs.items() 
        if name.startswith("terminal_")
    }
    
    # LLM 함수들 - 정의가 없을 수 있으므로 별도로 처리
    llm_functions = {
        name: {
            "name": name, 
            "description": MCP_LLM_FUNCTION_IMPLEMENTATIONS[name].__doc__
        }
        for name in MCP_LLM_FUNCTION_IMPLEMENTATIONS
    }
    
    # 함수 그룹 저장
    handler.save_function_group("browser_console", browser_console_functions)
    handler.save_function_group("terminal", terminal_functions)
    handler.save_function_group("llm", llm_functions)
    
    logger.info(f"Registered {len(function_impls)} MCP functions")


def create_function_context(handler: MCPHandler) -> None:
    """함수 컨텍스트 생성
    
    MCP 함수를 위한 기본 컨텍스트를 생성합니다.
    
    Args:
        handler: MCP 핸들러 인스턴스
    """
    # 기존 컨텍스트 확인
    if "functions" in handler.list_contexts():
        logger.info("Functions context already exists")
        return
    
    # 함수 컨텍스트 생성
    functions_data = {
        "browser_console": {
            "description": "브라우저 개발자 콘솔 함수 그룹",
            "functions": [name for name in MCP_FUNCTIONS if name.startswith("console_")]
        },
        "terminal": {
            "description": "윈도우 터미널 함수 그룹",
            "functions": [name for name in MCP_FUNCTIONS if name.startswith("terminal_")]
        },
        "llm": {
            "description": "로컬 LLM 함수 그룹",
            "functions": list(MCP_LLM_FUNCTION_IMPLEMENTATIONS.keys())
        }
    }
    
    # 컨텍스트 저장
    handler.create_context(functions_data, "functions")
    logger.info("Created functions context")
