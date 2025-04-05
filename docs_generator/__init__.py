"""
LLMNightRun 문서 생성기 패키지

깃허브 자동 문서화 시스템을 위한 패키지입니다.
"""

import logging

from .workflow import run_workflow
from .git_handler import GitHandler
from .code_analyzer import CodeAnalyzer
from .document_builder import DocumentBuilder
from .llm_client import LLMClient
from .config import Config

# 기본 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 버전 정보
__version__ = '0.1.0'

# 패키지 내보내기
__all__ = [
    'run_workflow',
    'GitHandler',
    'CodeAnalyzer',
    'DocumentBuilder',
    'LLMClient',
    'Config'
]