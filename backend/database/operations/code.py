"""
코드 관련 데이터베이스 작업 모듈

코드 스니펫 및 템플릿에 대한 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from ..models import (
    CodeSnippet as DBCodeSnippet, 
    CodeTemplate as DBCodeTemplate,
    CodeLanguageEnum, 
    LLMTypeEnum
)
from ...models.code import (
    CodeSnippet, CodeSnippetCreate,
    CodeTemplate, CodeTemplateCreate
)
from ...models.enums import CodeLanguage, LLMType


def get_code_snippets(
    db: Session, 
    snippet_id: Optional[int] = None,
    question_id: Optional[int] = None,
    response_id: Optional[int] = None,
    language: Optional[Union[str, CodeLanguage]] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[CodeSnippet]:
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
    query = db.query(DBCodeSnippet)
    
    if snippet_id:
        query = query.filter(DBCodeSnippet.id == snippet_id)
    
    if question_id:
        query = query.filter(DBCodeSnippet.question_id == question_id)
    
    if response_id:
        query = query.filter(DBCodeSnippet.response_id == response_id)
    
    if language:
        # Enum 변환
        if isinstance(language, str):
            db_language = CodeLanguageEnum[language]
        elif isinstance(language, CodeLanguage):
            db_language = CodeLanguageEnum[language.value]
        else:
            db_language = language
        
        query = query.filter(DBCodeSnippet.language == db_language)
    
    if tag:
        # JSON 필드에서 태그 검색 (데이터베이스에 따라 구현이 달라질 수 있음)
        query = query.filter(DBCodeSnippet.tags.like(f'%{tag}%'))
    
    return query.offset(skip).limit(limit).all()


def create_code_snippet(
    db: Session, 
    code_snippet: Union[CodeSnippet, CodeSnippetCreate, Dict[str, Any]]
) -> CodeSnippet:
    """
    새 코드 스니펫을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        code_snippet: 생성할 코드 스니펫 데이터
        
    Returns:
        생성된 코드 스니펫 객체
    """
    # 딕셔너리인 경우 처리
    if isinstance(code_snippet, dict):
        snippet_data = code_snippet
    else:
        snippet_data = code_snippet.dict()
    
    # ID 제거 (자동 생성)
    if "id" in snippet_data:
        del snippet_data["id"]
    
    # 생성/수정 시간 제거 (자동 설정)
    if "created_at" in snippet_data:
        del snippet_data["created_at"]
    if "updated_at" in snippet_data:
        del snippet_data["updated_at"]
    
    # 언어 처리 (문자열/Enum -> DB Enum)
    if "language" in snippet_data and not isinstance(snippet_data["language"], CodeLanguageEnum):
        language = snippet_data["language"]
        if isinstance(language, CodeLanguage):
            snippet_data["language"] = CodeLanguageEnum[language.value]
        else:
            snippet_data["language"] = CodeLanguageEnum[language]
    
    # LLM 타입 처리 (문자열/Enum -> DB Enum)
    if "source_llm" in snippet_data and snippet_data["source_llm"] and not isinstance(snippet_data["source_llm"], LLMTypeEnum):
        llm_type = snippet_data["source_llm"]
        if isinstance(llm_type, LLMType):
            snippet_data["source_llm"] = LLMTypeEnum[llm_type.value]
        else:
            snippet_data["source_llm"] = LLMTypeEnum[llm_type]
    
    # 데이터베이스 모델 생성
    db_snippet = DBCodeSnippet(**snippet_data)
    
    # 데이터베이스에 저장
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)
    
    return db_snippet


def update_code_snippet(
    db: Session, 
    snippet_id: int, 
    snippet_data: Union[CodeSnippet, Dict[str, Any]]
) -> Optional[CodeSnippet]:
    """
    코드 스니펫을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 업데이트할 스니펫 ID
        snippet_data: 업데이트할 데이터
        
    Returns:
        업데이트된 코드 스니펫 객체 또는 None (존재하지 않는 경우)
    """
    # 스니펫 조회
    db_snippet = db.query(DBCodeSnippet).filter(DBCodeSnippet.id == snippet_id).first()
    if not db_snippet:
        return None
    
    # 딕셔너리로 변환
    if not isinstance(snippet_data, dict):
        snippet_data = snippet_data.dict(exclude_unset=True)
    
    # 버전 증가 (새 버전 생성)
    new_version = db_snippet.version + 1
    
    # 새 버전의 스니펫 생성 (원본 복제)
    new_snippet = DBCodeSnippet(
        title=db_snippet.title,
        description=db_snippet.description,
        content=db_snippet.content,
        language=db_snippet.language,
        tags=db_snippet.tags,
        source_llm=db_snippet.source_llm,
        question_id=db_snippet.question_id,
        response_id=db_snippet.response_id,
        version=new_version,
        parent_id=snippet_id
    )
    
    # 언어 처리 (문자열/Enum -> DB Enum)
    if "language" in snippet_data and not isinstance(snippet_data["language"], CodeLanguageEnum):
        language = snippet_data["language"]
        if isinstance(language, CodeLanguage):
            snippet_data["language"] = CodeLanguageEnum[language.value]
        else:
            snippet_data["language"] = CodeLanguageEnum[language]
    
    # LLM 타입 처리 (문자열/Enum -> DB Enum)
    if "source_llm" in snippet_data and snippet_data["source_llm"] and not isinstance(snippet_data["source_llm"], LLMTypeEnum):
        llm_type = snippet_data["source_llm"]
        if isinstance(llm_type, LLMType):
            snippet_data["source_llm"] = LLMTypeEnum[llm_type.value]
        else:
            snippet_data["source_llm"] = LLMTypeEnum[llm_type]
    
    # 업데이트할 필드 설정
    for key, value in snippet_data.items():
        if hasattr(new_snippet, key):
            setattr(new_snippet, key, value)
    
    # 변경사항 저장
    db.add(new_snippet)
    db.commit()
    db.refresh(new_snippet)
    
    return new_snippet


def delete_code_snippet(db: Session, snippet_id: int) -> bool:
    """
    코드 스니펫을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 삭제할 스니펫 ID
        
    Returns:
        성공 여부
    """
    db_snippet = db.query(DBCodeSnippet).filter(DBCodeSnippet.id == snippet_id).first()
    if not db_snippet:
        return False
    
    db.delete(db_snippet)
    db.commit()
    
    return True


def get_code_templates(
    db: Session, 
    template_id: Optional[int] = None,
    language: Optional[Union[str, CodeLanguage]] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[CodeTemplate]:
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
    query = db.query(DBCodeTemplate)
    
    if template_id:
        query = query.filter(DBCodeTemplate.id == template_id)
    
    if language:
        # Enum 변환
        if isinstance(language, str):
            db_language = CodeLanguageEnum[language]
        elif isinstance(language, CodeLanguage):
            db_language = CodeLanguageEnum[language.value]
        else:
            db_language = language
        
        query = query.filter(DBCodeTemplate.language == db_language)
    
    if tag:
        # JSON 필드에서 태그 검색
        query = query.filter(DBCodeTemplate.tags.like(f'%{tag}%'))
    
    return query.offset(skip).limit(limit).all()


def create_code_template(
    db: Session, 
    template: Union[CodeTemplate, CodeTemplateCreate, Dict[str, Any]]
) -> CodeTemplate:
    """
    새 코드 템플릿을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        template: 생성할 코드 템플릿 데이터
        
    Returns:
        생성된 코드 템플릿 객체
    """
    # 딕셔너리인 경우 처리
    if isinstance(template, dict):
        template_data = template
    else:
        template_data = template.dict()
    
    # ID 제거 (자동 생성)
    if "id" in template_data:
        del template_data["id"]
    
    # 생성/수정 시간 제거 (자동 설정)
    if "created_at" in template_data:
        del template_data["created_at"]
    if "updated_at" in template_data:
        del template_data["updated_at"]
    
    # 언어 처리 (문자열/Enum -> DB Enum)
    if "language" in template_data and not isinstance(template_data["language"], CodeLanguageEnum):
        language = template_data["language"]
        if isinstance(language, CodeLanguage):
            template_data["language"] = CodeLanguageEnum[language.value]
        else:
            template_data["language"] = CodeLanguageEnum[language]
    
    # 데이터베이스 모델 생성
    db_template = DBCodeTemplate(**template_data)
    
    # 데이터베이스에 저장
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


def update_code_template(
    db: Session, 
    template_id: int, 
    template_data: Union[CodeTemplate, Dict[str, Any]]
) -> Optional[CodeTemplate]:
    """
    코드 템플릿을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        template_id: 업데이트할 템플릿 ID
        template_data: 업데이트할 데이터
        
    Returns:
        업데이트된 코드 템플릿 객체 또는 None (존재하지 않는 경우)
    """
    # 템플릿 조회
    db_template = db.query(DBCodeTemplate).filter(DBCodeTemplate.id == template_id).first()
    if not db_template:
        return None
    
    # 딕셔너리로 변환
    if not isinstance(template_data, dict):
        template_data = template_data.dict(exclude_unset=True)
    
    # 언어 처리 (문자열/Enum -> DB Enum)
    if "language" in template_data and not isinstance(template_data["language"], CodeLanguageEnum):
        language = template_data["language"]
        if isinstance(language, CodeLanguage):
            template_data["language"] = CodeLanguageEnum[language.value]
        else:
            template_data["language"] = CodeLanguageEnum[language]
    
    # 업데이트할 필드 설정
    for key, value in template_data.items():
        if hasattr(db_template, key):
            setattr(db_template, key, value)
    
    # 수정 시간 갱신
    db_template.updated_at = datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    db.refresh(db_template)
    
    return db_template


def delete_code_template(db: Session, template_id: int) -> bool:
    """
    코드 템플릿을 삭제하는 함수
    
    Args:
        db: 데이터베이스 세션
        template_id: 삭제할 템플릿 ID
        
    Returns:
        성공 여부
    """
    db_template = db.query(DBCodeTemplate).filter(DBCodeTemplate.id == template_id).first()
    if not db_template:
        return False
    
    db.delete(db_template)
    db.commit()
    
    return True