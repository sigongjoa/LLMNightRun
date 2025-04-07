"""
MCP 구성 및 컨텍스트 관리자

JSON 파일로 MCP 구성 및 컨텍스트를 관리하기 위한 모듈입니다.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Set
import datetime
import uuid

logger = logging.getLogger("mcp.config")

class MCPConfigManager:
    """MCP 구성 및 컨텍스트 파일 관리자"""
    
    def __init__(self, config_dir: str):
        """
        초기화
        
        Args:
            config_dir: 구성 파일이 저장될 디렉토리
        """
        self.config_dir = config_dir
        
        # 하위 디렉터리 생성
        self.contexts_dir = os.path.join(config_dir, "contexts")
        self.functions_dir = os.path.join(config_dir, "functions")
        self.schemas_dir = os.path.join(config_dir, "schemas")
        
        # 필요한 디렉터리 생성
        for directory in [self.config_dir, self.contexts_dir, self.functions_dir, self.schemas_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                
        logger.info(f"Initialized MCPConfigManager with config_dir: {config_dir}")
    
    # 컨텍스트 관련 메서드
    def list_contexts(self) -> List[str]:
        """
        사용 가능한 컨텍스트 목록 조회
        
        Returns:
            컨텍스트 ID 목록
        """
        return [
            f.replace(".json", "") 
            for f in os.listdir(self.contexts_dir) 
            if f.endswith(".json")
        ]
    
    def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        컨텍스트 조회
        
        Args:
            context_id: 컨텍스트 ID
            
        Returns:
            컨텍스트 데이터
        """
        file_path = os.path.join(self.contexts_dir, f"{context_id}.json")
        
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading context {context_id}: {str(e)}")
            return {}
    
    def save_context(self, context_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """
        컨텍스트 저장
        
        Args:
            context_id: 컨텍스트 ID
            data: 저장할 데이터
            merge: 기존 데이터와 병합 여부
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.contexts_dir, f"{context_id}.json")
        
        # 기존 데이터 병합
        if merge and os.path.exists(file_path):
            try:
                current_data = self.get_context(context_id)
                # 깊은 병합
                merged_data = self._deep_merge(current_data, data)
                data = merged_data
            except Exception as e:
                logger.error(f"Error merging context data: {str(e)}")
                # 오류 시 병합 없이 진행
        
        # 메타데이터 추가
        if '_metadata' not in data:
            data['_metadata'] = {}
        
        data['_metadata']['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved context {context_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving context {context_id}: {str(e)}")
            return False
    
    def delete_context(self, context_id: str) -> bool:
        """
        컨텍스트 삭제
        
        Args:
            context_id: 컨텍스트 ID
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.contexts_dir, f"{context_id}.json")
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted context {context_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting context {context_id}: {str(e)}")
            return False
    
    def create_context(self, data: Dict[str, Any] = None, context_id: str = None) -> str:
        """
        새 컨텍스트 생성
        
        Args:
            data: 초기 데이터 (선택 사항)
            context_id: 컨텍스트 ID (선택 사항, 없으면 자동 생성)
            
        Returns:
            생성된 컨텍스트 ID
        """
        if context_id is None:
            context_id = str(uuid.uuid4())
        
        if data is None:
            data = {}
        
        # 메타데이터 추가
        data['_metadata'] = {
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'id': context_id
        }
        
        self.save_context(context_id, data, merge=False)
        logger.info(f"Created new context with ID: {context_id}")
        
        return context_id
    
    # 함수 관련 메서드
    def list_function_groups(self) -> List[str]:
        """
        사용 가능한 함수 그룹 목록 조회
        
        Returns:
            함수 그룹 이름 목록
        """
        return [
            f.replace(".json", "") 
            for f in os.listdir(self.functions_dir) 
            if f.endswith(".json")
        ]
    
    def get_function_group(self, group_name: str) -> Dict[str, Any]:
        """
        함수 그룹 조회
        
        Args:
            group_name: 함수 그룹 이름
            
        Returns:
            함수 그룹 데이터
        """
        file_path = os.path.join(self.functions_dir, f"{group_name}.json")
        
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading function group {group_name}: {str(e)}")
            return {}
    
    def save_function_group(self, group_name: str, data: Dict[str, Any]) -> bool:
        """
        함수 그룹 저장
        
        Args:
            group_name: 함수 그룹 이름
            data: 저장할 데이터
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.functions_dir, f"{group_name}.json")
        
        # 메타데이터 추가
        if '_metadata' not in data:
            data['_metadata'] = {}
        
        data['_metadata']['updated_at'] = datetime.datetime.utcnow().isoformat()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved function group {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving function group {group_name}: {str(e)}")
            return False
    
    def delete_function_group(self, group_name: str) -> bool:
        """
        함수 그룹 삭제
        
        Args:
            group_name: 함수 그룹 이름
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.functions_dir, f"{group_name}.json")
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted function group {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting function group {group_name}: {str(e)}")
            return False
    
    # 스키마 관련 메서드
    def list_schemas(self) -> List[str]:
        """
        사용 가능한 스키마 목록 조회
        
        Returns:
            스키마 이름 목록
        """
        return [
            f.replace(".json", "") 
            for f in os.listdir(self.schemas_dir) 
            if f.endswith(".json")
        ]
    
    def get_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        스키마 조회
        
        Args:
            schema_name: 스키마 이름
            
        Returns:
            스키마 데이터
        """
        file_path = os.path.join(self.schemas_dir, f"{schema_name}.json")
        
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading schema {schema_name}: {str(e)}")
            return {}
    
    def save_schema(self, schema_name: str, data: Dict[str, Any]) -> bool:
        """
        스키마 저장
        
        Args:
            schema_name: 스키마 이름
            data: 저장할 데이터
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.schemas_dir, f"{schema_name}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved schema {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving schema {schema_name}: {str(e)}")
            return False
    
    def delete_schema(self, schema_name: str) -> bool:
        """
        스키마 삭제
        
        Args:
            schema_name: 스키마 이름
            
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.schemas_dir, f"{schema_name}.json")
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted schema {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting schema {schema_name}: {str(e)}")
            return False
    
    # 유틸리티 메서드
    def _deep_merge(self, source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        """
        두 딕셔너리의 깊은 병합
        
        Args:
            source: 소스 딕셔너리
            destination: 대상 딕셔너리
            
        Returns:
            병합된 딕셔너리
        """
        for key, value in destination.items():
            if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                source[key] = self._deep_merge(source[key], value)
            else:
                source[key] = value
        return source
    
    def export_all(self, output_file: str) -> bool:
        """
        모든 구성을 단일 JSON 파일로 내보내기
        
        Args:
            output_file: 출력 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            data = {
                "contexts": {},
                "functions": {},
                "schemas": {}
            }
            
            # 컨텍스트 내보내기
            for context_id in self.list_contexts():
                data["contexts"][context_id] = self.get_context(context_id)
            
            # 함수 그룹 내보내기
            for group_name in self.list_function_groups():
                data["functions"][group_name] = self.get_function_group(group_name)
            
            # 스키마 내보내기
            for schema_name in self.list_schemas():
                data["schemas"][schema_name] = self.get_schema(schema_name)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported all configurations to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configurations: {str(e)}")
            return False
    
    def import_all(self, input_file: str, overwrite: bool = False) -> bool:
        """
        구성 가져오기
        
        Args:
            input_file: 입력 파일 경로
            overwrite: 기존 항목 덮어쓰기 여부
            
        Returns:
            성공 여부
        """
        try:
            if not os.path.exists(input_file):
                logger.error(f"Import file not found: {input_file}")
                return False
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 컨텍스트 가져오기
            for context_id, context_data in data.get("contexts", {}).items():
                if overwrite or context_id not in self.list_contexts():
                    self.save_context(context_id, context_data, merge=False)
            
            # 함수 그룹 가져오기
            for group_name, group_data in data.get("functions", {}).items():
                if overwrite or group_name not in self.list_function_groups():
                    self.save_function_group(group_name, group_data)
            
            # 스키마 가져오기
            for schema_name, schema_data in data.get("schemas", {}).items():
                if overwrite or schema_name not in self.list_schemas():
                    self.save_schema(schema_name, schema_data)
            
            logger.info(f"Imported configurations from {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configurations: {str(e)}")
            return False
