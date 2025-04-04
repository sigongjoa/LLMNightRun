import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.connection import Base
from backend.main import app
from backend.database.connection import get_db

# 테스트용 데이터베이스 URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# 테스트 엔진 생성
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 테스트 세션 생성
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    # 테스트 DB 스키마 생성
    Base.metadata.create_all(bind=engine)
    
    # 테스트 세션 제공
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # 테스트 후 테이블 삭제
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    # FastAPI 테스트 클라이언트 생성
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
        
    # 의존성 오버라이드 제거
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_settings():
    """테스트용 설정 모의 객체"""
    class MockSettings:
        def __init__(self):
            self.openai_api_key = "test_openai_key"
            self.claude_api_key = "test_claude_key"
            self.github_token = "test_github_token"
            self.github_repo = "test_repo"
            self.github_username = "test_username"
            self.id = 1
    
    return MockSettings()