"""
MCP 함수 구현 모듈

브라우저 개발자 콘솔과 윈도우 터미널을 위한 MCP 함수 구현을 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional

from .tools.browser_console import BrowserConsoleTool
from .tools.terminal import TerminalTool

logger = logging.getLogger("mcp.functions")

# 도구 인스턴스 생성
browser_console_tool = BrowserConsoleTool()
terminal_tool = TerminalTool()


# 브라우저 콘솔 함수 구현
async def console_execute(session_id: str, code: str, timeout: int = 30) -> Dict[str, Any]:
    """브라우저 개발자 콘솔에서 JavaScript 코드 실행
    
    Args:
        session_id: 콘솔 세션 ID
        code: 실행할 JavaScript 코드
        timeout: 실행 제한 시간 (초)
        
    Returns:
        Dict[str, Any]: 실행 결과
    """
    try:
        result = await browser_console_tool.execute_javascript(session_id, code, timeout)
        return result
    except Exception as e:
        logger.error(f"Error executing JavaScript: {e}")
        return {
            "error": str(e),
            "status": "error",
            "result": None
        }

def console_logs(session_id: str, count: int = 100, level: str = None, source: str = None) -> Dict[str, Any]:
    """브라우저 개발자 콘솔 로그 조회
    
    Args:
        session_id: 콘솔 세션 ID
        count: 조회할 로그 수
        level: 로그 레벨 필터
        source: 로그 소스 필터
        
    Returns:
        Dict[str, Any]: 로그 목록
    """
    try:
        logs = browser_console_tool.get_logs(session_id, count, level, source)
        return {
            "logs": logs,
            "count": len(logs),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error retrieving console logs: {e}")
        return {
            "logs": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }

def console_clear(session_id: str) -> Dict[str, Any]:
    """브라우저 개발자 콘솔 로그 초기화
    
    Args:
        session_id: 콘솔 세션 ID
        
    Returns:
        Dict[str, Any]: 초기화 결과
    """
    try:
        success = browser_console_tool.clear_logs(session_id)
        return {
            "success": success,
            "status": "success" if success else "error",
            "error": None if success else "Session not found"
        }
    except Exception as e:
        logger.error(f"Error clearing console logs: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

def console_sessions() -> Dict[str, Any]:
    """브라우저 개발자 콘솔 활성 세션 목록 조회
    
    Returns:
        Dict[str, Any]: 세션 목록
    """
    try:
        sessions = browser_console_tool.get_active_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error retrieving console sessions: {e}")
        return {
            "sessions": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


# 터미널 함수 구현
def terminal_create(working_dir: str = None) -> Dict[str, Any]:
    """새 터미널 세션 생성
    
    Args:
        working_dir: 초기 작업 디렉터리
        
    Returns:
        Dict[str, Any]: 세션 정보
    """
    try:
        session_id = terminal_tool.create_session(working_dir)
        return {
            "session_id": session_id,
            "working_dir": terminal_tool.get_working_directory(session_id),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error creating terminal session: {e}")
        return {
            "session_id": None,
            "status": "error",
            "error": str(e)
        }

def terminal_delete(session_id: str) -> Dict[str, Any]:
    """터미널 세션 삭제
    
    Args:
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    try:
        success = terminal_tool.delete_session(session_id)
        return {
            "success": success,
            "status": "success" if success else "error",
            "error": None if success else "Session not found"
        }
    except Exception as e:
        logger.error(f"Error deleting terminal session: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

async def terminal_execute(session_id: str, command: str, timeout: int = None, working_dir: str = None) -> Dict[str, Any]:
    """터미널 명령어 실행
    
    Args:
        session_id: 세션 ID
        command: 실행할 명령어
        timeout: 실행 제한 시간 (초)
        working_dir: 작업 디렉터리
        
    Returns:
        Dict[str, Any]: 실행 결과
    """
    try:
        result = await terminal_tool.execute_command(session_id, command, timeout, working_dir)
        return {
            **result,
            "status": "success" if result.get("error") is None else "error"
        }
    except Exception as e:
        logger.error(f"Error executing terminal command: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": "EXECUTION_ERROR",
            "status": "error"
        }

def terminal_history(session_id: str, count: int = 10) -> Dict[str, Any]:
    """터미널 명령어 실행 기록 조회
    
    Args:
        session_id: 세션 ID
        count: 조회할 기록 수
        
    Returns:
        Dict[str, Any]: 명령어 실행 기록
    """
    try:
        history = terminal_tool.get_history(session_id, count)
        return {
            "history": history,
            "count": len(history),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error retrieving terminal history: {e}")
        return {
            "history": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }

def terminal_sessions() -> Dict[str, Any]:
    """터미널 활성 세션 목록 조회
    
    Returns:
        Dict[str, Any]: 세션 목록
    """
    try:
        sessions = terminal_tool.list_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error retrieving terminal sessions: {e}")
        return {
            "sessions": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }

def terminal_workdir(session_id: str, working_dir: str = None) -> Dict[str, Any]:
    """터미널 세션 작업 디렉터리 조회 또는 설정
    
    Args:
        session_id: 세션 ID
        working_dir: 설정할 작업 디렉터리 (None인 경우 조회만 수행)
        
    Returns:
        Dict[str, Any]: 작업 디렉터리 정보
    """
    try:
        if working_dir:
            # 작업 디렉터리 설정
            success = terminal_tool.set_working_directory(session_id, working_dir)
            if not success:
                return {
                    "working_dir": terminal_tool.get_working_directory(session_id),
                    "updated": False,
                    "status": "error",
                    "error": "Invalid directory or session not found"
                }
        
        # 작업 디렉터리 조회
        work_dir = terminal_tool.get_working_directory(session_id)
        if work_dir is None:
            return {
                "working_dir": None,
                "updated": False,
                "status": "error",
                "error": "Session not found"
            }
        
        return {
            "working_dir": work_dir,
            "updated": working_dir is not None,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error handling terminal working directory: {e}")
        return {
            "working_dir": None,
            "updated": False,
            "status": "error",
            "error": str(e)
        }


# 함수 매핑 - 함수 이름을 함수 객체에 매핑
MCP_FUNCTION_IMPLEMENTATIONS = {
    # 브라우저 콘솔 함수
    "console_execute": console_execute,
    "console_logs": console_logs,
    "console_clear": console_clear,
    "console_sessions": console_sessions,
    
    # 터미널 함수
    "terminal_create": terminal_create,
    "terminal_delete": terminal_delete,
    "terminal_execute": terminal_execute,
    "terminal_history": terminal_history,
    "terminal_sessions": terminal_sessions,
    "terminal_workdir": terminal_workdir
}
