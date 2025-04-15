"""
Model Context Protocol (MCP) 메시지 처리 핸들러
"""

import json
import uuid
import logging
import os
import requests
import difflib
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional

from .protocol import (
    MCPMessage, MCPMessageType, MCPFunctionCall, 
    MCPFunctionResponse, MCPContextUpdate, MCPError
)
from .config_manager import MCPConfigManager

logger = logging.getLogger("mcp")


class MCPHandler:
    """MCP 프로토콜 처리 핸들러"""
    
    def __init__(self, config_dir: str = None):
        """
        초기화
        
        Args:
            config_dir: 구성 파일 저장 디렉토리
        """
        self.registered_functions: Dict[str, Callable] = {}
        self.contexts: Dict[str, Dict[str, Any]] = {}
        
        # 기본 config_dir 설정
        if config_dir is None:
            # 프로젝트 루트 디렉토리 추정
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            config_dir = os.path.join(project_root, "config", "mcp")
        
        # 구성 관리자 초기화
        self.config_manager = MCPConfigManager(config_dir)
        logger.info(f"Initialized MCPHandler with config_dir: {config_dir}")
        
        # 파일 시스템에서 컨텍스트 로드
        self._load_contexts_from_files()
        
        # 기본 시스템 함수 등록
        self._register_system_functions()
    
    def register_function(self, name: str, func: Callable) -> None:
        """
        함수 등록
        
        Args:
            name: 함수 이름
            func: 함수 객체
        """
        logger.info(f"Registering MCP function: {name}")
        self.registered_functions[name] = func
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 메시지 처리
        
        Args:
            message_data: 메시지 데이터
            
        Returns:
            처리 결과
        """
        try:
            # V2 호환성을 위해 parse_obj 대신 model_validate 사용
            message = MCPMessage.model_validate(message_data)
            
            if message.type == MCPMessageType.FUNCTION_CALL:
                return await self._handle_function_call(message)
            elif message.type == MCPMessageType.CONTEXT_UPDATE:
                return self._handle_context_update(message)
            elif message.type == "mcp_test":
                # 명시적으로 비동기 함수로 처리
                import inspect
                if inspect.iscoroutinefunction(self._handle_mcp_test):
                    return await self._handle_mcp_test(message)
                else:
                    return self._handle_mcp_test(message)
            else:
                raise ValueError(f"Unsupported message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {str(e)}")
            return self._create_error_response(
                str(e), 
                "mcp_processing_error",
                request_id=message_data.get("request_id")
            )
    
    async def _handle_function_call(self, message: MCPMessage) -> Dict[str, Any]:
        """
        함수 호출 처리
        
        Args:
            message: 함수 호출 메시지
            
        Returns:
            함수 응답
        """
        function_call: MCPFunctionCall = message.content
        
        if function_call.name not in self.registered_functions:
            return self._create_error_response(
                f"Function '{function_call.name}' not registered",
                "function_not_found",
                request_id=message.request_id
            )
        
        try:
            func = self.registered_functions[function_call.name]
            import inspect
            
            # 비동기 함수인 경우 await 사용
            if inspect.iscoroutinefunction(func):
                result = await func(**function_call.arguments)
            else:
                # 동기 함수를 별도 스레드에서 실행
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                import functools
                
                with ThreadPoolExecutor() as pool:
                    result = await asyncio.get_event_loop().run_in_executor(
                        pool, functools.partial(func, **function_call.arguments)
                    )
            
            # 로깅 추가
            logger.debug(f"Function '{function_call.name}' executed with result: {result}")
            
            response = MCPMessage(
                type=MCPMessageType.FUNCTION_RESPONSE,
                content=MCPFunctionResponse(
                    call_id=function_call.call_id,
                    result=result
                ),
                request_id=message.request_id,
                timestamp=datetime.utcnow().isoformat(),
                version=message.version
            )
            
            # V2 호환성을 위해 dict 대신 model_dump 사용
            return response.model_dump()
            
        except Exception as e:
            logger.error(f"Error executing function '{function_call.name}': {str(e)}")
            return self._create_error_response(
                f"Error executing function: {str(e)}",
                "function_execution_error",
                request_id=message.request_id
            )
    
    def _handle_context_update(self, message: MCPMessage) -> Dict[str, Any]:
        """
        컨텍스트 업데이트 처리
        
        Args:
            message: 컨텍스트 업데이트 메시지
            
        Returns:
            업데이트 결과
        """
        context_update: MCPContextUpdate = message.content
        
        if context_update.context_id not in self.contexts:
            self.contexts[context_update.context_id] = {}
        
        # 컨텍스트 업데이트
        self.contexts[context_update.context_id].update(context_update.data)
        
        # 파일에도 저장
        self.config_manager.save_context(
            context_update.context_id, 
            context_update.data,
            merge=True
        )
        
        # 성공 응답
        return {
            "type": "context_update_success",
            "request_id": message.request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": context_update.context_id
        }
    
    def _create_error_response(self, message: str, code: str, details: Dict[str, Any] = None, request_id: str = None) -> Dict[str, Any]:
        """
        에러 응답 생성
        
        Args:
            message: 에러 메시지
            code: 에러 코드
            details: 상세 정보
            request_id: 요청 ID
            
        Returns:
            에러 응답
        """
        error_response = MCPMessage(
            type=MCPMessageType.ERROR,
            content=MCPError(
                message=message,
                code=code,
                details=details
            ),
            request_id=request_id or str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # V2 호환성을 위해 dict 대신 model_dump 사용
        return error_response.model_dump()
    
    def _load_contexts_from_files(self):
        """파일에서 컨텍스트 로드"""
        context_ids = self.config_manager.list_contexts()
        for context_id in context_ids:
            try:
                context_data = self.config_manager.get_context(context_id)
                if context_data:
                    self.contexts[context_id] = context_data
                    logger.debug(f"Loaded context {context_id} from file")
            except Exception as e:
                logger.error(f"Error loading context {context_id}: {str(e)}")
    
    def create_context(self, data: Dict[str, Any] = None, context_id: str = None) -> str:
        """
        새 컨텍스트 생성
        
        Args:
            data: 초기 데이터
            context_id: 컨텍스트 ID (없으면 자동 생성)
            
        Returns:
            생성된 컨텍스트 ID
        """
        # 구성 관리자를 통해 생성
        context_id = self.config_manager.create_context(data, context_id)
        
        # 메모리에도 저장
        if data is None:
            data = {}
        self.contexts[context_id] = data
        
        return context_id
    
    def delete_context(self, context_id: str) -> bool:
        """
        컨텍스트 삭제
        
        Args:
            context_id: 컨텍스트 ID
            
        Returns:
            성공 여부
        """
        # 구성 관리자에서 삭제
        result = self.config_manager.delete_context(context_id)
        
        # 메모리에서도 삭제
        if context_id in self.contexts:
            del self.contexts[context_id]
        
        return result
    
    def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        컨텍스트 조회
        
        Args:
            context_id: 컨텍스트 ID
            
        Returns:
            컨텍스트 데이터
        """
        # 먼저 메모리에서 확인
        if context_id in self.contexts:
            return self.contexts[context_id]
        
        # 파일에서 로드
        context_data = self.config_manager.get_context(context_id)
        if context_data:
            # 메모리에 캐싱
            self.contexts[context_id] = context_data
        
        return context_data or {}
    
    def list_contexts(self) -> List[str]:
        """
        컨텍스트 목록 조회
        
        Returns:
            컨텍스트 ID 목록
        """
        # 구성 관리자에서 목록 조회
        return self.config_manager.list_contexts()
    
    def export_config(self, output_file: str) -> bool:
        """
        구성 내보내기
        
        Args:
            output_file: 출력 파일 경로
            
        Returns:
            성공 여부
        """
        return self.config_manager.export_all(output_file)
    
    def import_config(self, input_file: str, overwrite: bool = False) -> bool:
        """
        구성 가져오기
        
        Args:
            input_file: 입력 파일 경로
            overwrite: 기존 항목 덮어쓰기 여부
            
        Returns:
            성공 여부
        """
        result = self.config_manager.import_all(input_file, overwrite)
        if result:
            # 가져오기 성공 시 메모리 컨텍스트 갱신
            self._load_contexts_from_files()
        return result
    
    def save_function_group(self, group_name: str, functions: Dict[str, Dict[str, Any]]) -> bool:
        """
        함수 그룹 저장
        
        Args:
            group_name: 그룹 이름
            functions: 함수 정보
            
        Returns:
            성공 여부
        """
        return self.config_manager.save_function_group(group_name, functions)
    
    def get_function_group(self, group_name: str) -> Dict[str, Any]:
        """
        함수 그룹 조회
        
        Args:
            group_name: 그룹 이름
            
        Returns:
            함수 그룹 정보
        """
        return self.config_manager.get_function_group(group_name)
    
    def list_function_groups(self) -> List[str]:
        """
        함수 그룹 목록 조회
        
        Returns:
            함수 그룹 이름 목록
        """
        return self.config_manager.list_function_groups()
        
    def list_directory(self, path: str) -> Dict[str, Any]:
        """
        지정된 디렉토리의 콘텐츠를 보여줍니다.
        
        Args:
            path: 조회할 디렉토리 경로
            
        Returns:
            파일 및 디렉토리 목록
        """
        try:
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"Path not found: {path}"
                }
                
            if not os.path.isdir(path):
                return {
                    "success": False,
                    "error": f"Not a directory: {path}"
                }
            
            # 디렉토리 내용 조회
            contents = os.listdir(path)
            files = []
            directories = []
            
            for item in contents:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    directories.append({
                        "name": item,
                        "type": "directory",
                        "path": item_path
                    })
                else:
                    try:
                        size = os.path.getsize(item_path)
                    except (OSError, FileNotFoundError):
                        size = 0
                        
                    files.append({
                        "name": item,
                        "type": "file",
                        "path": item_path,
                        "size": size
                    })
            
            return {
                "success": True,
                "path": path,
                "directories": directories,
                "files": files,
                "total_items": len(contents)
            }
            
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_files(self, path: str, pattern: str, recursive: bool = True) -> Dict[str, Any]:
        """
        파일 검색
        
        Args:
            path: 검색 시작 디렉토리
            pattern: 검색 패턴 (이름 포함 검색)
            recursive: 하위 디렉토리 검색 여부
            
        Returns:
            검색 결과
        """
        try:
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"Path not found: {path}"
                }
                
            if not os.path.isdir(path):
                return {
                    "success": False,
                    "error": f"Not a directory: {path}"
                }
            
            results = []
            pattern = pattern.lower()  # 대소문자 구분 없이 검색
            
            if recursive:
                # 하위 디렉토리 포함 검색
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if pattern in file.lower():
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                            except (OSError, FileNotFoundError):
                                size = 0
                                
                            results.append({
                                "name": file,
                                "path": file_path,
                                "type": "file",
                                "size": size
                            })
                    
                    # 디렉토리도 검색
                    for dir_name in dirs:
                        if pattern in dir_name.lower():
                            dir_path = os.path.join(root, dir_name)
                            results.append({
                                "name": dir_name,
                                "path": dir_path,
                                "type": "directory"
                            })
            else:
                # 현재 디렉토리만 검색
                contents = os.listdir(path)
                for item in contents:
                    if pattern in item.lower():
                        item_path = os.path.join(path, item)
                        if os.path.isdir(item_path):
                            results.append({
                                "name": item,
                                "path": item_path,
                                "type": "directory"
                            })
                        else:
                            try:
                                size = os.path.getsize(item_path)
                            except (OSError, FileNotFoundError):
                                size = 0
                                
                            results.append({
                                "name": item,
                                "path": item_path,
                                "type": "file",
                                "size": size
                            })
            
            return {
                "success": True,
                "path": path,
                "pattern": pattern,
                "recursive": recursive,
                "results": results,
                "total_matches": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def edit_file(self, path: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """
        텍스트 파일의 특정 부분을 수정하고 변경사항을 보여줌
        
        Args:
            path: 수정할 파일 경로
            old_text: 교체할 원본 텍스트
            new_text: 새로운 텍스트
            
        Returns:
            편집 결과 및 diff 정보
        """
        try:
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"파일을 찾을 수 없습니다: {path}"
                }
                
            if not os.path.isfile(path):
                return {
                    "success": False,
                    "error": f"경로가 파일이 아닙니다: {path}"
                }
            
            # 파일 내용 읽기
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                return {
                    "success": False,
                    "error": f"텍스트 파일이 아닙니다: {path}"
                }
            
            # 내용이 존재하는지 확인
            if old_text not in content:
                return {
                    "success": False,
                    "error": f"지정한 원본 텍스트를 파일에서 찾을 수 없습니다."
                }
            
            # 내용 교체
            new_content = content.replace(old_text, new_text)
            
            # diff 생성
            diff = list(difflib.unified_diff(
                content.splitlines(),
                new_content.splitlines(),
                fromfile=f'a/{os.path.basename(path)}',
                tofile=f'b/{os.path.basename(path)}',
                lineterm=''
            ))
            
            # 파일 쓰기
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            return {
                "success": True,
                "path": path,
                "diff": '\n'.join(diff),
                "changes": {
                    "old_text": old_text,
                    "new_text": new_text
                }
            }
                
        except Exception as e:
            logger.error(f"Error editing file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _register_system_functions(self):
        """
        기본 시스템 함수 등록
        """
        logger.info("Registering system functions")
        
        # 파일 편집 함수 등록
        self.register_function("edit_file", self.edit_file)
        
        # 파일 시스템 탐색 함수 등록
        self.register_function("list_directory", self.list_directory)
        self.register_function("search_files", self.search_files)
        
    async def _handle_mcp_test(self, message: MCPMessage) -> Dict[str, Any]:
        """
        MCP 테스트 메시지 처리
        
        Args:
            message: 테스트 메시지
            
        Returns:
            테스트 결과
        """
        try:
            content = message.content
            context_id = content.get('context_id')
            
            if not context_id or context_id not in self.contexts:
                return self._create_error_response(
                    f"Context ID '{context_id}' not found",
                    "context_not_found",
                    request_id=message.request_id
                )
            
            # 컨텍스트에서 LLM 설정 가져오기
            context_data = self.get_context(context_id)
            llm_config = context_data.get('llm_config', {})
            
            if not llm_config:
                return self._create_error_response(
                    "No LLM configuration found in context",
                    "missing_llm_config",
                    request_id=message.request_id
                )
                
            # 로컬 LLM 연결 테스트
            provider = llm_config.get('provider', 'local')
            base_url = llm_config.get('baseUrl', 'http://localhost:1234/v1')
            api_key = llm_config.get('apiKey', '')
            model = llm_config.get('model', 'local-model')
            
            # 간단한 요청으로 LLM 테스트
            try:
                if provider == 'local':
                    # 단순 echo 요청으로 연결 테스트
                    headers = {}
                    if api_key:
                        headers['Authorization'] = f"Bearer {api_key}"
                        
                    test_url = f"{base_url}/chat/completions"
                    test_data = {
                        "model": model,
                        "messages": [{"role": "system", "content": "Test connection"}, 
                                     {"role": "user", "content": "Echo: LLMNightRun test"}],
                        "max_tokens": 10
                    }
                    
                    # requests.post 대신 asyncio를 사용하는 것이 좋지만, 간단한 수정을 위해 aiohttp를 필요로 하지 않도록 유지
                    response = requests.post(test_url, json=test_data, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "message": "LLM connection test successful",
                            "llm_response": response.json(),
                            "request_id": message.request_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        return self._create_error_response(
                            f"LLM connection failed: {response.status_code} - {response.text}",
                            "llm_connection_error",
                            request_id=message.request_id
                        )
                else:
                    # 다른 프로바이더 구현 추가 가능...
                    return self._create_error_response(
                        f"Provider '{provider}' not yet supported for testing",
                        "provider_not_supported",
                        request_id=message.request_id
                    )
            except requests.exceptions.RequestException as e:
                return self._create_error_response(
                    f"LLM connection failed: {str(e)}",
                    "llm_connection_error",
                    request_id=message.request_id
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP test message: {str(e)}")
            return self._create_error_response(
                f"Error handling MCP test: {str(e)}",
                "mcp_test_error",
                request_id=message.request_id
            )
