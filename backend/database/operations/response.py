"""
응답 관련 데이터베이스 작업 모듈
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import Response, LLMTypeEnum


def get_responses(db: Session, response_id: Optional[int] = None, question_id: Optional[int] = None, 
                llm_type: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    응답 목록 또는 단일 응답을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        response_id: 응답 ID (선택 사항)
        question_id: 질문 ID (선택 사항)
        llm_type: LLM 유형 (선택 사항)
        skip: 건너뛸 결과 수
        limit: 최대 결과 수
        
    Returns:
        응답 목록 또는 단일 응답
    """
    query = db.query(Response)
    
    if response_id:
        return query.filter(Response.id == response_id).first()
    
    if question_id:
        query = query.filter(Response.question_id == question_id)
    
    if llm_type:
        try:
            llm_type_enum = LLMTypeEnum[llm_type]
            query = query.filter(Response.llm_type == llm_type_enum)
        except KeyError:
            # 유효하지 않은 LLM 유형은 무시
            pass
    
    return query.offset(skip).limit(limit).all()


def create_response(db: Session, question_id: int, llm_type: str, content: str, project_id: Optional[int] = None) -> Response:
    """
    새 응답을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        question_id: 질문 ID
        llm_type: LLM 유형
        content: 응답 내용
        project_id: 프로젝트 ID (선택 사항)
        
    Returns:
        생성된 응답
    """
    try:
        llm_type_enum = LLMTypeEnum[llm_type]
    except KeyError:
        llm_type_enum = LLMTypeEnum.manual
    
    response = Response(
        question_id=question_id,
        llm_type=llm_type_enum,
        content=content,
        project_id=project_id
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    return response


def update_response(db: Session, response_id: int, response_data: Dict[str, Any]) -> Optional[Response]:
    """
    응답을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        response_id: 응답 ID
        response_data: 업데이트할 응답 데이터
        
    Returns:
        업데이트된 응답 또는 None
    """
    response = db.query(Response).filter(Response.id == response_id).first()
    
    if not response:
        return None
    
    for key, value in response_data.items():
        if hasattr(response, key) and value is not None:
            if key == 'llm_type' and isinstance(value, str):
                try:
                    value = LLMTypeEnum[value]
                except KeyError:
                    continue
            setattr(response, key, value)
    
    db.commit()
    db.refresh(response)
    
    return response


def delete_response(db: Session, response_id: int) -> bool:
    """
    응답을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        response_id: 응답 ID
        
    Returns:
        삭제 성공 여부
    """
    response = db.query(Response).filter(Response.id == response_id).first()
    
    if not response:
        return False
    
    db.delete(response)
    db.commit()
    
    return True
