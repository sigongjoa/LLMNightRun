"""
데이터베이스 테이블 초기화 스크립트
이 스크립트는 SQLite 데이터베이스를 생성하고 필요한 테이블을 만듭니다.
"""

import os
import sys
from pathlib import Path

# 현재 스크립트의 디렉토리를 찾고 프로젝트 루트 경로를 추가
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

# 백엔드 모듈 임포트
from backend.database.connection import engine, Base
from backend.database.models import (
    Question, 
    Response, 
    CodeSnippet, 
    CodeTemplate,
    Settings
)

def init_db():
    """데이터베이스 테이블을 생성합니다."""
    print("데이터베이스 테이블을 생성 중...")
    # metadata.create_all()을 사용하여 모든 정의된 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    init_db()