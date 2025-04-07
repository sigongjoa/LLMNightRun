"""
Model Context Protocol (MCP) 함수 레지스트리
"""

import logging
import os
from typing import Dict, Any

from .handler import MCPHandler
from .fs_functions import FSFunctions
from .json_functions import JSONFunctions

logger = logging.getLogger("mcp.registry")

def register_fs_functions(handler: MCPHandler, base_dir: str = None) -> None:
    """
    파일 시스템 MCP 함수 등록
    
    Args:
        handler: MCP 핸들러
        base_dir: 기본 작업 디렉토리 (None인 경우 현재 디렉토리 사용)
    """
    fs = FSFunctions(base_dir)
    
    # 파일 시스템 함수 등록
    handler.register_function("fs.readFile", fs.read_file)
    handler.register_function("fs.writeFile", fs.write_file)
    handler.register_function("fs.listDirectory", fs.list_directory)
    handler.register_function("fs.createDirectory", fs.create_directory)
    handler.register_function("fs.delete", fs.delete)
    handler.register_function("fs.move", fs.move)
    
    logger.info("Registered File System MCP functions")

def register_json_functions(handler: MCPHandler, base_dir: str = None) -> None:
    """
    JSON 처리 MCP 함수 등록
    
    Args:
        handler: MCP 핸들러
        base_dir: 기본 작업 디렉토리 (None인 경우 현재 디렉토리 사용)
    """
    json_funcs = JSONFunctions(base_dir)
    
    # JSON 함수 등록
    handler.register_function("json.readJSON", json_funcs.read_json)
    handler.register_function("json.writeJSON", json_funcs.write_json)
    handler.register_function("json.updateJSON", json_funcs.update_json)
    handler.register_function("json.validateJSON", json_funcs.validate_json)
    
    logger.info("Registered JSON MCP functions")

def register_all_functions(handler: MCPHandler) -> None:
    """
    모든 MCP 함수 등록
    
    Args:
        handler: MCP 핸들러
    """
    # 프로젝트 루트 디렉토리
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # 파일 시스템 함수 등록
    register_fs_functions(handler, project_root)
    
    # JSON 함수 등록
    register_json_functions(handler, project_root)
    
    # 나중에 추가될 다른 함수 등록
    # register_other_functions(handler)
    
    logger.info(f"Registered all MCP functions. Base directory: {project_root}")
