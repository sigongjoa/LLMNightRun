import pytest
from datetime import datetime
from backend.database.models import Question, Response, CodeSnippet, LLMTypeEnum, CodeLanguageEnum
from backend.database.operations import (
    get_questions, 
    create_question, 
    get_responses, 
    create_response,
    get_code_snippets,
    create_code_snippet,
    get_settings,
    create_or_update_settings
)
from backend.models import LLMType, CodeLanguage, Settings

def test_create_and_get_question(test_db):
    """질문 생성 및 조회 테스트"""
    # 질문 생성
    question = create_question(
        test_db, 
        {
            "content": "테스트 질문입니다", 
            "tags": ["테스트", "데이터베이스"]
        }
    )
    
    # ID 확인
    assert question.id is not None
    
    # 생성된 질문 조회
    questions = get_questions(test_db)
    assert len(questions) == 1
    assert questions[0].id == question.id
    assert questions[0].content == "테스트 질문입니다"
    assert len(questions[0].tags) == 2
    assert "테스트" in questions[0].tags
    
    # ID로 조회
    question_by_id = get_questions(test_db, question_id=question.id, single=True)
    assert question_by_id is not None
    assert question_by_id.id == question.id

def test_create_and_get_response(test_db):
    """응답 생성 및 조회 테스트"""
    # 먼저 질문 생성
    question = create_question(
        test_db, 
        {
            "content": "응답 테스트용 질문", 
            "tags": ["테스트"]
        }
    )
    
    # 응답 생성
    response = create_response(
        test_db,
        {
            "question_id": question.id,
            "llm_type": LLMType.OPENAI_API,
            "content": "테스트 응답입니다"
        }
    )
    
    # ID 확인
    assert response.id is not None
    
    # 생성된 응답 조회
    responses = get_responses(test_db)
    assert len(responses) == 1
    assert responses[0].id == response.id
    assert responses[0].question_id == question.id
    assert responses[0].content == "테스트 응답입니다"
    assert responses[0].llm_type == LLMTypeEnum.openai_api
    
    # 질문 ID로 조회
    responses_by_question = get_responses(test_db, question_id=question.id)
    assert len(responses_by_question) == 1
    assert responses_by_question[0].id == response.id
    
    # LLM 유형으로 조회
    responses_by_type = get_responses(test_db, llm_type=LLMType.OPENAI_API)
    assert len(responses_by_type) == 1
    assert responses_by_type[0].id == response.id

def test_create_and_get_code_snippet(test_db):
    """코드 스니펫 생성 및 조회 테스트"""
    # 먼저 질문과 응답 생성
    question = create_question(
        test_db, 
        {
            "content": "코드 스니펫 테스트용 질문", 
            "tags": ["테스트"]
        }
    )
    
    response = create_response(
        test_db,
        {
            "question_id": question.id,
            "llm_type": LLMType.OPENAI_API,
            "content": "코드 스니펫 테스트용 응답"
        }
    )
    
    # 코드 스니펫 생성
    snippet = create_code_snippet(
        test_db,
        {
            "title": "테스트 코드",
            "description": "테스트 설명",
            "content": "print('Hello, World!')",
            "language": CodeLanguage.PYTHON,
            "tags": ["파이썬", "테스트"],
            "source_llm": LLMType.OPENAI_API,
            "question_id": question.id,
            "response_id": response.id,
            "version": 1
        }
    )
    
    # ID 확인
    assert snippet.id is not None
    
    # 생성된 스니펫 조회
    snippets = get_code_snippets(test_db)
    assert len(snippets) == 1
    assert snippets[0].id == snippet.id
    assert snippets[0].title == "테스트 코드"
    assert snippets[0].content == "print('Hello, World!')"
    assert snippets[0].language == CodeLanguageEnum.python
    
    # 질문 ID로 조회
    snippets_by_question = get_code_snippets(test_db, question_id=question.id)
    assert len(snippets_by_question) == 1
    assert snippets_by_question[0].id == snippet.id
    
    # 언어로 조회
    snippets_by_language = get_code_snippets(test_db, language=CodeLanguage.PYTHON)
    assert len(snippets_by_language) == 1
    assert snippets_by_language[0].id == snippet.id

def test_create_and_get_settings(test_db):
    """설정 생성 및 조회 테스트"""
    # 설정이 없는지 확인
    settings = get_settings(test_db)
    assert settings is None
    
    # 설정 생성
    new_settings = create_or_update_settings(
        test_db,
        {
            "openai_api_key": "test_openai_key",
            "claude_api_key": "test_claude_key",
            "github_token": "test_github_token",
            "github_repo": "test_repo",
            "github_username": "test_username"
        }
    )
    
    # ID 확인
    assert new_settings.id == 1
    
    # 생성된 설정 조회
    settings = get_settings(test_db)
    assert settings is not None
    assert settings.openai_api_key == "test_openai_key"
    assert settings.claude_api_key == "test_claude_key"
    assert settings.github_token == "test_github_token"
    
    # 설정 업데이트
    updated_settings = create_or_update_settings(
        test_db,
        {
            "openai_api_key": "updated_openai_key",
            "claude_api_key": "updated_claude_key"
        }
    )
    
    # 같은 ID인지 확인
    assert updated_settings.id == 1
    
    # 업데이트된 설정 조회
    settings = get_settings(test_db)
    assert settings.openai_api_key == "updated_openai_key"
    assert settings.claude_api_key == "updated_claude_key"
    assert settings.github_token == "test_github_token"  # 업데이트되지 않은 필드