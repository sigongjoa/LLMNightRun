"""
코드 스니펫 및 템플릿 관련 데이터베이스 작업 모듈
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import CodeSnippet, CodeTemplate, CodeLanguageEnum, LLMTypeEnum


# 코드 스니펫 관련 함수
def get_code_snippets(db: Session, snippet_id: Optional[int] = None, question_id: Optional[int] = None,
                    response_id: Optional[int] = None, language: Optional[str] = None,
                    tag: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    코드 스니펫 목록 또는 단일 코드 스니펫을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 스니펫 ID (선택 사항)
        question_id: 질문 ID (선택 사항)
        response_id: 응답 ID (선택 사항)
        language: 코드 언어 (선택 사항)
        tag: 태그 (선택 사항)
        skip: 건너뛸 결과 수
        limit: 최대 결과 수
        
    Returns:
        코드 스니펫 목록 또는 단일 코드 스니펫
    """
    query = db.query(CodeSnippet)
    
    if snippet_id:
        return query.filter(CodeSnippet.id == snippet_id).first()
    
    if question_id:
        query = query.filter(CodeSnippet.question_id == question_id)
    
    if response_id:
        query = query.filter(CodeSnippet.response_id == response_id)
    
    if language:
        try:
            language_enum = CodeLanguageEnum[language]
            query = query.filter(CodeSnippet.language == language_enum)
        except KeyError:
            # 유효하지 않은 언어는 무시
            pass
    
    if tag:
        query = query.filter(CodeSnippet.tags.any(tag))
    
    return query.offset(skip).limit(limit).all()


def create_code_snippet(db: Session, title: str, content: str, language: str,
                      description: Optional[str] = None, tags: Optional[List[str]] = None,
                      source_llm: Optional[str] = None, question_id: Optional[int] = None,
                      response_id: Optional[int] = None, project_id: Optional[int] = None,
                      parent_id: Optional[int] = None) -> CodeSnippet:
    """
    새 코드 스니펫을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        title: 스니펫 제목
        content: 스니펫 내용
        language: 코드 언어
        description: 설명 (선택 사항)
        tags: 태그 목록 (선택 사항)
        source_llm: 소스 LLM (선택 사항)
        question_id: 질문 ID (선택 사항)
        response_id: 응답 ID (선택 사항)
        project_id: 프로젝트 ID (선택 사항)
        parent_id: 부모 스니펫 ID (선택 사항)
        
    Returns:
        생성된 코드 스니펫
    """
    try:
        language_enum = CodeLanguageEnum[language]
    except KeyError:
        language_enum = CodeLanguageEnum.other
    
    llm_type_enum = None
    if source_llm:
        try:
            llm_type_enum = LLMTypeEnum[source_llm]
        except KeyError:
            pass
    
    tags = tags or []
    
    snippet = CodeSnippet(
        title=title,
        content=content,
        language=language_enum,
        description=description,
        tags=tags,
        source_llm=llm_type_enum,
        question_id=question_id,
        response_id=response_id,
        project_id=project_id,
        parent_id=parent_id,
        version=1
    )
    
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    
    return snippet


def update_code_snippet(db: Session, snippet_id: int, snippet_data: Dict[str, Any]) -> Optional[CodeSnippet]:
    """
    코드 스니펫을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 스니펫 ID
        snippet_data: 업데이트할 스니펫 데이터
        
    Returns:
        업데이트된 코드 스니펫 또는 None
    """
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()
    
    if not snippet:
        return None
    
    # 내용이 변경된 경우 버전 증가
    if 'content' in snippet_data and snippet_data['content'] != snippet.content:
        snippet_data['version'] = snippet.version + 1
    
    for key, value in snippet_data.items():
        if hasattr(snippet, key) and value is not None:
            if key == 'language' and isinstance(value, str):
                try:
                    value = CodeLanguageEnum[value]
                except KeyError:
                    continue
            elif key == 'source_llm' and isinstance(value, str):
                try:
                    value = LLMTypeEnum[value]
                except KeyError:
                    continue
            
            setattr(snippet, key, value)
    
    db.commit()
    db.refresh(snippet)
    
    return snippet


def delete_code_snippet(db: Session, snippet_id: int) -> bool:
    """
    코드 스니펫을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        snippet_id: 스니펫 ID
        
    Returns:
        삭제 성공 여부
    """
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()
    
    if not snippet:
        return False
    
    db.delete(snippet)
    db.commit()
    
    return True


# 코드 템플릿 관련 함수
def get_code_templates(db: Session, template_id: Optional[int] = None,
                      language: Optional[str] = None, tag: Optional[str] = None,
                      skip: int = 0, limit: int = 100):
    """
    코드 템플릿 목록 또는 단일 코드 템플릿을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        template_id: 템플릿 ID (선택 사항)
        language: 코드 언어 (선택 사항)
        tag: 태그 (선택 사항)
        skip: 건너뛸 결과 수
        limit: 최대 결과 수
        
    Returns:
        코드 템플릿 목록 또는 단일 코드 템플릿
    """
    query = db.query(CodeTemplate)
    
    if template_id:
        return query.filter(CodeTemplate.id == template_id).first()
    
    if language:
        try:
            language_enum = CodeLanguageEnum[language]
            query = query.filter(CodeTemplate.language == language_enum)
        except KeyError:
            # 유효하지 않은 언어는 무시
            pass
    
    if tag:
        query = query.filter(CodeTemplate.tags.any(tag))
    
    return query.offset(skip).limit(limit).all()


def create_code_template(db: Session, name: str, content: str, language: str,
                        description: Optional[str] = None, tags: Optional[List[str]] = None,
                        project_id: Optional[int] = None) -> CodeTemplate:
    """
    새 코드 템플릿을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        name: 템플릿 이름
        content: 템플릿 내용
        language: 코드 언어
        description: 설명 (선택 사항)
        tags: 태그 목록 (선택 사항)
        project_id: 프로젝트 ID (선택 사항)
        
    Returns:
        생성된 코드 템플릿
    """
    try:
        language_enum = CodeLanguageEnum[language]
    except KeyError:
        language_enum = CodeLanguageEnum.other
    
    tags = tags or []
    
    template = CodeTemplate(
        name=name,
        content=content,
        language=language_enum,
        description=description,
        tags=tags,
        project_id=project_id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def update_code_template(db: Session, template_id: int, template_data: Dict[str, Any]) -> Optional[CodeTemplate]:
    """
    코드 템플릿을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        template_id: 템플릿 ID
        template_data: 업데이트할 템플릿 데이터
        
    Returns:
        업데이트된 코드 템플릿 또는 None
    """
    template = db.query(CodeTemplate).filter(CodeTemplate.id == template_id).first()
    
    if not template:
        return None
    
    for key, value in template_data.items():
        if hasattr(template, key) and value is not None:
            if key == 'language' and isinstance(value, str):
                try:
                    value = CodeLanguageEnum[value]
                except KeyError:
                    continue
            
            setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    
    return template


def delete_code_template(db: Session, template_id: int) -> bool:
    """
    코드 템플릿을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        template_id: 템플릿 ID
        
    Returns:
        삭제 성공 여부
    """
    template = db.query(CodeTemplate).filter(CodeTemplate.id == template_id).first()
    
    if not template:
        return False
    
    db.delete(template)
    db.commit()
    
    return True
