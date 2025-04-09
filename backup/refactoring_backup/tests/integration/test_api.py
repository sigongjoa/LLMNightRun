import pytest
from fastapi.testclient import TestClient
from backend.models import LLMType

def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "LLMNightRun API" in response.json()["message"]

def test_health_endpoint(client):
    """헬스 체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "version" in response.json()
    assert "timestamp" in response.json()

def test_create_question(client):
    """질문 생성 API 테스트"""
    question_data = {
        "content": "테스트 질문입니다",
        "tags": ["테스트", "API"]
    }
    
    response = client.post("/questions/", json=question_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["content"] == question_data["content"]
    assert data["tags"] == question_data["tags"]
    assert "id" in data
    assert data["id"] is not None
    assert "created_at" in data
    
    # 생성된 ID 저장
    question_id = data["id"]
    
    # 생성한 질문 조회 테스트
    response = client.get(f"/questions/?skip=0&limit=100")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 1
    
    # ID로 특정 질문이 있는지 확인
    found = False
    for q in questions:
        if q["id"] == question_id:
            found = True
            assert q["content"] == question_data["content"]
            break
    
    assert found, "생성한 질문을 조회할 수 없습니다"

def test_create_response(client):
    """응답 생성 API 테스트"""
    # 먼저 질문 생성
    question_data = {
        "content": "응답 테스트용 질문",
        "tags": ["테스트"]
    }
    
    question_response = client.post("/questions/", json=question_data)
    assert question_response.status_code == 200
    question_id = question_response.json()["id"]
    
    # 응답 생성
    response_data = {
        "question_id": question_id,
        "llm_type": LLMType.OPENAI_API,
        "content": "테스트 응답입니다"
    }
    
    response = client.post("/responses/", json=response_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["question_id"] == question_id
    assert data["llm_type"] == LLMType.OPENAI_API
    assert data["content"] == response_data["content"]
    assert "id" in data
    assert data["id"] is not None
    assert "created_at" in data
    
    # 생성된 ID 저장
    response_id = data["id"]
    
    # 생성한 응답 조회 테스트
    response = client.get(f"/responses/?question_id={question_id}")
    assert response.status_code == 200
    responses = response.json()
    assert len(responses) >= 1
    
    # ID로 특정 응답이 있는지 확인
    found = False
    for r in responses:
        if r["id"] == response_id:
            found = True
            assert r["content"] == response_data["content"]
            assert r["llm_type"] == response_data["llm_type"]
            break
    
    assert found, "생성한 응답을 조회할 수 없습니다"