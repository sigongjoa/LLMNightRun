"""
GitHub 리포지토리 분석 모듈

이 모듈은 GitHub 리포지토리를 분석하여 모델 유형, 필요한 환경, 설치 방법 등을 식별합니다.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import requests
from git import Repo
from pathlib import Path


logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """GitHub 리포지토리를 분석하는 클래스"""
    
    def __init__(self, repo_url: str, clone_path: Optional[str] = None):
        """
        초기화 함수
        
        Args:
            repo_url: GitHub 리포지토리 URL
            clone_path: 리포지토리를 클론할 로컬 경로 (기본값: None - 임시 디렉토리 사용)
        """
        self.repo_url = repo_url
        self.repo_name = self._extract_repo_name(repo_url)
        self.clone_path = clone_path or os.path.join("models", self.repo_name)
        self.repo = None
        self.analysis_result = {}
        
    def _extract_repo_name(self, url: str) -> str:
        """URL에서 리포지토리 이름 추출"""
        # GitHub URL 패턴: https://github.com/username/repo
        match = re.search(r'github\.com/[^/]+/([^/]+)', url)
        if match:
            return match.group(1)
        return url.split('/')[-1]  # 폴백: URL의 마지막 부분 사용
    
    def clone_repository(self) -> bool:
        """GitHub 리포지토리 클론"""
        try:
            logger.info(f"Cloning repository {self.repo_url} to {self.clone_path}")
            if os.path.exists(self.clone_path):
                self.repo = Repo(self.clone_path)
                logger.info(f"Repository already exists at {self.clone_path}")
                return True
                
            self.repo = Repo.clone_from(self.repo_url, self.clone_path)
            logger.info(f"Repository cloned successfully to {self.clone_path}")
            return True
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return False
    
    def analyze(self) -> Dict[str, Any]:
        """리포지토리 분석 수행"""
        if not self.repo and not self.clone_repository():
            return {"error": "Failed to clone repository"}
        
        self.analysis_result = {
            "repo_name": self.repo_name,
            "repo_url": self.repo_url,
            "clone_path": self.clone_path,
        }
        
        # 파일 구조 분석
        self._analyze_file_structure()
        
        # README 분석
        self._analyze_readme()
        
        # 요구사항 파일 분석
        self._analyze_requirements()
        
        # 설정 파일 분석
        self._analyze_config_files()
        
        # 모델 유형 식별
        self._identify_model_type()
        
        # 실행 스크립트 식별
        self._identify_launch_scripts()
        
        return self.analysis_result
    
    def _analyze_file_structure(self):
        """리포지토리의 파일 구조 분석"""
        file_structure = []
        root_path = Path(self.clone_path)
        
        for path in root_path.glob('**/*'):
            if '.git' in path.parts:
                continue
            
            rel_path = path.relative_to(root_path)
            if path.is_file():
                file_structure.append(str(rel_path))
        
        self.analysis_result["file_structure"] = file_structure
    
    def _analyze_readme(self):
        """README 파일 분석"""
        readme_paths = [
            os.path.join(self.clone_path, "README.md"),
            os.path.join(self.clone_path, "Readme.md"),
            os.path.join(self.clone_path, "readme.md"),
        ]
        
        readme_content = None
        for path in readme_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    readme_content = f.read()
                break
        
        if readme_content:
            self.analysis_result["readme"] = {
                "content": readme_content[:1000] + "..." if len(readme_content) > 1000 else readme_content,
                "full_path": path
            }
    
    def _analyze_requirements(self):
        """요구사항 파일 분석"""
        req_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "environment.yml",
            "setup.py"
        ]
        
        requirements = {}
        
        for req_file in req_files:
            file_path = os.path.join(self.clone_path, req_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                requirements[req_file] = {
                    "content": content,
                    "path": file_path
                }
        
        self.analysis_result["requirements"] = requirements
    
    def _analyze_config_files(self):
        """설정 파일 분석"""
        config_patterns = [
            "*.yaml",
            "*.yml",
            "*.json",
            "*.ini",
            "*.cfg",
            "config*"
        ]
        
        config_files = {}
        
        for pattern in config_patterns:
            root_path = Path(self.clone_path)
            for file_path in root_path.glob(f"**/{pattern}"):
                if '.git' in file_path.parts:
                    continue
                
                rel_path = file_path.relative_to(root_path)
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        config_files[str(rel_path)] = {
                            "content": content,
                            "path": str(file_path)
                        }
                    except Exception as e:
                        logger.error(f"Error reading config file {file_path}: {str(e)}")
        
        self.analysis_result["config_files"] = config_files
    
    def _identify_model_type(self):
        """모델 유형 식별"""
        model_indicators = {
            "llama": ["llama", "alpaca", "vicuna"],
            "mistral": ["mistral"],
            "stable_diffusion": ["stable-diffusion", "stablediffusion", "diffusion"],
            "gpt": ["gpt", "minigpt", "tinygpt"],
            "bert": ["bert", "roberta", "electra"],
            "t5": ["t5", "flan-t5"],
            "huggingface": ["transformers", "huggingface", "tokenizers"]
        }
        
        detected_models = {}
        
        # README 및 파일 구조에서 모델 키워드 탐색
        readme = self.analysis_result.get("readme", {}).get("content", "").lower()
        file_structure = " ".join(self.analysis_result.get("file_structure", [])).lower()
        combined_text = readme + " " + file_structure
        
        for model_type, indicators in model_indicators.items():
            for indicator in indicators:
                if indicator.lower() in combined_text:
                    detected_models[model_type] = detected_models.get(model_type, 0) + 1
        
        # 가장 많이 언급된 모델 유형 선택
        if detected_models:
            primary_model = max(detected_models.items(), key=lambda x: x[1])[0]
            self.analysis_result["model_type"] = {
                "primary": primary_model,
                "all_detected": detected_models
            }
        else:
            self.analysis_result["model_type"] = {
                "primary": "unknown",
                "all_detected": {}
            }
    
    def _identify_launch_scripts(self):
        """실행 스크립트 식별"""
        launch_scripts = []
        
        # 일반적인 실행 스크립트 패턴
        launch_patterns = [
            "run.py", "app.py", "main.py", "inference.py", "demo.py",
            "predict.py", "serve.py", "start.py", "server.py",
            "gradio_*.py", "streamlit_*.py", "web_*.py",
            "*.sh", "run_*.py", "launch_*.py"
        ]
        
        for pattern in launch_patterns:
            root_path = Path(self.clone_path)
            for file_path in root_path.glob(f"**/{pattern}"):
                if '.git' in file_path.parts:
                    continue
                
                rel_path = file_path.relative_to(root_path)
                if file_path.is_file():
                    launch_scripts.append(str(rel_path))
        
        self.analysis_result["launch_scripts"] = launch_scripts
