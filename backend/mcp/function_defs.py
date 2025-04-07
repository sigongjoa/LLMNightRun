"""
MCP 함수 정의 모듈

브라우저 개발자 콘솔과 윈도우 터미널을 위한 MCP 함수를 정의합니다.
"""

from typing import Dict, Any, List, Optional

# 브라우저 콘솔 함수 정의
BROWSER_CONSOLE_FUNCTIONS = {
    "console_execute": {
        "name": "console_execute",
        "description": "브라우저 개발자 콘솔에서 JavaScript 코드를 실행합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id", "code"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "콘솔 세션 ID"
                },
                "code": {
                    "type": "string",
                    "description": "실행할 JavaScript 코드"
                },
                "timeout": {
                    "type": "integer",
                    "description": "실행 제한 시간 (초)",
                    "default": 30
                }
            }
        }
    },
    
    "console_logs": {
        "name": "console_logs",
        "description": "브라우저 개발자 콘솔에서 수집된 로그를 조회합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "콘솔 세션 ID"
                },
                "count": {
                    "type": "integer",
                    "description": "조회할 로그 수",
                    "default": 100
                },
                "level": {
                    "type": "string",
                    "description": "로그 레벨 필터 (info, warn, error 등)",
                    "enum": ["info", "warn", "error", "debug"]
                },
                "source": {
                    "type": "string",
                    "description": "로그 소스 필터 (console, network 등)",
                    "enum": ["console", "network", "javascript"]
                }
            }
        }
    },
    
    "console_clear": {
        "name": "console_clear",
        "description": "브라우저 개발자 콘솔에서 수집된 로그를 초기화합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "콘솔 세션 ID"
                }
            }
        }
    },
    
    "console_sessions": {
        "name": "console_sessions",
        "description": "활성 상태인 브라우저 개발자 콘솔 세션 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

# 터미널 함수 정의
TERMINAL_FUNCTIONS = {
    "terminal_create": {
        "name": "terminal_create",
        "description": "새 터미널 세션을 생성합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "working_dir": {
                    "type": "string",
                    "description": "초기 작업 디렉터리"
                }
            }
        }
    },
    
    "terminal_delete": {
        "name": "terminal_delete",
        "description": "터미널 세션을 삭제합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "터미널 세션 ID"
                }
            }
        }
    },
    
    "terminal_execute": {
        "name": "terminal_execute",
        "description": "터미널 명령어를 실행합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id", "command"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "터미널 세션 ID"
                },
                "command": {
                    "type": "string",
                    "description": "실행할 명령어"
                },
                "timeout": {
                    "type": "integer",
                    "description": "실행 제한 시간 (초)",
                    "default": 30
                },
                "working_dir": {
                    "type": "string",
                    "description": "작업 디렉터리 (세션 기본값을 대체)"
                }
            }
        }
    },
    
    "terminal_history": {
        "name": "terminal_history",
        "description": "터미널 명령어 실행 기록을 조회합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "터미널 세션 ID"
                },
                "count": {
                    "type": "integer",
                    "description": "조회할 기록 수",
                    "default": 10
                }
            }
        }
    },
    
    "terminal_sessions": {
        "name": "terminal_sessions",
        "description": "활성 상태인 터미널 세션 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    
    "terminal_workdir": {
        "name": "terminal_workdir",
        "description": "터미널 세션의 작업 디렉터리를 조회하거나 설정합니다.",
        "parameters": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "터미널 세션 ID"
                },
                "working_dir": {
                    "type": "string",
                    "description": "설정할 작업 디렉터리 (생략 시 조회만 수행)"
                }
            }
        }
    }
}

# 모든 MCP 함수 정의
MCP_FUNCTIONS = {
    **BROWSER_CONSOLE_FUNCTIONS,
    **TERMINAL_FUNCTIONS
}
