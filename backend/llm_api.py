from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime

from . import models
from .. import models as pydantic_models

# 질문 관련 함수
def get_questions(
    db: Session, 
    question_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100,
    single: bool = False
) -> Union[List[pydantic_models.Question], pydantic_models.Question, None]:
    """
    질문을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        question_id: 조회할 질문 ID (지정 시 해당 질문만 조회)
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        single: 단일 항목만 반환할지 여부
        
    Returns:
        질문 목록 또는 단일 질문 객체
    """
    query = db.query(models.Question)
    
    if question_id:
        query = query.filter(models.Question.id == question_id)
        if single:
            return query.first()
    
    return query.offset(skip).limit(limit).all()

def create_question(db: Session, question: pydantic_models.Question) -> pydantic_models.Question:
    """
    새 질문을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        question: 생성할 질문 Pydantic 모델
        
    Returns:
        생성된 질문 객체
    """
    db_question = models.Question(
        content=question.content,
        tags=question.tags,
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def update_question(
    db: Session, 
    question_id: int, 
    question_data: pydantic_models.Question
) -> Optional[pydantic_models.Question]:
    """
    질문을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        question_id: 업데이트할 질문 ID
        question_data: 업데이트할 데이터가 있는 Pydantic 모델
        
    Returns:
        업데이트된 질문 객체 또는 None (존재하지 않는 경우)
    """
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question:
        # 업데이트할 필드 설정
        if question_data.content:
            db_question.content = question_data.content
        if question_data.tags:
            db_question.tags = question_data.tags
            
        db.commit()
        db.refresh(db_question)
    return db_question

def delete_question(db: Session, question_id: int) -> bool:
    """
    질문을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        question_id: 삭제할 질문 ID
        
    Returns:
        성공 여부를 나타내는 불리언 값
    """
    db_question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if db_question:
        db.delete(db_question)
        db.commit()
        return True
    return False

# 응답 관련 함수
def get_responses(
    db: Session, 
    response_id: Optional[int] = None,
    question_id: Optional[int] = None,
    llm_type: Optional[pydantic_models.LLMType] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[pydantic_models.Response]:
    """
    응답을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        response_id: 조회할 응답 ID (지정 시 해당 응답만 조회)
        question_id: 특정 질문에 대한 응답만 조회
        llm_type: 특정 LLM 유형에 대한 응답만 조회
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        
    Returns:
        응답 목록
    """
    query = db.query(models.Response)
    
    if response_id:
        query = query.filter(models.Response.id == response_id)
    
    if question_id:
        query = query.filter(models.Response.question_id == question_id)
    
    if llm_type:
        query = query.filter(models.Response.llm_type == llm_type)
    
    return query.offset(skip).limit(limit).all()

def create_response(db: Session, response: pydantic_models.Response) -> pydantic_models.Response:
    """
    새 응답을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        response: 생성할 응답 Pydantic 모델
        
    Returns:
        생성된 응답 객체
    """
    db_response = models.Response(
        question_id=response.question_id,
        llm_type=response.llm_type,
        content=response.content,
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def update_response(
    db: Session, 
    response_id: int, 
    response_data: pydantic_models.Response
) -> Optional[pydantic_models.Response]:
    """
    응답을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        response_id: 업데이트할 응답 ID
        response_data: 업데이트할 데이터가 있는 Pydantic 모델
        
    Returns:
        업데이트된 응답 객체 또는 None (존재하지 않는 경우)
    """
    db_response = db.query(models.Response).filter(models.Response.id == response_id).first()
    if db_response:
        # 업데이트할 필드 설정
        if response_data.content:
            db_response.content = response_data.content
        if response_data.llm_type:
            db_response.llm_type = response_data.llm_type
            
        db.commit()
        db.refresh(db_response)
    return db_response

def delete_response(db: Session, response_id: int) -> bool:
    """
    응답을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        response_id: 삭제할 응답 ID
        
    Returns:
        성공 여부를 나타내는 불리언 값
    """
    db_response = db.query(models.Response).filter(models.Response.id == response_id).first()
    if db_response:
        db.delete(db_response)
        db.commit()
        return True
    return False

# 코드 스니펫 관련 함수
def get_code_snippets(
    db: Session, 
    snippet_id: Optional[int] = None,
    question_id: Optional[int] = None,
    response_id: Optional[int] = None,
    language: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[pydantic_models.CodeSnippet]:
    """
    코드 스니펫을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 조회할 스니펫 ID (지정 시 해당 스니펫만 조회)
        question_id: 특정 질문과 관련된 스니펫만 조회
        response_id: 특정 응답과 관련된 스니펫만 조회
        language: 특정 언어의 스니펫만 조회
        tag: 특정 태그가 포함된 스니펫만 조회
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        
    Returns:
        코드 스니펫 목록
    """
    query = db.query(models.CodeSnippet)
    
    if snippet_id:
        query = query.filter(models.CodeSnippet.id == snippet_id)
    
    if question_id:
        query = query.filter(models.CodeSnippet.question_id == question_id)
    
    if response_id:
        query = query.filter(models.CodeSnippet.response_id == response_id)
    
    if language:
        query = query.filter(models.CodeSnippet.language == language)
    
    if tag:
        # JSON 필드에서 특정 태그 포함 여부 확인 (데이터베이스에 따라 구현이 달라질 수 있음)
        # SQLite용 임시 구현 (실제 환경에서는 데이터베이스에 맞게 조정 필요)
        query = query.filter(models.CodeSnippet.tags.like(f'%{tag}%'))
    
    return query.offset(skip).limit(limit).all()

def create_code_snippet(
    db: Session, 
    code_snippet: pydantic_models.CodeSnippet
) -> pydantic_models.CodeSnippet:
    """
    새 코드 스니펫을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        code_snippet: 생성할 코드 스니펫 Pydantic 모델
        
    Returns:
        생성된 코드 스니펫 객체
    """
    db_snippet = models.CodeSnippet(
        title=code_snippet.title,
        description=code_snippet.description,
        content=code_snippet.content,
        language=code_snippet.language,
        tags=code_snippet.tags,
        source_llm=code_snippet.source_llm,
        question_id=code_snippet.question_id,
        response_id=code_snippet.response_id,
        version=code_snippet.version,
    )
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)
    return db_snippet

def update_code_snippet(
    db: Session, 
    snippet_id: int, 
    snippet_data: pydantic_models.CodeSnippet
) -> Optional[pydantic_models.CodeSnippet]:
    """
    코드 스니펫을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 업데이트할 스니펫 ID
        snippet_data: 업데이트할 데이터가 있는 Pydantic 모델
        
    Returns:
        업데이트된 코드 스니펫 객체 또는 None (존재하지 않는 경우)
    """
    db_snippet = db.query(models.CodeSnippet).filter(models.CodeSnippet.id == snippet_id).first()
    if db_snippet:
        # 새 버전 생성 (히스토리 관리)
        new_version = db_snippet.version + 1
        
        # 새 버전의 스니펫 생성 (원본 복제)
        new_snippet = models.CodeSnippet(
            title=db_snippet.title,
            description=db_snippet.description,
            content=db_snippet.content,
            language=db_snippet.language,
            tags=db_snippet.tags,
            source_llm=db_snippet.source_llm,
            question_id=db_snippet.question_id,
            response_id=db_snippet.response_id,
            version=new_version,
            parent_id=db_snippet.id
        )
        
        # 업데이트할 필드 설정
        if snippet_data.title:
            new_snippet.title = snippet_data.title
        if snippet_data.description:
            new_snippet.description = snippet_data.description
        if snippet_data.content:
            new_snippet.content = snippet_data.content
        if snippet_data.language:
            new_snippet.language = snippet_data.language
        if snippet_data.tags:
            new_snippet.tags = snippet_data.tags
            
        db.add(new_snippet)
        db.commit()
        db.refresh(new_snippet)
        return new_snippet
    return None

def delete_code_snippet(db: Session, snippet_id: int) -> bool:
    """
    코드 스니펫을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 삭제할 스니펫 ID
        
    Returns:
        성공 여부를 나타내는 불리언 값
    """
    db_snippet = db.query(models.CodeSnippet).filter(models.CodeSnippet.id == snippet_id).first()
    if db_snippet:
        db.delete(db_snippet)
        db.commit()
        return True
    return False

# 코드 템플릿 관련 함수
def get_code_templates(
    db: Session, 
    template_id: Optional[int] = None,
    language: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[pydantic_models.CodeTemplate]:
    """
    코드 템플릿을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        template_id: 조회할 템플릿 ID (지정 시 해당 템플릿만 조회)
        language: 특정 언어의 템플릿만 조회
        tag: 특정 태그가 포함된 템플릿만 조회
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        
    Returns:
        코드 템플릿 목록
    """
    query = db.query(models.CodeTemplate)
    
    if template_id:
        query = query.filter(models.CodeTemplate.id == template_id)
    
    if language:
        query = query.filter(models.CodeTemplate.language == language)
    
    if tag:
        # JSON 필드에서 특정 태그 포함 여부 확인
        query = query.filter(models.CodeTemplate.tags.like(f'%{tag}%'))
    
    return query.offset(skip).limit(limit).all()

def create_code_template(
    db: Session, 
    template: pydantic_models.CodeTemplate
) -> pydantic_models.CodeTemplate:
    """
    새 코드 템플릿을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        template: 생성할 코드 템플릿 Pydantic 모델
        
    Returns:
        생성된 코드 템플릿 객체
    """
    db_template = models.CodeTemplate(
        name=template.name,
        description=template.description,
        content=template.content,
        language=template.language,
        tags=template.tags,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_code_template(
    db: Session, 
    template_id: int, 
    template_data: pydantic_models.CodeTemplate
) -> Optional[pydantic_models.CodeTemplate]:
    """
    코드 템플릿을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        template_id: 업데이트할 템플릿 ID
        template_data: 업데이트할 데이터가 있는 Pydantic 모델
        
    Returns:
        업데이트된 코드 템플릿 객체 또는 None (존재하지 않는 경우)
    """
    db_template = db.query(models.CodeTemplate).filter(models.CodeTemplate.id == template_id).first()
    if db_template:
        # 업데이트할 필드 설정
        if template_data.name:
            db_template.name = template_data.name
        if template_data.description:
            db_template.description = template_data.description
        if template_data.content:
            db_template.content = template_data.content
        if template_data.language:
            db_template.language = template_data.language
        if template_data.tags:
            db_template.tags = template_data.tags
            
        db_template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_template)
        return db_template
    return None

def delete_code_template(db: Session, template_id: int) -> bool:
    """
    코드 템플릿을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        template_id: 삭제할 템플릿 ID
        
    Returns:
        성공 여부를 나타내는 불리언 값
    """
    db_template = db.query(models.CodeTemplate).filter(models.CodeTemplate.id == template_id).first()
    if db_template:
        db.delete(db_template)
        db.commit()
        return True
    return False

# 설정 관련 함수
def get_settings(db: Session) -> Optional[pydantic_models.Settings]:
    """
    시스템 설정을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        설정 객체 또는 None (설정이 없는 경우)
    """
    return db.query(models.Settings).first()

def create_or_update_settings(
    db: Session, 
    settings: pydantic_models.Settings
) -> pydantic_models.Settings:
    """
    시스템 설정을 생성하거나 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        settings: 설정 Pydantic 모델
        
    Returns:
        생성 또는 업데이트된 설정 객체
    """
    db_settings = db.query(models.Settings).first()
    
    if db_settings:
        # 기존 설정 업데이트
        if settings.openai_api_key:
            db_settings.openai_api_key = settings.openai_api_key
        if settings.claude_api_key:
            db_settings.claude_api_key = settings.claude_api_key
        if settings.github_token:
            db_settings.github_token = settings.github_token
        if settings.github_repo:
            db_settings.github_repo = settings.github_repo
        if settings.github_username:
            db_settings.github_username = settings.github_username
            
        db_settings.updated_at = datetime.utcnow()
    else:
        # 새 설정 생성
        db_settings = models.Settings(
            openai_api_key=settings.openai_api_key,
            claude_api_key=settings.claude_api_key,
            github_token=settings.github_token,
            github_repo=settings.github_repo,
            github_username=settings.github_username,
        )
        db.add(db_settings)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings