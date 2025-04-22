"""
스크립트 실행기 모듈

전처리 스크립트를 실행하는 기능을 제공합니다.
"""

import os
import re
import logging
import importlib.util
import subprocess
import sys

logger = logging.getLogger(__name__)

class ScriptRunner:
    """
    전처리 스크립트를 실행하는 클래스
    """
    
    def __init__(self, data_dir, cache_dir):
        """
        스크립트 실행기를 초기화합니다.
        
        Args:
            data_dir (str): 데이터 디렉토리 경로
            cache_dir (str): 캐시 디렉토리 경로
        """
        self.data_dir = data_dir
        self.cache_dir = cache_dir
    
    def run_custom_script(self, script_path, env_info=None):
        """
        사용자 정의 전처리 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            env_info (dict, optional): 환경 정보
            
        Raises:
            ValueError: 스크립트가 유효하지 않은 경우
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        if not os.path.exists(script_path):
            raise ValueError(f"스크립트를 찾을 수 없습니다: {script_path}")
        
        logger.info(f"사용자 정의 전처리 스크립트 실행 중: {script_path}")
        
        try:
            if env_info and env_info.get("type") == "venv":
                # 가상 환경의 Python으로 스크립트 실행
                python_path = env_info.get("python_path")
                if python_path and os.path.exists(python_path):
                    subprocess.run(
                        [python_path, script_path, "--data-dir", self.data_dir, "--cache-dir", self.cache_dir],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    return
            
            # 스크립트 모듈로 로드하여 실행
            spec = importlib.util.spec_from_file_location("custom_preprocessing", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # preprocess 함수 실행
            if hasattr(module, "preprocess"):
                module.preprocess(data_dir=self.data_dir, cache_dir=self.cache_dir)
            else:
                logger.warning(f"스크립트에 preprocess 함수가 없습니다: {script_path}")
                
        except Exception as e:
            error_msg = f"사용자 정의 전처리 스크립트 실행 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def find_and_run_preprocessing_scripts(self, repo_path, env_info=None):
        """
        레포지토리에서 전처리 스크립트를 찾아 실행합니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            env_info (dict, optional): 환경 정보
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        # 전처리 스크립트 패턴
        script_patterns = [
            r'preprocess.*\.py$',
            r'data_prep.*\.py$',
            r'prepare_data.*\.py$'
        ]
        
        scripts_found = []
        
        # 스크립트 찾기
        for root, _, files in os.walk(repo_path):
            for file in files:
                if any(re.search(pattern, file, re.IGNORECASE) for pattern in script_patterns):
                    scripts_found.append(os.path.join(root, file))
        
        if not scripts_found:
            logger.info("레포지토리에서 전처리 스크립트를 찾을 수 없습니다.")
            return
        
        # 스크립트 실행
        for script_path in scripts_found:
            try:
                logger.info(f"레포지토리 전처리 스크립트 실행 중: {os.path.basename(script_path)}")
                
                # 실행 방법 선택
                if env_info:
                    self._run_script_in_env(script_path, env_info)
                else:
                    self._run_script_directly(script_path)
                    
            except Exception as e:
                logger.warning(f"스크립트 실행 실패: {script_path} - {e}")
    
    def _run_script_in_env(self, script_path, env_info):
        """
        환경 내에서 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            env_info (dict): 환경 정보
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        if env_info.get("type") == "venv":
            # 가상 환경에서 실행
            python_path = env_info.get("python_path")
            if python_path and os.path.exists(python_path):
                try:
                    subprocess.run(
                        [
                            python_path, script_path,
                            "--data-dir", self.data_dir,
                            "--cache-dir", self.cache_dir
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    error_msg = f"가상 환경에서 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        elif env_info.get("type") == "conda":
            # Conda 환경에서 실행
            env_name = env_info.get("name")
            if env_name:
                try:
                    # 플랫폼에 따른 Conda 실행 방법
                    if sys.platform == 'win32':
                        cmd = f"conda run -n {env_name} python \"{script_path}\" --data-dir \"{self.data_dir}\" --cache-dir \"{self.cache_dir}\""
                        subprocess.run(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                    else:
                        subprocess.run(
                            [
                                "conda", "run", "-n", env_name,
                                "python", script_path,
                                "--data-dir", self.data_dir,
                                "--cache-dir", self.cache_dir
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                except subprocess.CalledProcessError as e:
                    error_msg = f"Conda 환경에서 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
    
    def _run_script_directly(self, script_path):
        """
        스크립트를 직접 모듈로 로드하여 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        try:
            # 스크립트 모듈로 로드
            spec = importlib.util.spec_from_file_location("preprocessing_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 표준 함수들 찾아서 실행
            if hasattr(module, "preprocess"):
                module.preprocess(data_dir=self.data_dir, cache_dir=self.cache_dir)
            elif hasattr(module, "process"):
                module.process(data_dir=self.data_dir, cache_dir=self.cache_dir)
            elif hasattr(module, "main"):
                module.main(data_dir=self.data_dir, cache_dir=self.cache_dir)
            else:
                logger.warning(f"스크립트에 실행할 수 있는 함수를 찾을 수 없습니다: {script_path}")
                
        except Exception as e:
            error_msg = f"스크립트 직접 실행 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
