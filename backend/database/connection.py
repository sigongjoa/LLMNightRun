"""
데이터베이스 연결 모듈

SQLAlchemy 엔진과 세션을 관리합니다.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Generator

from backend.config import settings

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.database.url,
    connect_args=settings.database.connect_args
)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 호환성을 위한 별칭
Session = SessionLocal

# 모델 기본 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 제공 함수 (의존성 주입용)
def get_db() -> Generator:
    """데이터베이스 세션을 제공하는 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """컨텍스트 매니저로 데이터베이스 세션을 제공하는 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """데이터베이스 테이블을 생성하는 함수"""
    Base.metadata.create_all(bind=engine)