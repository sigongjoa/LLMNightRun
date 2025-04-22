"""
AI 환경 설정 모듈

AI 모델 학습 및 배포를 위한 환경 설정 기능을 제공합니다.
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from core.logging import get_logger
from core.events import publish
from core.config import get_config

logger = get_logger("github_ai_setup.environment")

def setup_environment(repo_path: str, env_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI 환경 설정 파일 생성
    
    Args:
        repo_path: 저장소 경로
        env_config: 환경 설정 딕셔너리
    
    Returns:
        생성된 파일 정보 딕셔너리
    """
    logger.info(f"AI 환경 설정 중: {repo_path}")
    
    result = {
        "success": True,
        "files_created": [],
        "errors": []
    }
    
    # requirements.txt 생성
    if env_config.get("generate_requirements", True):
        req_path = _generate_requirements(repo_path, env_config)
        if req_path:
            result["files_created"].append(req_path)
        else:
            result["success"] = False
            result["errors"].append("requirements.txt 생성 실패")
    
    # Dockerfile 생성
    if env_config.get("generate_dockerfile", True):
        docker_path = _generate_dockerfile(repo_path, env_config)
        if docker_path:
            result["files_created"].append(docker_path)
        else:
            result["success"] = False
            result["errors"].append("Dockerfile 생성 실패")
    
    # Docker Compose 생성
    if env_config.get("generate_docker_compose", False):
        compose_path = _generate_docker_compose(repo_path, env_config)
        if compose_path:
            result["files_created"].append(compose_path)
    
    # conda 환경 파일 생성
    if env_config.get("generate_conda_env", False):
        conda_path = _generate_conda_env(repo_path, env_config)
        if conda_path:
            result["files_created"].append(conda_path)
    
    # 결과 이벤트 발행
    publish("github_ai.environment.setup", 
           repo_path=repo_path, 
           success=result["success"],
           files_created=len(result["files_created"]))
    
    return result

def check_environment(repo_path: str) -> Dict[str, Any]:
    """
    환경 설정 상태 확인
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        환경 상태 딕셔너리
    """
    # 결과 딕셔너리
    result = {
        "has_environment_config": False,
        "environment_files": [],
        "python_version": None,
        "cuda_available": False,
        "required_packages": [],
        "missing_packages": [],
        "docker_support": False,
        "conda_support": False
    }
    
    # 환경 파일 확인
    env_files = [
        "requirements.txt",
        "Pipfile",
        "pyproject.toml",
        "environment.yml",
        "environment.yaml",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml"
    ]
    
    for env_file in env_files:
        file_path = os.path.join(repo_path, env_file)
        if os.path.exists(file_path):
            result["environment_files"].append(env_file)
    
    result["has_environment_config"] = len(result["environment_files"]) > 0
    
    # requirements.txt 분석
    req_path = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        result["required_packages"].append(line)
        except Exception as e:
            logger.warning(f"requirements.txt 읽기 실패: {str(e)}")
    
    # Docker 지원 확인
    docker_path = os.path.join(repo_path, "Dockerfile")
    result["docker_support"] = os.path.exists(docker_path)
    
    # conda 지원 확인
    conda_env_path = os.path.join(repo_path, "environment.yml")
    conda_env_path2 = os.path.join(repo_path, "environment.yaml")
    result["conda_support"] = os.path.exists(conda_env_path) or os.path.exists(conda_env_path2)
    
    # 현재 Python 버전 확인
    result["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # CUDA 가용성 확인 (현재 시스템)
    try:
        import torch
        result["cuda_available"] = torch.cuda.is_available()
    except:
        try:
            import tensorflow as tf
            result["cuda_available"] = tf.test.is_gpu_available()
        except:
            result["cuda_available"] = False
    
    # 누락된 패키지 확인
    if result["required_packages"]:
        try:
            import pkg_resources
            
            for package in result["required_packages"]:
                # 버전 요구사항 제거
                pkg_name = package.split("==")[0].split(">=")[0].split("<=")[0].strip()
                
                try:
                    pkg_resources.get_distribution(pkg_name)
                except pkg_resources.DistributionNotFound:
                    result["missing_packages"].append(pkg_name)
        except ImportError:
            logger.warning("pkg_resources 패키지를 가져올 수 없음")
    
    return result

def _generate_requirements(repo_path: str, env_config: Dict[str, Any]) -> str:
    """requirements.txt 파일 생성"""
    try:
        req_path = os.path.join(repo_path, "requirements.txt")
        
        # 기존 파일 확인
        if os.path.exists(req_path):
            # 백업 생성
            backup_path = req_path + ".bak"
            shutil.copy2(req_path, backup_path)
            logger.info(f"requirements.txt 백업 생성됨: {backup_path}")
        
        # 패키지 목록 추출
        packages = env_config.get("packages", [])
        
        # 파일 생성
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write("# AI 모델 의존성 패키지\n")
            f.write("# 생성 시간: " + os.path.basename(repo_path) + "\n\n")
            
            for package in packages:
                f.write(package + "\n")
        
        logger.info(f"requirements.txt 생성됨: {req_path}")
        return req_path
    
    except Exception as e:
        logger.error(f"requirements.txt 생성 실패: {str(e)}")
        return ""

def _generate_dockerfile(repo_path: str, env_config: Dict[str, Any]) -> str:
    """Dockerfile 생성"""
    try:
        docker_path = os.path.join(repo_path, "Dockerfile")
        
        # 기존 파일 확인
        if os.path.exists(docker_path):
            # 백업 생성
            backup_path = docker_path + ".bak"
            shutil.copy2(docker_path, backup_path)
            logger.info(f"Dockerfile 백업 생성됨: {backup_path}")
        
        # 설정 추출
        python_version = env_config.get("python_version", "3.8")
        cuda_version = env_config.get("cuda_version", "11.8")
        use_cuda = env_config.get("cuda_required", False)
        
        # 베이스 이미지 선택
        if use_cuda:
            base_image = f"nvidia/cuda:{cuda_version}-cudnn8-runtime-ubuntu20.04"
        else:
            base_image = f"python:{python_version}-slim"
        
        # 파일 내용 생성
        content = f"""# AI 모델 Docker 환경
FROM {base_image}

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    wget \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# 기본 명령
CMD ["python", "app.py"]
"""
        # 파일 생성
        with open(docker_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Dockerfile 생성됨: {docker_path}")
        return docker_path
    
    except Exception as e:
        logger.error(f"Dockerfile 생성 실패: {str(e)}")
        return ""

def _generate_docker_compose(repo_path: str, env_config: Dict[str, Any]) -> str:
    """docker-compose.yml 생성"""
    try:
        compose_path = os.path.join(repo_path, "docker-compose.yml")
        
        # 기존 파일 확인
        if os.path.exists(compose_path):
            # 백업 생성
            backup_path = compose_path + ".bak"
            shutil.copy2(compose_path, backup_path)
            logger.info(f"docker-compose.yml 백업 생성됨: {backup_path}")
        
        # 추가 서비스 확인 (벡터 DB, API 서버 등)
        has_api = env_config.get("deployment", {}).get("method") == "rest_api"
        use_vector_db = env_config.get("use_vector_db", False)
        
        # 파일 내용 생성
        content = """version: '3'

services:
  app:
    build: .
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
"""
        
        # API 서비스 추가
        if has_api:
            content += """
  api:
    build: .
    command: python api.py
    volumes:
      - ./:/app
    ports:
      - "5000:5000"
    depends_on:
      - app
"""

        # 벡터 DB 추가
        if use_vector_db:
            content += """
  vector_db:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"
    volumes:
      - ./data/milvus:/var/lib/milvus
"""
        
        # 파일 생성
        with open(compose_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"docker-compose.yml 생성됨: {compose_path}")
        return compose_path
    
    except Exception as e:
        logger.error(f"docker-compose.yml 생성 실패: {str(e)}")
        return ""

def _generate_conda_env(repo_path: str, env_config: Dict[str, Any]) -> str:
    """conda 환경 파일 생성"""
    try:
        conda_path = os.path.join(repo_path, "environment.yml")
        
        # 기존 파일 확인
        if os.path.exists(conda_path):
            # 백업 생성
            backup_path = conda_path + ".bak"
            shutil.copy2(conda_path, backup_path)
            logger.info(f"environment.yml 백업 생성됨: {backup_path}")
        
        # 설정 추출
        python_version = env_config.get("python_version", "3.8")
        packages = env_config.get("packages", [])
        
        # 패키지 이름 추출 (버전 제거)
        conda_packages = []
        pip_packages = []
        
        for pkg in packages:
            pkg_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].strip()
            
            # 기본 패키지는 conda로, 나머지는 pip으로
            if pkg_name in ["numpy", "pandas", "matplotlib", "scipy", "scikit-learn"]:
                conda_packages.append(pkg)
            else:
                pip_packages.append(pkg)
        
        # 파일 내용 생성
        content = f"""name: {os.path.basename(repo_path)}_env
channels:
  - conda-forge
  - defaults
dependencies:
  - python={python_version}
"""
        
        # conda 패키지 추가
        for pkg in conda_packages:
            content += f"  - {pkg}\n"
        
        # pip 패키지 추가
        if pip_packages:
            content += "  - pip\n"
            content += "  - pip:\n"
            for pkg in pip_packages:
                content += f"    - {pkg}\n"
        
        # 파일 생성
        with open(conda_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"environment.yml 생성됨: {conda_path}")
        return conda_path
    
    except Exception as e:
        logger.error(f"environment.yml 생성 실패: {str(e)}")
        return ""
