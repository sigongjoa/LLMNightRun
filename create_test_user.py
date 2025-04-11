"""
데이터베이스에 테스트 사용자 계정 생성 스크립트
"""

import os
import sys
import logging
from pathlib import Path

# 백엔드 디렉토리를 Python 경로에 추가
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # 백엔드 모듈 임포트
    from backend.database.connection import get_db, create_tables
    from backend.database.models import User, UserSettings
    from backend.auth.dependencies import get_password_hash
    from sqlalchemy.exc import IntegrityError
    
    # 테스트 계정 정보
    TEST_USERS = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "first_name": "관리자",
            "last_name": "사용자",
            "is_admin": True
        },
        {
            "username": "user",
            "email": "user@example.com",
            "password": "user123",
            "first_name": "일반",
            "last_name": "사용자",
            "is_admin": False
        }
    ]
    
    # 데이터베이스 테이블 생성
    logger.info("데이터베이스 테이블 생성 중...")
    create_tables()
    
    # 테스트 계정 생성
    logger.info("테스트 계정 생성 중...")
    db = next(get_db())
    
    for user_data in TEST_USERS:
        # 기존 사용자 확인
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        
        if existing_user:
            logger.info(f"사용자 '{user_data['username']}'이(가) 이미 존재합니다.")
            continue
        
        # 새 사용자 생성
        hashed_password = get_password_hash(user_data["password"])
        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            is_active=True,
            is_admin=user_data.get("is_admin", False)
        )
        
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            logger.info(f"사용자 '{new_user.username}' 생성 완료")
            
            # 사용자 설정 생성
            user_settings = UserSettings(
                user_id=new_user.id,
                theme="light",
                language="ko",
                notification_enabled=True
            )
            db.add(user_settings)
            db.commit()
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"사용자 '{user_data['username']}' 생성 중 오류 발생: {str(e)}")
    
    logger.info("\n" + "-"*50)
    logger.info("기본 테스트 계정:")
    logger.info("1. 관리자 계정")
    logger.info("   - 아이디: admin")
    logger.info("   - 비밀번호: admin123")
    logger.info("2. 일반 사용자 계정")
    logger.info("   - 아이디: user")
    logger.info("   - 비밀번호: user123")
    logger.info("-"*50)
    
    # 데이터베이스 연결 종료
    db.close()
    
except ImportError as e:
    logger.error(f"모듈 가져오기 오류: {str(e)}")
    logger.error("백엔드 디렉토리 구조를 확인하세요.")
    sys.exit(1)
except Exception as e:
    logger.error(f"오류 발생: {str(e)}")
    sys.exit(1)
