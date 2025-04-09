"""
모델 디렉토리 관리 모듈

이 모듈은 모델별 디렉토리를 생성하고 관리합니다.
"""

import os
import shutil
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


logger = logging.getLogger(__name__)


class ModelDirectoryManager:
    """모델 디렉토리를 관리하는 클래스"""
    
    def __init__(self, base_models_dir: str = "models"):
        """
        초기화 함수
        
        Args:
            base_models_dir: 모델이 저장될 기본 디렉토리 (기본값: "models")
        """
        self.base_models_dir = base_models_dir
        os.makedirs(base_models_dir, exist_ok=True)
    
    def create_model_directory(self, model_name: str) -> str:
        """
        모델 디렉토리 생성
        
        Args:
            model_name: 모델 이름
            
        Returns:
            str: 생성된 모델 디렉토리 경로
        """
        # 모델 이름에서 유효하지 않은 문자 제거
        safe_model_name = "".join(c for c in model_name if c.isalnum() or c in ['-', '_']).strip()
        if not safe_model_name:
            safe_model_name = f"model_{int(time.time())}"
        
        model_dir = os.path.join(self.base_models_dir, safe_model_name)
        
        # 이미 존재하는 경우 타임스탬프 추가
        if os.path.exists(model_dir):
            timestamp = int(time.time())
            model_dir = os.path.join(self.base_models_dir, f"{safe_model_name}_{timestamp}")
        
        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"Created model directory: {model_dir}")
        
        # 서브 디렉토리 생성
        subdirs = ['weights', 'config', 'scripts', 'data']
        for subdir in subdirs:
            os.makedirs(os.path.join(model_dir, subdir), exist_ok=True)
        
        return model_dir
    
    def save_model_metadata(self, model_dir: str, metadata: Dict[str, Any]) -> bool:
        """
        모델 메타데이터 저장
        
        Args:
            model_dir: 모델 디렉토리 경로
            metadata: 저장할 메타데이터
            
        Returns:
            bool: 성공 여부
        """
        try:
            config_dir = os.path.join(model_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            metadata_path = os.path.join(config_dir, "metadata.json")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved model metadata to {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model metadata: {str(e)}")
            return False
    
    def copy_configuration_files(self, source_dir: str, model_dir: str, file_patterns: List[str] = None) -> List[str]:
        """
        설정 파일 복사
        
        Args:
            source_dir: 소스 디렉토리
            model_dir: 대상 모델 디렉토리
            file_patterns: 복사할 파일 패턴 목록 (기본값: None - 모든 설정 파일)
            
        Returns:
            List[str]: 복사된 파일 경로 목록
        """
        if file_patterns is None:
            file_patterns = ["*.yaml", "*.yml", "*.json", "*.ini", "*.cfg", "config*"]
        
        config_dir = os.path.join(model_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        copied_files = []
        
        try:
            # 파일 패턴에 맞는 파일 복사
            for pattern in file_patterns:
                source_path = Path(source_dir)
                for file_path in source_path.glob(f"**/{pattern}"):
                    if '.git' in file_path.parts or '__pycache__' in file_path.parts:
                        continue
                    
                    # 상대 경로 유지하면서 복사
                    rel_path = file_path.relative_to(source_path)
                    dest_path = os.path.join(config_dir, str(rel_path))
                    
                    # 대상 디렉토리 생성
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # 파일 복사
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(str(rel_path))
                    logger.info(f"Copied {file_path} to {dest_path}")
            
            return copied_files
        except Exception as e:
            logger.error(f"Error copying configuration files: {str(e)}")
            return copied_files
    
    def copy_launch_scripts(self, source_dir: str, model_dir: str, script_paths: List[str]) -> List[str]:
        """
        실행 스크립트 복사
        
        Args:
            source_dir: 소스 디렉토리
            model_dir: 대상 모델 디렉토리
            script_paths: 복사할 스크립트 경로 목록
            
        Returns:
            List[str]: 복사된 스크립트 경로 목록
        """
        scripts_dir = os.path.join(model_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        copied_scripts = []
        
        try:
            for script_path in script_paths:
                full_source_path = os.path.join(source_dir, script_path)
                
                if not os.path.exists(full_source_path):
                    logger.warning(f"Script not found: {full_source_path}")
                    continue
                
                # 대상 경로 설정
                script_name = os.path.basename(script_path)
                dest_path = os.path.join(scripts_dir, script_name)
                
                # 파일 복사
                shutil.copy2(full_source_path, dest_path)
                copied_scripts.append(script_name)
                logger.info(f"Copied launch script {full_source_path} to {dest_path}")
            
            return copied_scripts
        except Exception as e:
            logger.error(f"Error copying launch scripts: {str(e)}")
            return copied_scripts
    
    def list_model_directories(self) -> List[Dict[str, Any]]:
        """
        모델 디렉토리 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 모델 정보 목록
        """
        models_info = []
        
        try:
            for item in os.listdir(self.base_models_dir):
                model_dir = os.path.join(self.base_models_dir, item)
                
                if not os.path.isdir(model_dir):
                    continue
                
                # 메타데이터 파일 확인
                metadata_path = os.path.join(model_dir, "config", "metadata.json")
                metadata = {}
                
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                model_info = {
                    "name": item,
                    "path": model_dir,
                    "metadata": metadata,
                    "created": os.path.getctime(model_dir)
                }
                
                models_info.append(model_info)
            
            # 생성 날짜 기준으로 정렬
            models_info.sort(key=lambda x: x["created"], reverse=True)
            
            return models_info
        except Exception as e:
            logger.error(f"Error listing model directories: {str(e)}")
            return []
    
    def get_model_directory(self, model_name: str) -> Optional[str]:
        """
        모델 디렉토리 경로 조회
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Optional[str]: 모델 디렉토리 경로 (없는 경우 None)
        """
        model_dir = os.path.join(self.base_models_dir, model_name)
        
        if os.path.exists(model_dir) and os.path.isdir(model_dir):
            return model_dir
        
        return None
