"""
GitHub 저장소 테이블에 repo_info 열 추가

데이터베이스 스키마 업데이트를 위한 스크립트입니다.
"""

import sqlite3
from pathlib import Path
import os
import sys

# 프로젝트 루트 디렉토리를 추가하여 import가 올바르게 작동하도록 합니다
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.connection import get_db_url

def add_repo_info_column():
    """
    github_repositories 테이블에 repo_info 열 추가
    """
    print("GitHub 저장소 테이블에 repo_info 열 추가 중...")
    
    # SQLite 데이터베이스 URL에서 파일 경로 추출
    db_url = get_db_url()
    db_path = db_url.replace('sqlite:///', '')
    
    if not Path(db_path).exists():
        print(f"오류: 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    try:
        # SQLite 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 정보 확인
        cursor.execute("PRAGMA table_info(github_repositories)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # repo_info 열이 이미 존재하는지 확인
        if 'repo_info' in column_names:
            print("repo_info 열이 이미 존재합니다.")
            conn.close()
            return True
        
        # ALTER TABLE 명령으로 새 열 추가
        cursor.execute("ALTER TABLE github_repositories ADD COLUMN repo_info TEXT DEFAULT '{}'")
        conn.commit()
        
        print("repo_info 열이 성공적으로 추가되었습니다.")
        conn.close()
        return True
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    add_repo_info_column()
