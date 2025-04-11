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
    import logging
    logger = logging.getLogger(__name__)
    
    from sqlalchemy import inspect
    from sqlalchemy import Table, Column, Integer, Index
    
    # 인스펙터 생성
    inspector = inspect(engine)
    
    # code_snippets 테이블이 있는지 확인하고 인덱스 삭제
    try:
        if 'code_snippets' in inspector.get_table_names():
            # 이미 존재하는 인덱스 확인
            indexes = inspector.get_indexes('code_snippets')
            if any(idx['name'] == 'ix_code_snippets_id' for idx in indexes):
                # 인덱스가 이미 존재하면 메타데이터에서 해당 인덱스 삭제
                logger.info("인덱스 ix_code_snippets_id 이미 존재하므로 메타데이터에서 제거합니다.")
                
                # 메타데이터에서 code_snippets 테이블 가져오기
                code_snippets = Base.metadata.tables.get('code_snippets')
                
                # code_snippets 테이블이 메타데이터에 있으면 인덱스 제거
                if code_snippets is not None:
                    for idx in list(code_snippets.indexes):
                        if idx.name == 'ix_code_snippets_id':
                            code_snippets.indexes.remove(idx)
                            logger.info("메타데이터에서 ix_code_snippets_id 인덱스 제거 완료")
                            break
    except Exception as e:
        logger.error(f"인덱스 검사 중 오류 발생: {str(e)}")
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)