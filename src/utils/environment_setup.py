"""
환경 설정 (Environment Setup)

AI 모델 학습을 위한 환경을 설정합니다.
필요한 패키지 설치, 가상 환경 설정 등을 처리합니다.
"""

import os
import logging
import subprocess
import sys
import json
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """
    AI 모델 학습 환경을 설정하는 클래스
    """
    
    def __init__(self, config):
        """
        환경 설정 관리자를 초기화합니다.
        
        Args:
            config (dict): 환경 설정 관련 설정
                - venv_dir (str): 가상 환경 디렉토리 (기본값: 'venv')
                - use_conda (bool): Conda 사용 여부 (기본값: False)
                - cuda_version (str, optional): 사용할 CUDA 버전
                - python_version (str, optional): 사용할 Python 버전
                - force_reinstall (bool): 기존 환경 재설치 여부 (기본값: False)
        """
        self.venv_dir = config.get("venv_dir", "venv")
        self.use_conda = config.get("use_conda", False)
        self.cuda_version = config.get("cuda_version")
        self.python_version = config.get("python_version", "3.8")
        self.force_reinstall = config.get("force_reinstall", False)
        
        # 시스템 정보 로깅
        self._log_system_info()
    
    def _log_system_info(self):
        """시스템 정보를 로깅합니다."""
        logger.info(f"운영체제: {platform.system()} {platform.release()}")
        logger.info(f"Python 버전: {platform.python_version()}")
        
        # CUDA 정보 확인
        try:
            if platform.system() == 'Windows':
                nvcc_proc = subprocess.run(
                    ["nvcc", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if nvcc_proc.returncode == 0:
                    cuda_version = nvcc_proc.stdout.split("release ")[1].split(",")[0]
                    logger.info(f"CUDA 버전: {cuda_version}")
                else:
                    logger.info("CUDA가 설치되어 있지 않습니다.")
            else:
                # Linux 또는 macOS
                nvidia_smi_proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if nvidia_smi_proc.returncode == 0:
                    logger.info(f"NVIDIA 드라이버 버전: {nvidia_smi_proc.stdout.strip()}")
                else:
                    logger.info("NVIDIA 드라이버가 설치되어 있지 않습니다.")
        except:
            logger.info("CUDA/NVIDIA 정보를 가져올 수 없습니다.")
    
    def setup_environment(self, repo_path):
        """
        AI 모델 학습 환경을 설정합니다.
        
        Args:
            repo_path (str): 레포지토리 로컬 경로
            
        Returns:
            str: 설정된 환경의 경로
            
        Raises:
            FileNotFoundError: 레포지토리 경로가 존재하지 않는 경우
            RuntimeError: 환경 설정 중 오류가 발생한 경우
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"레포지토리 경로를 찾을 수 없습니다: {repo_path}")
        
        logger.info(f"환경 설정 시작: {repo_path}")
        
        # 환경 유형 결정
        env_type = self._determine_env_type(repo_path)
        logger.info(f"환경 유형: {env_type}")
        
        # 레포지토리 요구사항 파일 찾기
        req_file = self._find_requirements_file(repo_path)
        logger.info(f"요구사항 파일: {req_file}")
        
        # 환경 설정 방법 결정
        if env_type == "conda" or self.use_conda:
            env_path = self._setup_conda_env(repo_path, req_file)
        else:
            env_path = self._setup_venv(repo_path, req_file)
        
        logger.info(f"환경 설정 완료: {env_path}")
        return env_path
    
    def _determine_env_type(self, repo_path):
        """
        레포지토리에 맞는 환경 유형을 결정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            str: 환경 유형 ("conda" 또는 "venv")
        """
        # Conda 환경 파일 확인
        conda_files = [
            os.path.join(repo_path, "environment.yml"),
            os.path.join(repo_path, "environment.yaml"),
            os.path.join(repo_path, "conda_env.yml")
        ]
        
        for file_path in conda_files:
            if os.path.exists(file_path):
                return "conda"
        
        # Poetry 확인
        if os.path.exists(os.path.join(repo_path, "pyproject.toml")):
            return "poetry"
        
        # 기본값: venv
        return "venv"
    
    def _find_requirements_file(self, repo_path):
        """
        레포지토리에서 요구사항 파일을 찾습니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            str 또는 None: 요구사항 파일 경로 또는 None (파일을 찾지 못한 경우)
        """
        # 일반적인 요구사항 파일 이름
        req_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/main.txt",
            "setup.py"
        ]
        
        for file_name in req_files:
            file_path = os.path.join(repo_path, file_name)
            if os.path.exists(file_path):
                return file_path
        
        # 요구사항 파일 찾기 (중첩 디렉토리 검색)
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file == "requirements.txt":
                    return os.path.join(root, file)
        
        return None
    
    def _setup_conda_env(self, repo_path, req_file):
        """
        Conda 환경을 설정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            req_file (str): 요구사항 파일 경로
            
        Returns:
            str: Conda 환경 경로
            
        Raises:
            RuntimeError: Conda 환경 설정 중 오류가 발생한 경우
        """
        try:
            # Conda 실행 가능 여부 확인
            subprocess.run(
                ["conda", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = "Conda가 시스템에 설치되어 있지 않습니다."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # 환경 이름 (레포지토리 이름 기반)
        repo_name = os.path.basename(repo_path)
        env_name = f"ai_{repo_name}"
        
        # 기존 환경이 있고 재설치 옵션이 활성화된 경우 제거
        if self.force_reinstall:
            try:
                logger.info(f"기존 Conda 환경 제거 중: {env_name}")
                subprocess.run(
                    ["conda", "env", "remove", "--name", env_name, "--yes"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            except subprocess.CalledProcessError:
                # 오류 무시 (환경이 존재하지 않을 수 있음)
                pass
        
        # 환경 파일 경로
        env_file = None
        conda_files = [
            os.path.join(repo_path, "environment.yml"),
            os.path.join(repo_path, "environment.yaml"),
            os.path.join(repo_path, "conda_env.yml")
        ]
        
        for file_path in conda_files:
            if os.path.exists(file_path):
                env_file = file_path
                break
        
        try:
            if env_file:
                # 환경 파일이 있는 경우 해당 파일로 환경 생성
                logger.info(f"Conda 환경 파일 사용: {env_file}")
                subprocess.run(
                    ["conda", "env", "create", "--file", env_file, "--name", env_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            else:
                # 환경 파일이 없는 경우 수동으로 환경 생성
                logger.info(f"Conda 환경 수동 생성: {env_name}")
                
                # Python 버전 설정
                python_spec = f"python={self.python_version}"
                
                # CUDA 설정
                cuda_spec = f"cudatoolkit={self.cuda_version}" if self.cuda_version else ""
                
                # 환경 생성
                cmd = ["conda", "create", "--name", env_name, python_spec, "--yes"]
                if cuda_spec:
                    cmd.append(cuda_spec)
                
                subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                
                # 요구사항 설치 (필요한 경우)
                if req_file:
                    logger.info(f"요구사항 파일 설치 중: {req_file}")
                    
                    # Windows 또는 다른 플랫폼에 따른 Conda 활성화 명령
                    if platform.system() == 'Windows':
                        activate_cmd = ["conda", "activate", env_name, "&&"]
                        pip_cmd = ["pip", "install", "-r", req_file]
                        full_cmd = " ".join(activate_cmd + pip_cmd)
                        
                        subprocess.run(
                            full_cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                    else:
                        # Linux 또는 macOS
                        subprocess.run(
                            ["conda", "run", "--name", env_name, "pip", "install", "-r", req_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
            
            # 환경 정보 저장
            env_info = {
                "type": "conda",
                "name": env_name,
                "python_version": self.python_version,
                "cuda_version": self.cuda_version,
                "requirements_file": req_file
            }
            
            env_info_path = os.path.join(repo_path, "env_info.json")
            with open(env_info_path, 'w', encoding='utf-8') as f:
                json.dump(env_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Conda 환경 설정 완료: {env_name}")
            return env_name
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Conda 환경 설정 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _setup_venv(self, repo_path, req_file):
        """
        Python 가상 환경(venv)을 설정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            req_file (str): 요구사항 파일 경로
            
        Returns:
            str: 가상 환경 경로
            
        Raises:
            RuntimeError: 가상 환경 설정 중 오류가 발생한 경우
        """
        # venv 디렉토리 경로
        venv_path = os.path.join(repo_path, self.venv_dir)
        
        # 기존 환경이 있고 재설치 옵션이 활성화된 경우 제거
        if os.path.exists(venv_path) and self.force_reinstall:
            logger.info(f"기존 가상 환경 제거 중: {venv_path}")
            try:
                import shutil
                shutil.rmtree(venv_path)
            except Exception as e:
                logger.warning(f"가상 환경 제거 실패: {e}")
        
        # 가상 환경이 없는 경우 생성
        if not os.path.exists(venv_path):
            try:
                logger.info(f"가상 환경 생성 중: {venv_path}")
                
                # venv 모듈로 환경 생성
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                error_msg = f"가상 환경 생성 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # pip 경로
        if platform.system() == 'Windows':
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            python_path = os.path.join(venv_path, "bin", "python")
        
        # pip 업그레이드
        try:
            logger.info("pip 업그레이드 중")
            subprocess.run(
                [pip_path, "install", "--upgrade", "pip"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"pip 업그레이드 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        
        # 요구사항 설치 (파일이 있는 경우)
        if req_file:
            try:
                logger.info(f"요구사항 파일 설치 중: {req_file}")
                subprocess.run(
                    [pip_path, "install", "-r", req_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                error_msg = f"요구사항 설치 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # setup.py가 있는 경우 설치
        setup_py = os.path.join(repo_path, "setup.py")
        if os.path.exists(setup_py):
            try:
                logger.info("setup.py 설치 중")
                subprocess.run(
                    [pip_path, "install", "-e", repo_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.warning(f"setup.py 설치 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        
        # 환경 정보 저장
        env_info = {
            "type": "venv",
            "path": venv_path,
            "python_path": python_path,
            "pip_path": pip_path,
            "requirements_file": req_file
        }
        
        env_info_path = os.path.join(repo_path, "env_info.json")
        with open(env_info_path, 'w', encoding='utf-8') as f:
            json.dump(env_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"가상 환경 설정 완료: {venv_path}")
        return venv_path
