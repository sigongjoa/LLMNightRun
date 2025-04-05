"""
설정 관리 모듈

이 모듈은 문서 생성기의 설정을 관리합니다.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)

# 기본 설정값
DEFAULT_CONFIG = {
    # 문서 생성 설정
    "docs": {
        "enabled": True,
        "types": ["README", "API", "MODELS", "DATABASE", "ARCHITECTURE", "TESTING", "CHANGELOG", "CONFIGURATION"],
        "output_dir": "docs",
        "force_recreate": False,
    },
    
    # Git 설정
    "git": {
        "auto_commit": True,
        "auto_push": False,
        "commit_prefix": "docs: ",
        "branch": None,  # None이면 현재 브랜치 사용
    },
    
    # LLM 설정
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.2,
        "api_key_env": "OPENAI_API_KEY",
    },
    
    # 파일 분석 설정
    "analysis": {
        "max_files": 100,
        "ignore_patterns": [
            "__pycache__/**",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git/**",
            ".vscode/**",
            ".idea/**",
            "venv/**",
            "env/**",
            "node_modules/**"
        ],
        "router_patterns": [
            "**/routes/**",
            "**/routers/**",
            "**/api/**",
            "*router*"
        ],
        "model_patterns": [
            "**/models/**",
            "*model*"
        ],
        "database_patterns": [
            "**/database/**",
            "**/db/**",
            "**/orm/**",
            "*db*"
        ],
        "test_patterns": [
            "**/tests/**",
            "**/*_test.py",
            "**/*test*.py"
        ],
        "config_patterns": [
            "**/*.yml",
            "**/*.yaml",
            "**/*.json",
            "**/*.toml",
            "**/*.ini",
            "**/*.env"
        ]
    }
}


class Config:
    """문서 생성기 설정 관리 클래스"""
    
    def __init__(self, repo_path: str = "."):
        """
        설정 관리자 초기화
        
        Args:
            repo_path: Git 저장소 경로
        """
        self.repo_path = os.path.abspath(repo_path)
        self.config_path = os.path.join(self.repo_path, '.docs-generator.yml')
        self.config = DEFAULT_CONFIG.copy()
        
        # 설정 파일 로드 시도
        self._load_config()
        
    def _load_config(self) -> None:
        """설정 파일 로드"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                
                if user_config:
                    # 사용자 설정으로 기본 설정 업데이트
                    self._update_nested_dict(self.config, user_config)
                    logger.info(f"설정 파일 로드됨: {self.config_path}")
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {str(e)}")
        else:
            logger.info(f"설정 파일이 없습니다. 기본 설정을 사용합니다: {self.config_path}")
            
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """중첩 딕셔너리 업데이트"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def save_config(self) -> bool:
        """
        현재 설정을 파일로 저장
        
        Returns:
            성공 여부
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"설정 파일 저장됨: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 가져오기
        
        Args:
            key: 설정 키 (점 표기법 지원, 예: 'docs.enabled')
            default: 기본값 (키가 없는 경우)
            
        Returns:
            설정값 또는 기본값
        """
        if '.' in key:
            parts = key.split('.')
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        설정값 설정
        
        Args:
            key: 설정 키 (점 표기법 지원)
            value: 설정값
        """
        if '.' in key:
            parts = key.split('.')
            target = self.config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
        else:
            self.config[key] = value
    
    def get_doc_types(self) -> List[str]:
        """
        생성할 문서 유형 목록 가져오기
        
        Returns:
            문서 유형 목록
        """
        return self.get('docs.types', ["README", "API", "MODELS", "DATABASE", "TESTING"])
    
    def is_doc_enabled(self, doc_type: str) -> bool:
        """
        특정 문서 유형이 활성화되어 있는지 확인
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            활성화 여부
        """
        if not self.get('docs.enabled', True):
            return False
        
        return doc_type in self.get_doc_types()
    
    def get_output_dir(self) -> str:
        """
        문서 출력 디렉토리 가져오기
        
        Returns:
            출력 디렉토리 경로
        """
        output_dir = self.get('docs.output_dir', 'docs')
        return os.path.join(self.repo_path, output_dir)
    
    def get_llm_api_key(self) -> Optional[str]:
        """
        LLM API 키 가져오기
        
        Returns:
            API 키 또는 None
        """
        env_var = self.get('llm.api_key_env', 'OPENAI_API_KEY')
        return os.environ.get(env_var)
    
    def get_ignore_patterns(self) -> List[str]:
        """
        무시할 파일 패턴 목록 가져오기
        
        Returns:
            패턴 목록
        """
        return self.get('analysis.ignore_patterns', [])
    
    def is_auto_commit_enabled(self) -> bool:
        """
        자동 커밋 활성화 여부 확인
        
        Returns:
            활성화 여부
        """
        return self.get('git.auto_commit', True)
    
    def is_auto_push_enabled(self) -> bool:
        """
        자동 푸시 활성화 여부 확인
        
        Returns:
            활성화 여부
        """
        return self.get('git.auto_push', False)
    
    def get_classification_patterns(self, file_type: str) -> List[str]:
        """
        파일 분류 패턴 가져오기
        
        Args:
            file_type: 파일 유형 (router, model, database, test, config)
            
        Returns:
            패턴 목록
        """
        pattern_key = f"analysis.{file_type}_patterns"
        return self.get(pattern_key, [])