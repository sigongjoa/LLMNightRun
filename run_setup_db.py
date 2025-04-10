"""
데이터베이스 초기 설정 스크립트
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 문자열
from backend.config import settings
DB_CONN_STRING = settings.database.url

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_db_tables():
    """데이터베이스 테이블 생성"""
    from backend.database.connection import Base, engine
    
    try:
        logger.info("데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 중 오류: {str(e)}")
        return False

def create_admin_user():
    """관리자 사용자 생성"""
    from backend.database.connection import get_db
    from backend.database.models import User, UserSettings
    
    db = next(get_db())
    
    try:
        # 관리자 사용자가 이미 존재하는지 확인
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            logger.info("관리자 사용자가 이미 존재합니다.")
            return True
        
        # 관리자 비밀번호 해싱 (실제 구현에서는 안전한 비밀번호 사용!)
        hashed_password = pwd_context.hash("admin123")
        
        # 관리자 사용자 생성
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )
        
        # 사용자 설정 생성
        settings = UserSettings(
            user_id=admin.id,
            theme="light",
            language="ko",
            notification_enabled=True
        )
        
        # DB에 저장
        # 먼저 사용자 저장
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # ID를 가져온 후 설정 업데이트
        settings.user_id = admin.id
        # 설정 저장
        db.add(settings)
        db.commit()
        
        logger.info(f"관리자 사용자 생성 완료 (ID: {admin.id})")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"관리자 사용자 생성 중 오류: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """메인 실행 함수"""
    try:
        logger.info("데이터베이스 초기 설정 시작")
        
        # 테이블 생성
        if not create_db_tables():
            logger.error("데이터베이스 테이블 생성 실패")
            sys.exit(1)
        
        # 관리자 사용자 생성
        if not create_admin_user():
            logger.error("관리자 사용자 생성 실패")
            sys.exit(1)
        
        logger.info("데이터베이스 초기 설정 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기 설정 중 오류: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
