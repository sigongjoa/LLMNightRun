"""
MCP 함수 레지스트리 모듈

MCP 함수와 함수 정의를 관리하는 레지스트리 클래스를 제공합니다.
"""

import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger("mcp.function_registry")

class FunctionRegistry:
    """MCP 함수 레지스트리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.functions: Dict[str, Callable] = {}
        self.function_definitions: Dict[str, Dict[str, Any]] = {}
        logger.info("FunctionRegistry initialized")
    
    def register_function(self, name: str, function: Callable, definition: Optional[Dict[str, Any]] = None) -> None:
        """
        함수 등록
        
        Args:
            name: 함수 이름
            function: 함수 객체
            definition: 함수 정의 (JSON Schema)
        """
        self.functions[name] = function
        
        if definition:
            self.function_definitions[name] = definition
        
        logger.info(f"Registered function: {name}")
    
    def has_function(self, name: str) -> bool:
        """
        함수 존재 여부 확인
        
        Args:
            name: 함수 이름
            
        Returns:
            bool: 함수 존재 여부
        """
        return name in self.functions
    
    def has_function_definition(self, name: str) -> bool:
        """
        함수 정의 존재 여부 확인
        
        Args:
            name: 함수 이름
            
        Returns:
            bool: 함수 정의 존재 여부
        """
        return name in self.function_definitions
    
    def get_function(self, name: str) -> Callable:
        """
        함수 가져오기
        
        Args:
            name: 함수 이름
            
        Returns:
            Callable: 함수 객체
            
        Raises:
            KeyError: 함수가 존재하지 않는 경우
        """
        if not self.has_function(name):
            raise KeyError(f"Function '{name}' not registered")
        
        return self.functions[name]
    
    def get_function_definition(self, name: str) -> Dict[str, Any]:
        """
        함수 정의 가져오기
        
        Args:
            name: 함수 이름
            
        Returns:
            Dict[str, Any]: 함수 정의
            
        Raises:
            KeyError: 함수 정의가 존재하지 않는 경우
        """
        if not self.has_function_definition(name):
            raise KeyError(f"Function definition for '{name}' not registered")
        
        return self.function_definitions[name]
    
    def list_functions(self) -> List[str]:
        """
        등록된 함수 목록 가져오기
        
        Returns:
            List[str]: 함수 이름 목록
        """
        return list(self.functions.keys())
    
    def list_function_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        등록된 함수 정의 목록 가져오기
        
        Returns:
            Dict[str, Dict[str, Any]]: 함수 이름과 정의 매핑
        """
        return self.function_definitions.copy()
    
    def remove_function(self, name: str) -> bool:
        """
        함수 제거
        
        Args:
            name: 함수 이름
            
        Returns:
            bool: 제거 성공 여부
        """
        if not self.has_function(name):
            return False
        
        del self.functions[name]
        
        if self.has_function_definition(name):
            del self.function_definitions[name]
        
        logger.info(f"Removed function: {name}")
        return True
    
    def clear(self) -> None:
        """모든 함수 및 정의 제거"""
        self.functions.clear()
        self.function_definitions.clear()
        logger.info("Cleared all functions and definitions")

# 싱글톤 인스턴스
_function_registry = None

def get_function_registry() -> FunctionRegistry:
    """
    함수 레지스트리 인스턴스 가져오기
    
    Returns:
        FunctionRegistry: 함수 레지스트리 인스턴스
    """
    global _function_registry
    
    if _function_registry is None:
        _function_registry = FunctionRegistry()
        
        # 기본 함수 등록
        from .fs_functions import FSFunctions
        from .export_functions import ExportFunctions
        from .prompt_engineering import PromptEngineering
        
        fs_functions = FSFunctions()
        export_functions = ExportFunctions()
        prompt_engineering = PromptEngineering()
        _function_registry.register_function("read_file", fs_functions.read_file, {
            "name": "read_file",
            "description": "파일 내용을 읽습니다",
            "parameters": {
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "읽을 파일 경로"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "파일 인코딩 (기본값: utf-8)",
                        "default": "utf-8"
                    }
                }
            },
            "examples": [
                "main.py 파일의 내용을 읽어줘",
                "requirements.txt 파일을 확인해줘"
            ]
        })
        
        _function_registry.register_function("write_file", fs_functions.write_file, {
            "name": "write_file",
            "description": "파일에 내용을 씁니다",
            "parameters": {
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "쓸 파일 경로"
                    },
                    "content": {
                        "type": "string",
                        "description": "파일에 쓸 내용"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "파일 인코딩 (기본값: utf-8)",
                        "default": "utf-8"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "기존 파일 덮어쓰기 여부 (기본값: true)",
                        "default": True
                    }
                }
            },
            "examples": [
                "test.py 파일을 생성하고 내용을 작성해줘",
                "config.json 파일에 설정을 저장해줘"
            ]
        })
        
        _function_registry.register_function("list_directory", fs_functions.list_directory, {
            "name": "list_directory",
            "description": "디렉토리 내용을 나열합니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "나열할 디렉토리 경로 (기본값: ./)",
                        "default": "./"
                    }
                }
            },
            "examples": [
                "현재 디렉토리의 파일 목록을 보여줘",
                "backend 폴더의 내용을 알려줘"
            ]
        })
        
        _function_registry.register_function("create_directory", fs_functions.create_directory, {
            "name": "create_directory",
            "description": "디렉토리를 생성합니다",
            "parameters": {
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "생성할 디렉토리 경로"
                    }
                }
            },
            "examples": [
                "temp 디렉토리를 생성해줘",
                "새 프로젝트 폴더를 만들어줘"
            ]
        })
        
        _function_registry.register_function("delete", fs_functions.delete, {
            "name": "delete",
            "description": "파일 또는 디렉토리를 삭제합니다",
            "parameters": {
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "삭제할 파일 또는 디렉토리 경로"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "디렉토리인 경우 재귀적 삭제 여부 (기본값: false)",
                        "default": False
                    }
                }
            },
            "examples": [
                "temp.txt 파일을 삭제해줘",
                "빈 디렉토리를 삭제해줘"
            ]
        })
        
        # 채팅 내보내기 함수 등록
        _function_registry.register_function("export_chat_history", export_functions.export_chat_history, {
            "name": "export_chat_history",
            "description": "채팅 내역을 파일로 내보냅니다",
            "parameters": {
                "type": "object",
                "required": ["history"],
                "properties": {
                    "history": {
                        "type": "array",
                        "description": "채팅 내역 목록",
                        "items": {
                            "type": "object"
                        }
                    },
                    "format": {
                        "type": "string",
                        "description": "내보내기 형식 (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "json"
                    },
                    "title": {
                        "type": "string",
                        "description": "내보내기 제목 (없으면 자동 생성)"
                    }
                }
            },
            "examples": [
                "현재 대화 내용을 JSON으로 내보내줘",
                "대화 내용을 마크다운 형식으로 저장해줘"
            ]
        })
        
        _function_registry.register_function("get_exports_list", export_functions.get_exports_list, {
            "name": "get_exports_list",
            "description": "내보낸 채팅 내역 목록을 조회합니다",
            "parameters": {
                "type": "object",
                "properties": {}
            },
            "examples": [
                "내보낸 대화 목록을 보여줘",
                "이전에 저장한 대화 파일들을 찾아줘"
            ]
        })
        
        _function_registry.register_function("delete_export", export_functions.delete_export, {
            "name": "delete_export",
            "description": "내보낸 채팅 내역 파일을 삭제합니다",
            "parameters": {
                "type": "object",
                "required": ["filename"],
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "삭제할 파일 이름"
                    }
                }
            },
            "examples": [
                "Chat_Export_20250408_123045.json 파일을 삭제해줘"
            ]
        })
        
        # 프롬프트 엔지니어링 함수 등록
        _function_registry.register_function("get_prompt_settings", prompt_engineering.get_settings, {
            "name": "get_prompt_settings",
            "description": "프롬프트 엔지니어링 설정을 조회합니다",
            "parameters": {
                "type": "object",
                "properties": {}
            },
            "examples": [
                "현재 프롬프트 설정을 보여줘",
                "프롬프트 엔지니어링 옵션을 확인하고 싶어"
            ]
        })
        
        _function_registry.register_function("update_prompt_settings", prompt_engineering.update_settings, {
            "name": "update_prompt_settings",
            "description": "프롬프트 엔지니어링 설정을 업데이트합니다",
            "parameters": {
                "type": "object",
                "required": ["new_settings"],
                "properties": {
                    "new_settings": {
                        "type": "object",
                        "description": "업데이트할 설정 객체"
                    }
                }
            },
            "examples": [
                "시스템 프롬프트를 변경해줘",
                "프롬프트 설정의 temperature를 0.8로 변경해줘"
            ]
        })
        
        _function_registry.register_function("get_prompt_templates", prompt_engineering.get_templates, {
            "name": "get_prompt_templates",
            "description": "프롬프트 템플릿 목록을 조회합니다",
            "parameters": {
                "type": "object",
                "properties": {}
            },
            "examples": [
                "사용 가능한 프롬프트 템플릿을 보여줘",
                "저장된 프롬프트 프리셋 목록을 확인하고 싶어"
            ]
        })
        
        _function_registry.register_function("get_prompt_template", prompt_engineering.get_template, {
            "name": "get_prompt_template",
            "description": "특정 프롬프트 템플릿을 조회합니다",
            "parameters": {
                "type": "object",
                "required": ["template_id"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "템플릿 ID"
                    }
                }
            },
            "examples": [
                "technical 템플릿의 내용을 보여줘",
                "creative 프롬프트 설정 세부 정보를 알려줘"
            ]
        })
        
        _function_registry.register_function("set_active_template", prompt_engineering.set_active_template, {
            "name": "set_active_template",
            "description": "활성 프롬프트 템플릿을 설정합니다",
            "parameters": {
                "type": "object",
                "required": ["template_id"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "활성화할 템플릿 ID"
                    }
                }
            },
            "examples": [
                "technical 템플릿을 활성화해줘",
                "reasoning 프롬프트 모드로 변경해줘"
            ]
        })
        
        _function_registry.register_function("create_prompt_template", prompt_engineering.create_template, {
            "name": "create_prompt_template",
            "description": "새 프롬프트 템플릿을 생성합니다",
            "parameters": {
                "type": "object",
                "required": ["template_id", "template_data"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "템플릿 ID (영문 + 숫자만 가능)"
                    },
                    "template_data": {
                        "type": "object",
                        "description": "템플릿 데이터 객체",
                        "required": ["name", "description", "systemPrompt"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "템플릿 이름"
                            },
                            "description": {
                                "type": "string",
                                "description": "템플릿 설명"
                            },
                            "systemPrompt": {
                                "type": "string",
                                "description": "시스템 프롬프트"
                            }
                        }
                    }
                }
            },
            "examples": [
                "새로운 프롬프트 템플릿을 만들어줘",
                "코딩 전문가 모드 템플릿을 생성해줘"
            ]
        })
        
        _function_registry.register_function("update_prompt_template", prompt_engineering.update_template, {
            "name": "update_prompt_template",
            "description": "프롬프트 템플릿을 업데이트합니다",
            "parameters": {
                "type": "object",
                "required": ["template_id", "template_data"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "템플릿 ID"
                    },
                    "template_data": {
                        "type": "object",
                        "description": "업데이트할 템플릿 데이터 객체"
                    }
                }
            },
            "examples": [
                "technical 템플릿의 시스템 프롬프트를 수정해줘",
                "creative 템플릿의 temperature 값을 변경해줘"
            ]
        })
        
        _function_registry.register_function("delete_prompt_template", prompt_engineering.delete_template, {
            "name": "delete_prompt_template",
            "description": "프롬프트 템플릿을 삭제합니다",
            "parameters": {
                "type": "object",
                "required": ["template_id"],
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "삭제할 템플릿 ID"
                    }
                }
            },
            "examples": [
                "mytemplate 템플릿을 삭제해줘",
                "더 이상 필요없는 custom 템플릿을 제거해줘"
            ]
        })
        
        _function_registry.register_function("get_active_template_settings", prompt_engineering.get_active_template_settings, {
            "name": "get_active_template_settings",
            "description": "현재 활성화된 프롬프트 템플릿 설정을 조회합니다",
            "parameters": {
                "type": "object",
                "properties": {}
            },
            "examples": [
                "현재 사용 중인 템플릿 설정을 보여줘",
                "활성화된 프롬프트 프리셋 정보를 알려줘"
            ]
        })
        
    return _function_registry