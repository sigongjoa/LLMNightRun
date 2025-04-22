"""
자동 문서화 모듈의 메인 실행 파일
"""

import os
import sys
from pathlib import Path

# 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# GUI 애플리케이션 로드 및 실행
from gui_app import main

if __name__ == "__main__":
    main()
