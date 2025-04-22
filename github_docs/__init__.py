"""
GitHub 문서 자동생성 모듈

GitHub 저장소의 코드를 분석하여 문서를 자동으로 생성하는 기능을 제공합니다.
"""

from .templates import get_available_templates, render_template
from .code_analyzer import analyze_repository, get_file_content_stats
