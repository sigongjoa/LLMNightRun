"""
MCP 연동 모듈

이 모듈은 설치된 모델을 MCP 서버에 푸시하는 기능을 제공합니다.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPConnector:
    """MCP 서버와 연동하는 클래스"""
    
    def __init__(self):
        """
        초기화 함수
        """
        logger.info("MCP Connector 초기화")
    
    def upload_model(self, model_dir: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        모델을 MCP 서버에 업로드
        
        Args:
            model_dir: 모델 디렉토리 경로
            metadata: 모델 메타데이터
            
        Returns:
            Dict[str, Any]: 업로드 결과 정보
        """
        model_name = metadata.get("name", os.path.basename(model_dir))
        
        logger.info(f"모델 {model_name} MCP 서버 업로드 시작")
        
        result = {
            "status": "success",
            "model_name": model_name,
            "upload_time": int(time.time()),
            "message": f"모델 {model_name}이(가) MCP 서버에 업로드되었습니다."
        }
        
        try:
            # MCP 서버에 메타데이터 등록
            self._register_metadata(model_name, metadata)
            
            # 모델 가중치 파일 업로드
            weights_dir = os.path.join(model_dir, "weights")
            if os.path.exists(weights_dir):
                weight_files = self._upload_weights(model_name, weights_dir)
                result["weight_files"] = weight_files
            
            # 설정 파일 업로드
            config_dir = os.path.join(model_dir, "config")
            if os.path.exists(config_dir):
                config_files = self._upload_configs(model_name, config_dir)
                result["config_files"] = config_files
            
            # 실행 스크립트 업로드
            scripts_dir = os.path.join(model_dir, "scripts")
            if os.path.exists(scripts_dir):
                script_files = self._upload_scripts(model_name, scripts_dir)
                result["script_files"] = script_files
            
            logger.info(f"모델 {model_name} MCP 서버 업로드 완료")
            
            return result
            
        except Exception as e:
            logger.error(f"모델 {model_name} MCP 서버 업로드 실패: {str(e)}")
            
            result["status"] = "failed"
            result["error"] = str(e)
            
            return result
    
    def _register_metadata(self, model_name: str, metadata: Dict[str, Any]) -> bool:
        """
        모델 메타데이터를 MCP 서버에 등록
        
        Args:
            model_name: 모델 이름
            metadata: 모델 메타데이터
            
        Returns:
            bool: 성공 여부
        """
        logger.info(f"모델 {model_name} 메타데이터 등록")
        
        # MCP 서버에 메타데이터 등록 로직 구현
        # 실제 구현 시 MCP API 호출 필요
        
        return True
    
    def _upload_weights(self, model_name: str, weights_dir: str) -> List[str]:
        """
        모델 가중치 파일을 MCP 서버에 업로드
        
        Args:
            model_name: 모델 이름
            weights_dir: 가중치 파일 디렉토리 경로
            
        Returns:
            List[str]: 업로드된 파일 목록
        """
        logger.info(f"모델 {model_name} 가중치 파일 업로드")
        
        uploaded_files = []
        
        # 가중치 디렉토리의 모든 파일 탐색
        for root, _, files in os.walk(weights_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, weights_dir)
                
                # MCP 서버에 파일 업로드 로직 구현
                # 실제 구현 시 MCP API 호출 필요
                
                uploaded_files.append(rel_path)
                logger.info(f"가중치 파일 업로드: {rel_path}")
        
        return uploaded_files
    
    def _upload_configs(self, model_name: str, config_dir: str) -> List[str]:
        """
        설정 파일을 MCP 서버에 업로드
        
        Args:
            model_name: 모델 이름
            config_dir: 설정 파일 디렉토리 경로
            
        Returns:
            List[str]: 업로드된 파일 목록
        """
        logger.info(f"모델 {model_name} 설정 파일 업로드")
        
        uploaded_files = []
        
        # 설정 디렉토리의 모든 파일 탐색
        for root, _, files in os.walk(config_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, config_dir)
                
                # MCP 서버에 파일 업로드 로직 구현
                # 실제 구현 시 MCP API 호출 필요
                
                uploaded_files.append(rel_path)
                logger.info(f"설정 파일 업로드: {rel_path}")
        
        return uploaded_files
    
    def _upload_scripts(self, model_name: str, scripts_dir: str) -> List[str]:
        """
        실행 스크립트를 MCP 서버에 업로드
        
        Args:
            model_name: 모델 이름
            scripts_dir: 스크립트 디렉토리 경로
            
        Returns:
            List[str]: 업로드된 파일 목록
        """
        logger.info(f"모델 {model_name} 실행 스크립트 업로드")
        
        uploaded_files = []
        
        # 스크립트 디렉토리의 모든 파일 탐색
        for root, _, files in os.walk(scripts_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, scripts_dir)
                
                # MCP 서버에 파일 업로드 로직 구현
                # 실제 구현 시 MCP API 호출 필요
                
                uploaded_files.append(rel_path)
                logger.info(f"스크립트 파일 업로드: {rel_path}")
        
        return uploaded_files
    
    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """
        MCP 서버에 업로드된 모델 상태 조회
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Dict[str, Any]: 모델 상태 정보
        """
        logger.info(f"모델 {model_name} 상태 조회")
        
        # MCP 서버에서 모델 상태 조회 로직 구현
        # 실제 구현 시 MCP API 호출 필요
        
        return {
            "model_name": model_name,
            "status": "available",
            "upload_time": int(time.time()) - 3600,  # 예시: 1시간 전
            "size": 1024 * 1024 * 100  # 예시: 100MB
        }
    
    def update_model(self, model_name: str, model_dir: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 서버에 업로드된 모델 업데이트
        
        Args:
            model_name: 모델 이름
            model_dir: 모델 디렉토리 경로
            metadata: 모델 메타데이터
            
        Returns:
            Dict[str, Any]: 업데이트 결과 정보
        """
        logger.info(f"모델 {model_name} 업데이트")
        
        # 기존 모델 상태 확인
        status = self.get_model_status(model_name)
        
        if status.get("status") != "available":
            return {
                "status": "failed",
                "error": f"모델 {model_name}을(를) 찾을 수 없습니다."
            }
        
        # 모델 업데이트 로직은 업로드와 유사하게 구현
        result = self.upload_model(model_dir, metadata)
        
        if result["status"] == "success":
            result["message"] = f"모델 {model_name}이(가) 업데이트되었습니다."
        
        return result
