"""
Model Context Protocol (MCP) 파일 시스템 함수 구현
"""

import os
import json
import base64
import logging
from typing import Dict, Any, List, Optional
import shutil

logger = logging.getLogger("mcp.fs")

class FSFunctions:
    """파일 시스템 관련 MCP 함수 구현"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            base_dir: 기본 작업 디렉토리 (None인 경우 현재 디렉토리 사용)
        """
        self.base_dir = base_dir or os.getcwd()
        logger.info(f"Initialized FSFunctions with base_dir: {self.base_dir}")
    
    def _normalize_path(self, path: str) -> str:
        """
        경로 정규화 및 안전성 검증
        
        Args:
            path: 대상 경로
            
        Returns:
            정규화된 절대 경로
        """
        # 드라이브 루트 경로 처리 (예: D:\)
        if path.lower().startswith('d:\\'):
            return path  # 드라이브 루트 경로는 그대로 반환
            
        # 상대 경로인 경우 base_dir와 결합
        if not os.path.isabs(path):
            path = os.path.join(self.base_dir, path)
        
        # 경로 정규화
        normalized_path = os.path.normpath(os.path.abspath(path))
        
        # 보안 검사: base_dir 외부 접근 차단 (드라이브 루트인 경우 예외)
        if not normalized_path.startswith(self.base_dir) and not normalized_path.lower().startswith('d:\\'):
            raise ValueError(f"Path {path} is outside of allowed directories")
        
        return normalized_path
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        파일 읽기
        
        Args:
            path: 파일 경로
            encoding: 파일 인코딩 (이진 파일의 경우 None)
            
        Returns:
            파일 내용이 포함된 객체
        """
        try:
            normalized_path = self._normalize_path(path)
            
            if not os.path.exists(normalized_path):
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }
            
            if not os.path.isfile(normalized_path):
                return {
                    "success": False,
                    "error": f"Path is not a file: {path}"
                }
            
            if encoding:
                # 텍스트 파일
                with open(normalized_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    
                return {
                    "success": True,
                    "content": content,
                    "encoding": encoding,
                    "size": os.path.getsize(normalized_path)
                }
            else:
                # 바이너리 파일
                with open(normalized_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('ascii')
                    
                return {
                    "success": True,
                    "content": content,
                    "encoding": "base64",
                    "size": os.path.getsize(normalized_path)
                }
                
        except Exception as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8", overwrite: bool = True) -> Dict[str, Any]:
        """
        파일 쓰기
        
        Args:
            path: 파일 경로
            content: 파일 내용
            encoding: 파일 인코딩 (base64인 경우 바이너리 모드로 쓰기)
            overwrite: 기존 파일 덮어쓰기 여부
            
        Returns:
            작업 결과
        """
        try:
            normalized_path = self._normalize_path(path)
            
            # 디렉토리 존재 확인 및 생성
            directory = os.path.dirname(normalized_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # 기존 파일 존재 확인
            if os.path.exists(normalized_path) and not overwrite:
                return {
                    "success": False,
                    "error": f"File already exists and overwrite is False: {path}"
                }
            
            if encoding == "base64":
                # 바이너리 파일
                binary_data = base64.b64decode(content)
                with open(normalized_path, 'wb') as f:
                    f.write(binary_data)
            else:
                # 텍스트 파일
                with open(normalized_path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            return {
                "success": True,
                "path": path,
                "size": os.path.getsize(normalized_path)
            }
                
        except Exception as e:
            logger.error(f"Error writing file {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_directory(self, path: str = "./") -> Dict[str, Any]:
        """
        디렉토리 목록 조회
        
        Args:
            path: 디렉토리 경로
            
        Returns:
            디렉토리 내용 목록
        """
        try:
            normalized_path = self._normalize_path(path)
            
            if not os.path.exists(normalized_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {path}"
                }
            
            if not os.path.isdir(normalized_path):
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}"
                }
            
            items = []
            for item in os.listdir(normalized_path):
                item_path = os.path.join(normalized_path, item)
                
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                    "modified": os.path.getmtime(item_path)
                })
            
            return {
                "success": True,
                "path": path,
                "items": items
            }
                
        except Exception as e:
            logger.error(f"Error listing directory {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        디렉토리 생성
        
        Args:
            path: 생성할 디렉토리 경로
            
        Returns:
            작업 결과
        """
        try:
            normalized_path = self._normalize_path(path)
            
            if os.path.exists(normalized_path):
                if os.path.isdir(normalized_path):
                    return {
                        "success": True,
                        "path": path,
                        "message": "Directory already exists"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Path exists but is not a directory: {path}"
                    }
            
            os.makedirs(normalized_path)
            
            return {
                "success": True,
                "path": path,
                "message": "Directory created successfully"
            }
                
        except Exception as e:
            logger.error(f"Error creating directory {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 삭제
        
        Args:
            path: 삭제할 경로
            recursive: 디렉토리인 경우 재귀적 삭제 여부
            
        Returns:
            작업 결과
        """
        try:
            normalized_path = self._normalize_path(path)
            
            if not os.path.exists(normalized_path):
                return {
                    "success": False,
                    "error": f"Path not found: {path}"
                }
            
            if os.path.isdir(normalized_path):
                if recursive:
                    shutil.rmtree(normalized_path)
                else:
                    if len(os.listdir(normalized_path)) > 0:
                        return {
                            "success": False,
                            "error": f"Directory is not empty and recursive is False: {path}"
                        }
                    os.rmdir(normalized_path)
            else:
                os.remove(normalized_path)
            
            return {
                "success": True,
                "path": path,
                "message": "Successfully deleted"
            }
                
        except Exception as e:
            logger.error(f"Error deleting {path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def move(self, source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 이동
        
        Args:
            source: 원본 경로
            destination: 대상 경로
            overwrite: 대상이 존재할 경우 덮어쓰기 여부
            
        Returns:
            작업 결과
        """
        try:
            normalized_source = self._normalize_path(source)
            normalized_destination = self._normalize_path(destination)
            
            if not os.path.exists(normalized_source):
                return {
                    "success": False,
                    "error": f"Source path not found: {source}"
                }
            
            if os.path.exists(normalized_destination) and not overwrite:
                return {
                    "success": False,
                    "error": f"Destination already exists and overwrite is False: {destination}"
                }
            
            # 대상 디렉토리 생성
            dest_dir = os.path.dirname(normalized_destination)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            # 이동 또는 이름 변경
            shutil.move(normalized_source, normalized_destination)
            
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": "Successfully moved"
            }
                
        except Exception as e:
            logger.error(f"Error moving from {source} to {destination}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
