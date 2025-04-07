"""
MCP 함수 구현 모듈

브라우저 개발자 콘솔을 위한 MCP 함수 구현을 제공합니다.
터미널 기능은 비활성화되었습니다.
"""

import logging
from typing import Dict, Any, List, Optional

from .tools.browser_console import BrowserConsoleTool
from .tools.terminal import TerminalTool

logger = logging.getLogger("mcp.functions")

# 도구 인스턴스 생성
browser_console_tool = BrowserConsoleTool()
terminal_tool = TerminalTool()  # 더미 인스턴스 (기능 없음)


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
        # 코드 유효성 검사
        if not code or not code.strip():
            return {
                "error": "JavaScript code is empty",
                "status": "error",
                "result": None
            }
        
        result = await browser_console_tool.execute_javascript(session_id, code, timeout)
        return result
    except ValueError as e:
        # 세션 없음 또는 입력 오류
        logger.warning(f"ValueError executing JavaScript: {e}")
        return {
            "error": str(e),
            "status": "error",
            "result": None
        }
    except TimeoutError as e:
        # 실행 시간 초과
        logger.warning(f"Timeout executing JavaScript: {e}")
        return {
            "error": f"Execution timed out after {timeout} seconds",
            "status": "timeout",
            "result": None
        }
    except ConnectionError as e:
        # 연결 문제
        logger.error(f"Connection error executing JavaScript: {e}")
        return {
            "error": "Browser connection error: " + str(e),
            "status": "connection_error",
            "result": None
        }
    except Exception as e:
        # 기타 예외
        logger.error(f"Error executing JavaScript: {e}")
        # 디버깅을 위한 자세한 오류 정보
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
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


# 터미널 함수 구현 (비활성화됨)
def terminal_create(working_dir: str = None) -> Dict[str, Any]:
    """새 터미널 세션 생성 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "session_id": "dummy-session",
        "working_dir": "D:\\",
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }

def terminal_delete(session_id: str) -> Dict[str, Any]:
    """터미널 세션 삭제 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "success": True,
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }

async def terminal_execute(session_id: str, command: str, timeout: int = None, working_dir: str = None) -> Dict[str, Any]:
    """터미널 명령어 실행 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "stdout": "Terminal functionality is disabled",
        "stderr": "",
        "exit_code": 0,
        "error": None,
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }

def terminal_history(session_id: str, count: int = 10) -> Dict[str, Any]:
    """터미널 명령어 실행 기록 조회 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "history": [],
        "count": 0,
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }

def terminal_sessions() -> Dict[str, Any]:
    """터미널 세션 목록 조회 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "sessions": [],
        "count": 0,
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }

def terminal_workdir(session_id: str, working_dir: str = None) -> Dict[str, Any]:
    """터미널 작업 디렉터리 조회/설정 (비활성화됨)"""
    logger.warning("Terminal functionality is disabled")
    return {
        "working_dir": "D:\\",
        "updated": False,
        "status": "success",
        "disabled": True,
        "message": "Terminal functionality is disabled"
    }


# 함수 매핑 - 함수 이름을 함수 객체에 매핑
MCP_FUNCTION_IMPLEMENTATIONS = {
    # 브라우저 콘솔 함수
    "console_execute": console_execute,
    "console_logs": console_logs,
    "console_clear": console_clear,
    "console_sessions": console_sessions,
    
    # 터미널 함수 (비활성화됨)
    "terminal_create": terminal_create,
    "terminal_delete": terminal_delete,
    "terminal_execute": terminal_execute,
    "terminal_history": terminal_history,
    "terminal_sessions": terminal_sessions,
    "terminal_workdir": terminal_workdir
}
