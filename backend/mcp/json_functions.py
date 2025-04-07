"""
Model Context Protocol (MCP) JSON 파일 처리 함수 구현
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("mcp.json")

class JSONFunctions:
    """JSON 파일 처리 관련 MCP 함수 구현"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            base_dir: 기본 작업 디렉토리 (None인 경우 현재 디렉토리 사용)
        """
        self.base_dir = base_dir or os.getcwd()
        logger.info(f"Initialized JSONFunctions with base_dir: {self.base_dir}")
    
    def _normalize_path(self, path: str) -> str:
        """
        경로 정규화 및 안전성 검증
        
        Args:
            path: 대상 경로
            
        Returns:
            정규화된 절대 경로
        """
        # 상대 경로인 경우 base_dir와 결합
        if not os.path.isabs(path):
            path = os.path.join(self.base_dir, path)
        
        # 경로 정규화
        normalized_path = os.path.normpath(os.path.abspath(path))
        
        # 보안 검사: base_dir 외부 접근 차단
        if not normalized_path.startswith(self.base_dir):
            raise ValueError(f"Path {path} is outside of allowed base directory")
        
        return normalized_path
    
    def read_json(self, path: str) -> Dict[str, Any]:
        """
        JSON 파일 읽기
        
        Args:
            path: 파일 경로
            
        Returns:
            JSON 데이터
        """
        try:
            normalized_path = self._normalize_path(path)
            
            if not os.path.exists(normalized_path):
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }
            
            with open(normalized_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return {
                "success": True,
                "data": data
            }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for file {path}: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid JSON in file: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error reading JSON file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_json(self, path: str, data: Dict[str, Any], indent: int = 2, ensure_ascii: bool = False) -> Dict[str, Any]:
        """
        JSON 파일 쓰기
        
        Args:
            path: 파일 경로
            data: 저장할 JSON 데이터
            indent: 들여쓰기 크기 (None인 경우 압축)
            ensure_ascii: ASCII 인코딩 강제 여부
            
        Returns:
            작업 결과
        """
        try:
            normalized_path = self._normalize_path(path)
            
            # 디렉토리 존재 확인 및 생성
            directory = os.path.dirname(normalized_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            return {
                "success": True,
                "path": path
            }
                
        except Exception as e:
            logger.error(f"Error writing JSON file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_json(self, path: str, updates: Dict[str, Any], create_if_not_exists: bool = False) -> Dict[str, Any]:
        """
        JSON 파일 부분 업데이트
        
        Args:
            path: 파일 경로
            updates: 업데이트할 데이터
            create_if_not_exists: 파일이 없는 경우 생성 여부
            
        Returns:
            작업 결과
        """
        try:
            normalized_path = self._normalize_path(path)
            
            # 파일 존재 확인
            if not os.path.exists(normalized_path):
                if create_if_not_exists:
                    # 파일 생성
                    return self.write_json(path, updates)
                else:
                    return {
                        "success": False,
                        "error": f"File not found: {path}"
                    }
            
            # 기존 파일 읽기
            with open(normalized_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 데이터 업데이트
            if isinstance(data, dict):
                data = self._deep_update(data, updates)
            else:
                return {
                    "success": False,
                    "error": "Root JSON element is not an object"
                }
            
            # 업데이트된 데이터 저장
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "path": path,
                "updated_data": data
            }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for file {path}: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid JSON in file: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error updating JSON file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_json(self, data: Dict[str, Any], schema_path: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        JSON 데이터 유효성 검사
        
        Args:
            data: 검사할 JSON 데이터
            schema_path: 스키마 파일 경로 (schema와 둘 중 하나 필수)
            schema: 스키마 데이터 (schema_path와 둘 중 하나 필수)
            
        Returns:
            검사 결과
        """
        try:
            # 스키마 가져오기
            if schema is None and schema_path is None:
                return {
                    "success": False,
                    "error": "Either schema or schema_path must be provided"
                }
            
            if schema is None:
                schema_result = self.read_json(schema_path)
                if not schema_result["success"]:
                    return schema_result
                schema = schema_result["data"]
            
            # JSON 스키마 검증 라이브러리 필요
            # 간단한 검증만 수행하는 예제 코드
            validation_errors = []
            
            # 필수 필드 검사
            if "required" in schema:
                for field in schema["required"]:
                    if field not in data:
                        validation_errors.append(f"Required field '{field}' is missing")
            
            # 타입 검사
            if "properties" in schema:
                for field, field_schema in schema["properties"].items():
                    if field in data:
                        # 타입 검사
                        if "type" in field_schema:
                            expected_type = field_schema["type"]
                            if expected_type == "string" and not isinstance(data[field], str):
                                validation_errors.append(f"Field '{field}' should be a string")
                            elif expected_type == "number" and not isinstance(data[field], (int, float)):
                                validation_errors.append(f"Field '{field}' should be a number")
                            elif expected_type == "integer" and not isinstance(data[field], int):
                                validation_errors.append(f"Field '{field}' should be an integer")
                            elif expected_type == "boolean" and not isinstance(data[field], bool):
                                validation_errors.append(f"Field '{field}' should be a boolean")
                            elif expected_type == "array" and not isinstance(data[field], list):
                                validation_errors.append(f"Field '{field}' should be an array")
                            elif expected_type == "object" and not isinstance(data[field], dict):
                                validation_errors.append(f"Field '{field}' should be an object")
            
            if validation_errors:
                return {
                    "success": False,
                    "valid": False,
                    "errors": validation_errors
                }
            
            return {
                "success": True,
                "valid": True
            }
                
        except Exception as e:
            logger.error(f"Error validating JSON: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _deep_update(self, source: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        딕셔너리 깊은 업데이트
        
        Args:
            source: 원본 딕셔너리
            updates: 업데이트할 데이터
            
        Returns:
            업데이트된 딕셔너리
        """
        for key, value in updates.items():
            if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                source[key] = self._deep_update(source[key], value)
            else:
                source[key] = value
        return source
