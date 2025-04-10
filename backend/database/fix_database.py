"""
데이터베이스 수정 모듈

데이터베이스 스키마를 수정하거나 문제를 해결하는 기능을 제공합니다.
"""

import sqlite3
import logging

from backend.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

def fix_code_snippets_table():
    """
    code_snippets 테이블에 project_id 컬럼이 없는 경우 추가하는 함수
    """
    try:
        # SQLite 데이터베이스 연결
        conn = sqlite3.connect(settings.database.url.replace('sqlite:///', ''))
        cursor = conn.cursor()
        
        # 테이블 정보 조회
        cursor.execute("PRAGMA table_info(code_snippets)")
        columns = cursor.fetchall()
        
        # project_id 컬럼이 있는지 확인
        has_project_id = any(column[1] == 'project_id' for column in columns)
        
        # project_id 컬럼이 없으면 추가
        if not has_project_id:
            logger.info("code_snippets 테이블에 project_id 컬럼 추가 중...")
            cursor.execute("ALTER TABLE code_snippets ADD COLUMN project_id INTEGER")
            conn.commit()
            logger.info("code_snippets 테이블에 project_id 컬럼 추가 완료")
        else:
            logger.info("code_snippets 테이블에 project_id 컬럼이 이미 존재합니다.")
        
        # 연결 종료
        conn.close()
        
        return True
    except sqlite3.Error as e:
        logger.error(f"데이터베이스 수정 중 오류 발생: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        return False


def disable_code_snippets():
    """
    code_snippets 테이블을 사용하지 않도록 비활성화하는 함수
    """
    try:
        # SQLite 데이터베이스 연결
        conn = sqlite3.connect(settings.database.url.replace('sqlite:///', ''))
        cursor = conn.cursor()
        
        # 테이블 이름 변경 (백업)
        try:
            logger.info("code_snippets 테이블 백업 중...")
            cursor.execute("ALTER TABLE code_snippets RENAME TO code_snippets_backup")
            conn.commit()
            logger.info("code_snippets 테이블 백업 완료")
        except sqlite3.Error as e:
            logger.warning(f"code_snippets 테이블 백업 중 오류 발생 (테이블이 없을 수 있음): {str(e)}")
        
        # 연결 종료
        conn.close()
        
        return True
    except sqlite3.Error as e:
        logger.error(f"데이터베이스 수정 중 오류 발생: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        return False
