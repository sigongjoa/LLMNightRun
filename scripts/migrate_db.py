"""
데이터베이스 스키마 마이그레이션 스크립트

questions 및 responses 테이블에 project_id 컬럼을 추가합니다.
"""

import os
import sys
import sqlite3
import argparse
import shutil
from datetime import datetime

def backup_database(db_path):
    """데이터베이스 파일 백업"""
    # 백업 파일 이름 생성 (원본이름_YYYY-MM-DD_HHMMSS.backup)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = f"{db_path}.{timestamp}.backup"
    
    # 파일 복사
    shutil.copy2(db_path, backup_path)
    
    print(f"데이터베이스 백업 생성됨: {backup_path}")
    return backup_path

def migrate_database(db_path, skip_backup=False):
    """데이터베이스 스키마 마이그레이션 수행"""
    # 백업 수행
    if not skip_backup:
        backup_path = backup_database(db_path)
        print(f"원본 데이터베이스가 '{backup_path}'에 백업되었습니다.")
    
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 테이블 구조 확인
        print("현재 테이블 구조 확인 중...")
        
        # questions 테이블 검사
        cursor.execute("PRAGMA table_info(questions)")
        columns = cursor.fetchall()
        has_project_id_q = any(col[1] == 'project_id' for col in columns)
        
        # responses 테이블 검사
        cursor.execute("PRAGMA table_info(responses)")
        columns = cursor.fetchall()
        has_project_id_r = any(col[1] == 'project_id' for col in columns)
        
        # 필요한 마이그레이션 수행
        print("마이그레이션 시작...")
        
        if not has_project_id_q:
            print("questions 테이블에 project_id 컬럼 추가 중...")
            cursor.execute('ALTER TABLE questions ADD COLUMN project_id INTEGER REFERENCES projects(id)')
            print("questions 테이블 업데이트 완료!")
        else:
            print("questions 테이블에 이미 project_id 컬럼이 존재합니다.")
        
        if not has_project_id_r:
            print("responses 테이블에 project_id 컬럼 추가 중...")
            cursor.execute('ALTER TABLE responses ADD COLUMN project_id INTEGER REFERENCES projects(id)')
            print("responses 테이블 업데이트 완료!")
        else:
            print("responses 테이블에 이미 project_id 컬럼이 존재합니다.")
        
        # 변경사항 저장
        conn.commit()
        print("마이그레이션이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        # 오류 발생 시 롤백
        conn.rollback()
        print(f"오류 발생: {str(e)}")
        print("마이그레이션이 실패했습니다. 데이터베이스가 롤백되었습니다.")
        if not skip_backup:
            print(f"백업 파일({backup_path})을 사용하여 복원할 수 있습니다.")
        return False
    finally:
        # 연결 종료
        conn.close()
    
    return True

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='데이터베이스 스키마 마이그레이션')
    parser.add_argument('--db', default='llmnightrun.db', help='데이터베이스 파일 경로')
    parser.add_argument('--no-backup', action='store_true', help='백업 생성 건너뛰기')
    args = parser.parse_args()
    
    # 현재 디렉토리 기준 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    db_path = os.path.join(root_dir, args.db)
    
    # 파일 존재 여부 확인
    if not os.path.exists(db_path):
        print(f"오류: 데이터베이스 파일 '{db_path}'이(가) 존재하지 않습니다.")
        return 1
    
    print(f"데이터베이스 파일: {db_path}")
    print(f"백업 생성: {'아니오' if args.no_backup else '예'}")
    
    # 확인 질문
    if not args.no_backup:
        print("\n경고: 이 작업은 데이터베이스 스키마를 변경합니다.")
        print("계속하기 전에 백업이 생성됩니다.")
    else:
        print("\n경고: 백업 없이 데이터베이스 스키마를 변경합니다!")
        print("오류가 발생하면 데이터가 손실될 수 있습니다.")
    
    confirm = input("\n계속하시겠습니까? (y/n): ")
    if confirm.lower() != 'y':
        print("마이그레이션이 취소되었습니다.")
        return 0
    
    # 마이그레이션 실행
    success = migrate_database(db_path, args.no_backup)
    
    # 결과 출력
    if success:
        print("\n마이그레이션이 성공적으로 완료되었습니다.")
        print("이제 프로젝트 ID 기능을 사용할 수 있습니다.")
        print("원래 백엔드 서버(main.py)를 실행하여 변경사항을 확인하세요.")
        return 0
    else:
        print("\n마이그레이션이 실패했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
