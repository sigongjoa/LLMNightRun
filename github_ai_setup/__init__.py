"""
GitHub AI 설정 모듈

GitHub 저장소의 AI 관련 설정, 모델 훈련 환경, AI 설정 파이프라인을 제공합니다.
"""

from .analyzer import analyze_repository, get_ai_config_status
from .config_generator import generate_ai_config, apply_ai_config
from .environment import setup_environment, check_environment
from .manager import GitHubAIManager
