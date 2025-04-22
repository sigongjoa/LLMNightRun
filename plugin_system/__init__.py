"""
플러그인 시스템 모듈

플러그인 검색, 로드 및 관리 기능을 제공합니다.
"""

from .registry import PluginRegistry, get_registry
from .loader import load_plugin, load_plugins
