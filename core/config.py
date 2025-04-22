#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
설정 관리 모듈

이 모듈은 애플리케이션 설정을 관리하고 모든 모듈에서 접근할 수 있는 중앙화된 설정 시스템을 제공합니다.
"""

import os
import json
# yaml 모듈을 임포트할 수 없는 경우 대체 구현
try:
    import yaml
except ImportError:
    # yaml 모듈이 없는 경우 간단한 대체 구현
    class SimpleYAML:
        @staticmethod
        def safe_load(stream):
            # JSON과 유사하게 처리 (제한적 기능)
            return json.loads(stream)
            
        @staticmethod
        def dump(data, stream, default_flow_style=False, allow_unicode=True):
            # JSON 형식으로 저장
            json.dump(data, stream, indent=2, ensure_ascii=not allow_unicode)
    
    yaml = SimpleYAML()
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """구성 관리자 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        설정 관리자 초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: 없음, 기본 설정 사용)
        """
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_path = config_path
        self._config = {}
        
        # 기본 설정 로드
        self._load_defaults()
        
        # 사용자 설정 로드 (있는 경우)
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_defaults(self):
        """기본 설정값 로드"""
        self._config = {
            # 코어 설정
            "core": {
                "debug": False,
                "log_level": "INFO",
                "log_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"),
            },
            # 로컬 LLM 설정
            "local_llm": {
                "enabled": True,
                "base_url": "http://127.0.0.1:1234",
                "model_id": "deepseek-r1-distill-qwen-7b",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9,
                "timeout": 30,
            },
            # 벡터 DB 설정
            "vector_db": {
                "storage_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_db"),
                "default_encoder": "default",
                "dimension": 768,
                "sentence_transformer_model": "all-MiniLM-L6-v2",
            },
            # 대화 관리 설정
            "conversation": {
                "storage_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "conversations"),
                "max_history": 100,
                "default_format": "json",
            },
            # 플러그인 설정
            "plugin_system": {
                "plugins_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),
                "enabled_plugins": [],
                "auto_discover": True,
            },
            # GUI 설정
            "gui": {
                "theme": "light",
                "font_size": 10,
                "window_size": [800, 600],
                "save_layout": True,
            }
        }
        
        # 필요한 디렉토리 생성
        for section, settings in self._config.items():
            for key, value in settings.items():
                if isinstance(value, str) and (key.endswith('_dir') or key.endswith('_path')):
                    os.makedirs(value, exist_ok=True)
    
    def _load_config(self, config_path: str):
        """
        설정 파일 로드
        
        Args:
            config_path: 설정 파일 경로
        """
        try:
            ext = os.path.splitext(config_path)[1].lower()
            
            if ext == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
            elif ext in ['.yaml', '.yml']:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
            else:
                raise ValueError(f"지원되지 않는 설정 파일 형식: {ext}")
            
            # 사용자 설정으로 기본 설정 업데이트
            self._update_nested_dict(self._config, user_config)
            
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {str(e)}")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """
        중첩된 딕셔너리 업데이트
        
        Args:
            d: 대상 딕셔너리
            u: 업데이트할 딕셔너리
        
        Returns:
            업데이트된 딕셔너리
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        설정값 가져오기
        
        Args:
            section: 설정 섹션
            key: 설정 키 (None이면 섹션 전체 반환)
            default: 기본값 (키가 없을 경우)
        
        Returns:
            설정값 또는 기본값
        """
        if section not in self._config:
            return default
        
        if key is None:
            return self._config[section]
        
        return self._config[section].get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        설정값 설정
        
        Args:
            section: 설정 섹션
            key: 설정 키
            value: 설정값
        """
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
    
    def save(self, config_path: Optional[str] = None) -> None:
        """
        설정 저장
        
        Args:
            config_path: 저장할 설정 파일 경로 (기본값: 현재 설정 파일)
        """
        if config_path is None:
            if self.config_path is None:
                config_path = os.path.join(self.config_dir, "config.yaml")
            else:
                config_path = self.config_path
        
        try:
            # 파일 경로 확인 및 디렉토리 생성
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 확장자 확인
            ext = os.path.splitext(config_path)[1].lower()
            
            if ext == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            elif ext in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"지원되지 않는 설정 파일 형식: {ext}")
            
            self.config_path = config_path
            print(f"설정이 저장되었습니다: {config_path}")
        
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {str(e)}")

# 전역 설정 객체
_config_instance = None

def get_config(config_path: Optional[str] = None) -> Config:
    """
    전역 설정 객체 가져오기
    
    Args:
        config_path: 설정 파일 경로 (최초 호출 시에만 사용)
    
    Returns:
        설정 객체
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_path)
    
    return _config_instance
