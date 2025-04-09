"""
환경 설정 관리 모듈

이 모듈은 모델별 가상 환경을 생성하고 필요한 의존성을 설치합니다.
"""

import os
import subprocess
import platform
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union


logger = logging.getLogger(__name__)


class EnvironmentManager:
    """모델 실행 환경을 관리하는 클래스"""
    
    def __init__(self, model_name: str, model_path: str):
        """
        초기화 함수
        
        Args:
            model_name: 모델 이름
            model_path: 모델 디렉토리 경로
        """
        self.model_name = model_name
        self.model_path = model_path
        self.env_name = f"model_{model_name}"
        self.is_windows = platform.system() == "Windows"
        
    def create_venv(self, python_version: str = "3.8") -> bool:
        """
        가상 환경 생성
        
        Args:
            python_version: 파이썬 버전 (기본값: 3.8)
            
        Returns:
            bool: 성공 여부
        """
        env_path = os.path.join(self.model_path, "venv")
        
        try:
            logger.info(f"Creating virtual environment for {self.model_name} at {env_path}")
            
            # 이미 존재하는 경우 스킵
            if os.path.exists(env_path):
                logger.info(f"Virtual environment already exists at {env_path}")
                return True
            
            # venv 생성
            cmd = [sys.executable, "-m", "venv", env_path]
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info(f"Virtual environment created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating virtual environment: {e.stdout} {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating virtual environment: {str(e)}")
            return False
    
    def install_requirements(self, requirements_file: Optional[str] = None, packages: Optional[List[str]] = None) -> bool:
        """
        의존성 패키지 설치
        
        Args:
            requirements_file: requirements.txt 파일 경로 (기본값: None)
            packages: 설치할 패키지 목록 (기본값: None)
            
        Returns:
            bool: 성공 여부
        """
        if not requirements_file and not packages:
            logger.warning("No requirements file or packages specified")
            return True
        
        env_path = os.path.join(self.model_path, "venv")
        
        if not os.path.exists(env_path):
            logger.error(f"Virtual environment not found at {env_path}")
            return False
        
        try:
            logger.info(f"Installing requirements for {self.model_name}")
            
            # Windows와 다른 OS에 따라 pip 경로 설정
            if self.is_windows:
                pip_path = os.path.join(env_path, "Scripts", "pip")
            else:
                pip_path = os.path.join(env_path, "bin", "pip")
            
            # requirements.txt 파일이 있는 경우
            if requirements_file and os.path.exists(requirements_file):
                cmd = [pip_path, "install", "-r", requirements_file]
                logger.info(f"Running: {' '.join(cmd)}")
                proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Requirements from {requirements_file} installed successfully")
            
            # 개별 패키지 목록이 있는 경우
            if packages:
                cmd = [pip_path, "install"] + packages
                logger.info(f"Running: {' '.join(cmd)}")
                proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Packages {', '.join(packages)} installed successfully")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing requirements: {e.stdout} {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing requirements: {str(e)}")
            return False
    
    def create_activation_script(self) -> bool:
        """
        가상 환경 활성화 스크립트 생성
        
        Returns:
            bool: 성공 여부
        """
        env_path = os.path.join(self.model_path, "venv")
        
        if not os.path.exists(env_path):
            logger.error(f"Virtual environment not found at {env_path}")
            return False
        
        try:
            scripts_dir = os.path.join(self.model_path, "scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            
            # Windows용 배치 파일
            if self.is_windows:
                bat_path = os.path.join(scripts_dir, "activate_env.bat")
                with open(bat_path, 'w') as f:
                    f.write(f'@echo off\n')
                    f.write(f'call "{os.path.join(env_path, "Scripts", "activate.bat")}"\n')
                    f.write('echo Environment activated. You can now run your model scripts.\n')
                
                logger.info(f"Created Windows activation script at {bat_path}")
            
            # Linux/Mac용 쉘 스크립트
            sh_path = os.path.join(scripts_dir, "activate_env.sh")
            with open(sh_path, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write(f'source "{os.path.join(env_path, "bin", "activate")}"\n')
                f.write('echo "Environment activated. You can now run your model scripts."\n')
            
            # Linux/Mac에서는 실행 권한 부여
            if not self.is_windows:
                os.chmod(sh_path, 0o755)
            
            logger.info(f"Created shell activation script at {sh_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating activation scripts: {str(e)}")
            return False
    
    def setup_environment(self, requirements_file: Optional[str] = None, packages: Optional[List[str]] = None) -> bool:
        """
        환경 설정 전체 과정 실행
        
        Args:
            requirements_file: requirements.txt 파일 경로 (기본값: None)
            packages: 설치할 패키지 목록 (기본값: None)
            
        Returns:
            bool: 성공 여부
        """
        # 가상 환경 생성
        if not self.create_venv():
            return False
        
        # 의존성 설치
        if not self.install_requirements(requirements_file, packages):
            return False
        
        # 활성화 스크립트 생성
        if not self.create_activation_script():
            return False
        
        return True
