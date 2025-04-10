import sqlite3
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 데이터베이스 파일 경로
db_path = os.path.join(project_root, "llmnightrun.db")

def fix_github_repositories_table():
    print(f"데이터베이스 스키마 수정 중: {db_path}")
    
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
        else:
            # ALTER TABLE 명령으로 새 열 추가
            print("github_repositories 테이블에 repo_info 열 추가 중...")
            cursor.execute("ALTER TABLE github_repositories ADD COLUMN repo_info TEXT DEFAULT '{}'")
            conn.commit()
            print("repo_info 열이 성공적으로 추가되었습니다.")
        
        conn.close()
        print("데이터베이스 스키마 수정이 완료되었습니다.")
        return True
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    fix_github_repositories_table()
