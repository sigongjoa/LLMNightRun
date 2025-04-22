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
import re

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
                - detect_gpu (bool): GPU 자동 감지 여부 (기본값: True)
                - env_prefix (str): 환경 이름 접두사 (기본값: 'ai_')
        """
        self.venv_dir = config.get("venv_dir", "venv")
        self.use_conda = config.get("use_conda", False)
        self.cuda_version = config.get("cuda_version")
        self.python_version = config.get("python_version", "3.8")
        self.force_reinstall = config.get("force_reinstall", False)
        self.detect_gpu = config.get("detect_gpu", True)
        self.env_prefix = config.get("env_prefix", "ai_")
        
        # 시스템 정보 로깅 및 자동 감지
        self._log_system_info()
        
        # GPU가 있는 경우 CUDA 버전 자동 감지
        if self.detect_gpu and not self.cuda_version:
            self.cuda_version = self._detect_cuda_version()
    
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
    
    def _detect_cuda_version(self):
        """
        시스템의 CUDA 버전을 자동으로 감지합니다.
        
        Returns:
            str 또는 None: 감지된 CUDA 버전 또는 감지 실패 시 None
        """
        try:
            if platform.system() == 'Windows':
                nvcc_proc = subprocess.run(
                    ["nvcc", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if nvcc_proc.returncode == 0:
                    # "release X.Y" 패턴에서 버전 추출
                    match = re.search(r"release (\d+\.\d+)", nvcc_proc.stdout)
                    if match:
                        return match.group(1)
            else:
                # Linux 또는 macOS에서는 nvidia-smi를 사용하여 CUDA 버전 확인
                # 참고: nvidia-smi는 드라이버 버전을 보여주며, 이것이 지원하는 최대 CUDA 버전과 다를 수 있음
                nvidia_smi_proc = subprocess.run(
                    ["nvidia-smi"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if nvidia_smi_proc.returncode == 0:
                    # "CUDA Version: X.Y" 패턴에서 버전 추출
                    match = re.search(r"CUDA Version: (\d+\.\d+)", nvidia_smi_proc.stdout)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return None
    
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
        print("\n[DEBUG] setup_environment 호출됨: {}".format(repo_path))
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"레포지토리 경로를 찾을 수 없습니다: {repo_path}")
        
        logger.info(f"환경 설정 시작: {repo_path}")
        
        # 레포지토리 분석하여 프레임워크 감지
        framework = self._detect_framework(repo_path)
        if framework:
            logger.info(f"감지된 프레임워크: {framework}")
        
        # 환경 유형 결정
        env_type = self._determine_env_type(repo_path)
        logger.info(f"환경 유형: {env_type}")
        
        # 레포지토리 요구사항 파일 찾기
        req_file = self._find_requirements_file(repo_path)
        logger.info(f"요구사항 파일: {req_file}")
        
        # 환경 설정 방법 결정
        if env_type == "conda" or self.use_conda:
            env_path = self._setup_conda_env(repo_path, req_file, framework)
        else:
            env_path = self._setup_venv(repo_path, req_file, framework)
        
        logger.info(f"환경 설정 완료: {env_path}")
        return env_path
    
    def _detect_framework(self, repo_path):
        """
        레포지토리에서 사용하는 프레임워크를 감지합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            str 또는 None: 감지된 프레임워크 또는 감지 실패 시 None
        """
        # 주요 프레임워크 키워드
        frameworks = {
            "pytorch": ["torch", "pytorch"],
            "tensorflow": ["tensorflow", "tf"],
            "keras": ["keras"],
            "scikit-learn": ["sklearn", "scikit-learn"],
            "huggingface": ["transformers", "huggingface"],
            "jax": ["jax", "flax"]
        }
        
        # 요구사항 파일에서 프레임워크 감지
        req_file = self._find_requirements_file(repo_path)
        if req_file and os.path.exists(req_file):
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                    for framework, keywords in frameworks.items():
                        if any(keyword in content for keyword in keywords):
                            return framework
            except:
                pass
        
        # README 파일에서 프레임워크 감지
        readme_files = ["README.md", "README.rst", "README", "README.txt"]
        for filename in readme_files:
            readme_path = os.path.join(repo_path, filename)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                        for framework, keywords in frameworks.items():
                            if any(keyword in content for keyword in keywords):
                                return framework
                except:
                    pass
        
        # Python 파일에서 프레임워크 감지
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                            for framework, keywords in frameworks.items():
                                for keyword in keywords:
                                    # import 문에서 키워드 검색
                                    if re.search(rf"(import|from)\s+{keyword}", content):
                                        return framework
                    except:
                        pass
        
        return None
    
    def _determine_env_type(self, repo_path):
        """
        레포지토리에 맞는 환경 유형을 결정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            str: 환경 유형 ("conda" 또는 "venv" 또는 "poetry")
        """
        # Conda 환경 파일 확인
        conda_files = [
            os.path.join(repo_path, "environment.yml"),
            os.path.join(repo_path, "environment.yaml"),
            os.path.join(repo_path, "conda_env.yml"),
            os.path.join(repo_path, "conda-env.yml")
        ]
        
        for file_path in conda_files:
            if os.path.exists(file_path):
                return "conda"
        
        # Poetry 확인
        if os.path.exists(os.path.join(repo_path, "pyproject.toml")):
            with open(os.path.join(repo_path, "pyproject.toml"), 'r', encoding='utf-8') as f:
                content = f.read()
                if "tool.poetry" in content:
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
        # 일반적인 요구사항 파일 이름 및 경로
        req_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/main.txt",
            "requirements/base.txt",
            "requirements/core.txt",
            "requirements/prod.txt",
            "setup.py"
        ]
        
        # 직접 검색
        for file_name in req_files:
            file_path = os.path.join(repo_path, file_name)
            if os.path.exists(file_path):
                return file_path
        
        # 하위 디렉토리 검색
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file == "requirements.txt":
                    return os.path.join(root, file)
        
        return None
    
    def _find_conda_env_file(self, repo_path):
        """
        레포지토리에서 Conda 환경 파일을 찾습니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            str 또는 None: 환경 파일 경로 또는 None (파일을 찾지 못한 경우)
        """
        # Conda 환경 파일 확인
        conda_files = [
            os.path.join(repo_path, "environment.yml"),
            os.path.join(repo_path, "environment.yaml"),
            os.path.join(repo_path, "conda_env.yml"),
            os.path.join(repo_path, "conda-env.yml")
        ]
        
        for file_path in conda_files:
            if os.path.exists(file_path):
                return file_path
        
        # 하위 디렉토리 검색
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.lower() in ["environment.yml", "environment.yaml", "conda_env.yml"]:
                    return os.path.join(root, file)
        
        return None
    
    def _create_conda_env_from_file(self, env_name, env_file):
        """
        환경 파일을 사용하여 Conda 환경을 생성합니다.
        
        Args:
            env_name (str): 환경 이름
            env_file (str): 환경 파일 경로
            
        Raises:
            RuntimeError: 환경 생성 중 오류가 발생한 경우
        """
        try:
            subprocess.run(
                ["conda", "env", "create", "--file", env_file, "--name", env_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Conda 환경 생성 실패: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _create_conda_env_manually(self, env_name, req_file, framework=None):
        """
        수동으로 Conda 환경을 생성합니다.
        
        Args:
            env_name (str): 환경 이름
            req_file (str): 요구사항 파일 경로
            framework (str, optional): 감지된 프레임워크
            
        Raises:
            RuntimeError: 환경 생성 중 오류가 발생한 경우
        """
        try:
            # Python 버전 설정
            python_spec = f"python={self.python_version}"
            
            # CUDA 설정
            cuda_spec = f"cudatoolkit={self.cuda_version}" if self.cuda_version else ""
            
            # 프레임워크 관련 패키지
            framework_packages = []
            if framework:
                if framework == "pytorch" and self.cuda_version:
                    framework_packages.append("pytorch")
                    framework_packages.append("torchvision")
                    framework_packages.append("torchaudio")
                    framework_packages.append(f"cudatoolkit={self.cuda_version}")
                elif framework == "tensorflow" and self.cuda_version:
                    framework_packages.append("tensorflow-gpu")
                elif framework == "tensorflow":
                    framework_packages.append("tensorflow")
                elif framework == "scikit-learn":
                    framework_packages.append("scikit-learn")
                elif framework == "huggingface":
                    framework_packages.append("transformers")
                    framework_packages.append("datasets")
                elif framework == "jax":
                    framework_packages.append("jax")
                    framework_packages.append("flax")
            
            # 환경 생성 명령
            cmd = ["conda", "create", "--name", env_name, python_spec, "--yes"]
            if cuda_spec and cuda_spec not in framework_packages:
                cmd.append(cuda_spec)
            for pkg in framework_packages:
                cmd.append(pkg)
            
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # 요구사항 설치 (필요한 경우)
            if req_file:
                logger.info(f"요구사항 파일 설치 중: {req_file}")
                
                # 플랫폼에 따른 Conda 활성화 명령
                if platform.system() == 'Windows':
                    # Windows에서는 환경 활성화 후 pip 설치를 위한 별도 명령 필요
                    cmd = f"conda activate {env_name} && pip install -r \"{req_file}\""
                    
                    # conda activate는 직접 실행할 수 없으므로 cmd /c를 사용
                    subprocess.run(
                        ["cmd", "/c", cmd],
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
        except subprocess.CalledProcessError as e:
            error_msg = f"Conda 환경 수동 생성 실패: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _setup_conda_env(self, repo_path, req_file, framework=None):
        """
        Conda 환경을 설정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            req_file (str): 요구사항 파일 경로
            framework (str, optional): 감지된 프레임워크
            
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
        
        # 환경 이름 생성 (레포지토리 이름 기반)
        repo_name = os.path.basename(repo_path)
        env_name = f"{self.env_prefix}{repo_name}"
        
        # 이름 길이 제한
        if len(env_name) > 50:
            import hashlib
            # 해시 생성
            hash_obj = hashlib.md5(repo_name.encode())
            hash_str = hash_obj.hexdigest()[:8]
            env_name = f"{self.env_prefix}{hash_str}"
        
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
        env_file = self._find_conda_env_file(repo_path)
        
        try:
            if env_file:
                # 환경 파일이 있는 경우 해당 파일로 환경 생성
                logger.info(f"Conda 환경 파일 사용: {env_file}")
                self._create_conda_env_from_file(env_name, env_file)
            else:
                # 환경 파일이 없는 경우 수동으로 환경 생성
                logger.info(f"Conda 환경 수동 생성: {env_name}")
                self._create_conda_env_manually(env_name, req_file, framework)
            
            # 환경 정보 저장
            env_info = {
                "type": "conda",
                "name": env_name,
                "python_version": self.python_version,
                "cuda_version": self.cuda_version,
                "framework": framework,
                "requirements_file": req_file,
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            
            env_info_path = os.path.join(repo_path, "env_info.json")
            with open(env_info_path, 'w', encoding='utf-8') as f:
                json.dump(env_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Conda 환경 설정 완료: {env_name}")
            return env_name
            
        except Exception as e:
            error_msg = f"Conda 환경 설정 실패: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _setup_venv(self, repo_path, req_file, framework=None):
        """
        Python 가상 환경(venv)을 설정합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            req_file (str): 요구사항 파일 경로
            framework (str, optional): 감지된 프레임워크
            
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
                error_msg = f"가상 환경 생성 실패: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # pip 및 python 경로
        if platform.system() == 'Windows':
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            python_path = os.path.join(venv_path, "bin", "python")
        
        # 표준화된 경로 확인 (Windows에서 / 대신 \ 사용)
        pip_path = os.path.normpath(pip_path)
        python_path = os.path.normpath(python_path)
        
        # 가상 환경 초기 설치 작업
        try:
            # pip 업그레이드 (선택적) - 실패해도 계속 진행
            logger.info("pip 업그레이드 중")
            try:
                subprocess.run(
                    [pip_path, "install", "--upgrade", "pip"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False  # 실패해도 중단하지 않음
                )
            except Exception as e:
                logger.warning(f"pip 업그레이드 실패 (무시하고 계속 진행): {e}")
            
            # 프레임워크 패키지 설치
            if framework:
                logger.info(f"프레임워크 패키지 설치 중: {framework}")
                if framework == "pytorch":
                    # PyTorch 설치 명령은 CUDA 버전에 따라 다름
                    if self.cuda_version:
                        torch_install = f"torch torchvision torchaudio"
                    else:
                        torch_install = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                    
                    subprocess.run(
                        [pip_path, "install", torch_install],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        check=False  # PyTorch 설치 실패해도 계속 진행
                    )
                elif framework == "tensorflow":
                    subprocess.run(
                        [pip_path, "install", "tensorflow"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False  # TensorFlow 설치 실패해도 계속 진행
                    )
                elif framework == "scikit-learn":
                    subprocess.run(
                        [pip_path, "install", "scikit-learn", "numpy", "pandas", "matplotlib"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False  # 설치 실패해도 계속 진행
                    )
                elif framework == "huggingface":
                    subprocess.run(
                        [pip_path, "install", "transformers", "datasets", "tokenizers"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False  # 설치 실패해도 계속 진행
                    )
                elif framework == "jax":
                    # JAX 설치는 CPU/GPU에 따라 다름
                    if self.cuda_version:
                        jax_install = "jax[cuda] -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html flax"
                    else:
                        jax_install = "jax flax"
                    
                    subprocess.run(
                        [pip_path, "install", jax_install],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        check=False  # 설치 실패해도 계속 진행
                    )
            
            # 요구사항 설치 (파일이 있는 경우)
            if req_file:
                logger.info(f"요구사항 파일 설치 중: {req_file}")
                subprocess.run(
                    [pip_path, "install", "-r", req_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False  # 요구사항 설치 실패해도 계속 진행
                )
            
            # setup.py가 있는 경우 설치
            setup_py = os.path.join(repo_path, "setup.py")
            if os.path.exists(setup_py):
                logger.info("setup.py 설치 중")
                subprocess.run(
                    [pip_path, "install", "-e", repo_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False  # setup.py 설치 실패해도 계속 진행
                )
            
            # 환경 정보 저장
            env_info = {
                "type": "venv",
                "path": venv_path,
                "python_path": python_path,
                "pip_path": pip_path,
                "framework": framework,
                "requirements_file": req_file,
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            
            env_info_path = os.path.join(repo_path, "env_info.json")
            with open(env_info_path, 'w', encoding='utf-8') as f:
                json.dump(env_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"가상 환경 설정 완료: {venv_path}")
            return venv_path
            
        except Exception as e:
            error_msg = f"가상 환경 설정 실패: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
