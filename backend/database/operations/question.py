"""
질문 관련 데이터베이스 작업 모듈
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import Question


def get_questions(db: Session, question_id: Optional[int] = None, skip: int = 0, limit: int = 100, single: bool = False):
    """
    질문 목록 또는 단일 질문을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        question_id: 질문 ID (선택 사항)
        skip: 건너뛸 결과 수
        limit: 최대 결과 수
        single: 단일 결과 반환 여부
        
    Returns:
        단일 질문 또는 질문 목록
    """
    if question_id:
        query = db.query(Question).filter(Question.id == question_id)
        return query.first() if single else query.all()
    
    return db.query(Question).offset(skip).limit(limit).all()


def create_question(db: Session, content: str, tags: Optional[List[str]] = None, project_id: Optional[int] = None) -> Question:
    """
    새 질문을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        content: 질문 내용
        tags: 태그 목록 (선택 사항)
        project_id: 프로젝트 ID (선택 사항)
        
    Returns:
        생성된 질문
    """
    tags = tags or []
    
    question = Question(
        content=content,
        tags=tags,
        project_id=project_id
    )
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question


def update_question(db: Session, question_id: int, question_data: Dict[str, Any]) -> Optional[Question]:
    """
    질문을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        question_id: 질문 ID
        question_data: 업데이트할 질문 데이터
        
    Returns:
        업데이트된 질문 또는 None
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        return None
    
    for key, value in question_data.items():
        if hasattr(question, key) and value is not None:
            setattr(question, key, value)
    
    db.commit()
    db.refresh(question)
    
    return question


def delete_question(db: Session, question_id: int) -> bool:
    """
    질문을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        question_id: 질문 ID
        
    Returns:
        삭제 성공 여부
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        return False
    
    db.delete(question)
    db.commit()
    
    return True
