"""
설정 호환성 모듈

이 모듈은 호환성을 위해 유지되며, 실제 설정은 backend.config 패키지에 있습니다.
"""

# backend.config 패키지에서 settings 가져오기
from backend.config.settings import settings, get_settings, Settings

# 호환성을 위해 다시 내보내기
__all__ = ['settings', 'get_settings', 'Settings']
