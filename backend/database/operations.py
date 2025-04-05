from sqlalchemy.orm import Session
from datetime import datetime

from . import models
# from .. import models as pydantic_models
from backend import models as pydantic_models

from typing import List, Optional, Dict, Any, Union
import json

from . import models
from backend import models as pydantic_models
from backend.models import IndexingStatus, IndexingFrequency

from ..models.agent_log import AgentSession as DBAgentSession, AgentLog as DBAgentLog, AgentPhaseEnum
from ...models.agent_log import AgentSession, AgentLog, AgentPhase

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


# 인덱싱 설정 관리 함수
def get_indexing_settings(
    db: Session,
    codebase_id: int
) -> Optional[models.CodebaseIndexingSettings]:
    """
    코드베이스의 인덱싱 설정을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        인덱싱 설정 또는 None (없는 경우)
    """
    return db.query(models.CodebaseIndexingSettings)\
        .filter(models.CodebaseIndexingSettings.codebase_id == codebase_id)\
        .first()

def create_or_update_indexing_settings(
    db: Session,
    codebase_id: int,
    settings: Dict[str, Any]
) -> models.CodebaseIndexingSettings:
    """
    코드베이스의 인덱싱 설정을 생성하거나 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        settings: 설정 데이터
        
    Returns:
        생성 또는 업데이트된 인덱싱 설정
    """
    # 기존 설정이 있는지 확인
    existing_settings = get_indexing_settings(db, codebase_id)
    
    if existing_settings:
        # 기존 설정 업데이트
        for key, value in settings.items():
            if value is not None and hasattr(existing_settings, key):
                setattr(existing_settings, key, value)
        
        existing_settings.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_settings)
        return existing_settings
    else:
        # 새 설정 생성
        new_settings = models.CodebaseIndexingSettings(
            codebase_id=codebase_id,
            **settings
        )
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings

# 인덱싱 실행 관리 함수
def create_indexing_run(
    db: Session,
    codebase_id: int,
    is_full_index: bool = False,
    triggered_by: str = "manual"
) -> models.CodebaseIndexingRun:
    """
    새 인덱싱 실행을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        is_full_index: 전체 인덱싱 여부
        triggered_by: 트리거 소스
        
    Returns:
        생성된 인덱싱 실행 객체
    """
    # 설정 ID 조회
    settings = get_indexing_settings(db, codebase_id)
    settings_id = settings.id if settings else None
    
    # 인덱싱 실행 생성
    indexing_run = models.CodebaseIndexingRun(
        codebase_id=codebase_id,
        settings_id=settings_id,
        status=models.IndexingStatusEnum.pending,
        is_full_index=is_full_index,
        triggered_by=triggered_by
    )
    
    db.add(indexing_run)
    db.commit()
    db.refresh(indexing_run)
    return indexing_run

def update_indexing_run(
    db: Session,
    run_id: int,
    update_data: Dict[str, Any]
) -> Optional[models.CodebaseIndexingRun]:
    """
    인덱싱 실행 정보를 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        run_id: 인덱싱 실행 ID
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트된 인덱싱 실행 객체 또는 None (없는 경우)
    """
    indexing_run = db.query(models.CodebaseIndexingRun)\
        .filter(models.CodebaseIndexingRun.id == run_id)\
        .first()
    
    if not indexing_run:
        return None
    
    # 필드 업데이트
    for key, value in update_data.items():
        if hasattr(indexing_run, key):
            setattr(indexing_run, key, value)
    
    db.commit()
    db.refresh(indexing_run)
    return indexing_run

def get_indexing_runs(
    db: Session,
    codebase_id: int,
    status: Optional[str] = None,
    limit: int = 10
) -> List[models.CodebaseIndexingRun]:
    """
    코드베이스의 인덱싱 실행 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        status: 상태 필터
        limit: 최대 조회 개수
        
    Returns:
        인덱싱 실행 목록
    """
    query = db.query(models.CodebaseIndexingRun)\
        .filter(models.CodebaseIndexingRun.codebase_id == codebase_id)
    
    if status:
        query = query.filter(models.CodebaseIndexingRun.status == status)
    
    return query.order_by(models.CodebaseIndexingRun.id.desc())\
        .limit(limit)\
        .all()

def get_latest_indexing_run(
    db: Session,
    codebase_id: int
) -> Optional[models.CodebaseIndexingRun]:
    """
    코드베이스의 최신 인덱싱 실행을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        최신 인덱싱 실행 또는 None (없는 경우)
    """
    return db.query(models.CodebaseIndexingRun)\
        .filter(models.CodebaseIndexingRun.codebase_id == codebase_id)\
        .order_by(models.CodebaseIndexingRun.id.desc())\
        .first()

# 코드 임베딩 관리 함수
def create_code_embedding(
    db: Session,
    codebase_id: int,
    file_id: int,
    chunk_id: str,
    content: str,
    embedding: Optional[List[float]] = None,
    embedding_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    run_id: Optional[int] = None
) -> models.CodeEmbedding:
    """
    새 코드 임베딩을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        file_id: 파일 ID
        chunk_id: 청크 ID
        content: 원본 코드 내용
        embedding: 임베딩 벡터
        embedding_key: 외부 벡터 DB에서의 키
        metadata: 추가 메타데이터
        run_id: 인덱싱 실행 ID
        
    Returns:
        생성된 코드 임베딩 객체
    """
    code_embedding = models.CodeEmbedding(
        codebase_id=codebase_id,
        file_id=file_id,
        run_id=run_id,
        chunk_id=chunk_id,
        content=content,
        embedding=embedding,
        embedding_key=embedding_key,
        metadata=metadata or {}
    )
    
    db.add(code_embedding)
    db.commit()
    db.refresh(code_embedding)
    return code_embedding

def update_code_embedding(
    db: Session,
    embedding_id: int,
    update_data: Dict[str, Any]
) -> Optional[models.CodeEmbedding]:
    """
    코드 임베딩을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        embedding_id: 임베딩 ID
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트된 코드 임베딩 객체 또는 None (없는 경우)
    """
    code_embedding = db.query(models.CodeEmbedding)\
        .filter(models.CodeEmbedding.id == embedding_id)\
        .first()
    
    if not code_embedding:
        return None
    
    # 필드 업데이트
    for key, value in update_data.items():
        if hasattr(code_embedding, key):
            setattr(code_embedding, key, value)
    
    code_embedding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(code_embedding)
    return code_embedding

def get_file_embeddings(
    db: Session,
    file_id: int
) -> List[models.CodeEmbedding]:
    """
    파일의 모든 임베딩을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        file_id: 파일 ID
        
    Returns:
        코드 임베딩 목록
    """
    return db.query(models.CodeEmbedding)\
        .filter(models.CodeEmbedding.file_id == file_id)\
        .all()

def delete_file_embeddings(
    db: Session,
    file_id: int
) -> int:
    """
    파일의 모든 임베딩을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        file_id: 파일 ID
        
    Returns:
        삭제된 임베딩 수
    """
    result = db.query(models.CodeEmbedding)\
        .filter(models.CodeEmbedding.file_id == file_id)\
        .delete()
    
    db.commit()
    return result

def get_codebase_embeddings_stats(
    db: Session,
    codebase_id: int
) -> Dict[str, Any]:
    """
    코드베이스의 임베딩 통계를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        통계 정보
    """
    # 총 임베딩 수
    total_embeddings = db.query(models.CodeEmbedding)\
        .filter(models.CodeEmbedding.codebase_id == codebase_id)\
        .count()
    
    # 임베딩된 파일 수
    indexed_files = db.query(models.CodeEmbedding.file_id)\
        .filter(models.CodeEmbedding.codebase_id == codebase_id)\
        .distinct()\
        .count()
    
    # 최근 인덱싱 실행
    latest_run = get_latest_indexing_run(db, codebase_id)
    
    return {
        "total_embeddings": total_embeddings,
        "indexed_files": indexed_files,
        "last_indexed_at": latest_run.end_time if latest_run and latest_run.end_time else None,
        "last_index_status": latest_run.status.value if latest_run else None
    }

def get_agent_sessions(
    db: Session, 
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[AgentSession]:
    """
    Agent 세션 목록 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 특정 세션 ID로 필터링
        agent_type: Agent 유형으로 필터링
        status: 상태로 필터링
        skip: 건너뛸 항목 수
        limit: 최대 반환 항목 수
    
    Returns:
        Agent 세션 목록
    """
    query = db.query(DBAgentSession)
    
    if session_id:
        query = query.filter(DBAgentSession.session_id == session_id)
    
    if agent_type:
        query = query.filter(DBAgentSession.agent_type == agent_type)
    
    if status:
        query = query.filter(DBAgentSession.status == status)
    
    query = query.order_by(DBAgentSession.start_time.desc())
    
    return query.offset(skip).limit(limit).all()


def get_agent_session(
    db: Session, 
    session_id: str
) -> Optional[AgentSession]:
    """
    특정 Agent 세션 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
    
    Returns:
        Agent 세션 또는 None
    """
    return db.query(DBAgentSession).filter(DBAgentSession.session_id == session_id).first()


def create_agent_session(
    db: Session,
    session: AgentSession
) -> AgentSession:
    """
    새 Agent 세션 생성
    
    Args:
        db: 데이터베이스 세션
        session: 생성할 세션 정보
    
    Returns:
        생성된 Agent 세션
    """
    db_session = DBAgentSession(
        session_id=session.session_id,
        agent_type=session.agent_type,
        start_time=session.start_time or datetime.utcnow(),
        status=session.status,
        parameters=session.parameters or {}
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


def update_agent_session(
    db: Session,
    session_id: str,
    update_data: Dict[str, Any]
) -> Optional[AgentSession]:
    """
    Agent 세션 업데이트
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
        update_data: 업데이트할 데이터 필드
    
    Returns:
        업데이트된 Agent 세션 또는 None
    """
    db_session = db.query(DBAgentSession).filter(DBAgentSession.session_id == session_id).first()
    
    if not db_session:
        return None
    
    for key, value in update_data.items():
        if hasattr(db_session, key):
            setattr(db_session, key, value)
    
    db.commit()
    db.refresh(db_session)
    
    return db_session


def finish_agent_session(
    db: Session,
    session_id: str,
    status: str = "completed"
) -> Optional[AgentSession]:
    """
    Agent 세션 종료 처리
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
        status: 종료 상태 (completed, error 등)
    
    Returns:
        업데이트된 Agent 세션 또는 None
    """
    return update_agent_session(
        db,
        session_id,
        {
            "status": status,
            "end_time": datetime.utcnow()
        }
    )


def get_agent_logs(
    db: Session,
    session_id: Optional[str] = None,
    phase: Optional[Union[AgentPhase, str]] = None,
    step: Optional[int] = None,
    has_error: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AgentLog]:
    """
    Agent 로그 목록 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID로 필터링
        phase: 특정 단계로 필터링
        step: 특정 스텝으로 필터링
        has_error: 오류 발생 여부로 필터링
        skip: 건너뛸 항목 수
        limit: 최대 반환 항목 수
    
    Returns:
        Agent 로그 목록
    """
    query = db.query(DBAgentLog)
    
    if session_id:
        query = query.filter(DBAgentLog.session_id == session_id)
    
    if phase:
        if isinstance(phase, str):
            phase = AgentPhaseEnum[phase]
        query = query.filter(DBAgentLog.phase == phase)
    
    if step is not None:
        query = query.filter(DBAgentLog.step == step)
    
    if has_error is not None:
        if has_error:
            query = query.filter(DBAgentLog.error.isnot(None))
        else:
            query = query.filter(DBAgentLog.error.is_(None))
    
    query = query.order_by(DBAgentLog.timestamp.asc())
    
    return query.offset(skip).limit(limit).all()


def create_agent_log(
    db: Session,
    log: AgentLog
) -> AgentLog:
    """
    새 Agent 로그 생성
    
    Args:
        db: 데이터베이스 세션
        log: 생성할 로그 정보
    
    Returns:
        생성된 Agent 로그
    """
    # 세션 확인 및 업데이트
    db_session = db.query(DBAgentSession).filter(DBAgentSession.session_id == log.session_id).first()
    
    if db_session:
        # 총 스텝 수 업데이트
        if log.step > db_session.total_steps:
            db_session.total_steps = log.step
    else:
        # 세션이 없으면 자동으로 생성
        db_session = DBAgentSession(
            session_id=log.session_id,
            agent_type=log.agent_type,
            start_time=datetime.utcnow(),
            status="running"
        )
        db.add(db_session)
    
    # 로그 생성
    db_log = DBAgentLog(
        session_id=log.session_id,
        step=log.step,
        phase=AgentPhaseEnum[log.phase],
        timestamp=log.timestamp or datetime.utcnow(),
        input_data=log.input_data,
        output_data=log.output_data,
        tool_calls=log.tool_calls,
        error=log.error
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log