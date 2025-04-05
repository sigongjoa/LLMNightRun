"""
질문 관련 데이터베이스 작업 모듈

질문 데이터에 대한 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any

from ..models import Question as DBQuestion
from ...models.question import Question, QuestionCreate


def get_questions(
    db: Session, 
    question_id: Optional[int] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100,
    single: bool = False
) -> Union[List[Question], Question, None]:
    """
    질문을 조회하는 함수
    
    Args:
        db: 데이터베이스 세션
        question_id: 조회할 질문 ID (지정 시 해당 질문만 조회)
        tag: 특정 태그로 필터링
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        single: 단일 항목만 반환할지 여부
        
    Returns:
        질문 목록 또는 단일 질문 객체
    """
    query = db.query(DBQuestion)
    
    if question_id:
        query = query.filter(DBQuestion.id == question_id)
        if single:
            return query.first()
    
    if tag:
        # JSON 필드에서 태그 검색 (데이터베이스에 따라 구현이 달라질 수 있음)
        # SQLite용 임시 구현 (실제 환경에서는 데이터베이스에 맞게 조정 필요)
        query = query.filter(DBQuestion.tags.like(f'%{tag}%'))
    
    return query.offset(skip).limit(limit).all()


def create_question(db: Session, question: Union[Question, QuestionCreate, Dict[str, Any]]) -> Question:
    """
    새 질문을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        question: 생성할 질문 데이터
        
    Returns:
        생성된 질문 객체
    """
    # 딕셔너리인 경우 처리
    if isinstance(question, dict):
        question_data = question
    else:
        question_data = question.dict()
    
    # ID 제거 (자동 생성)
    if "id" in question_data:
        del question_data["id"]
    
    # 생성/수정 시간 제거 (자동 설정)
    if "created_at" in question_data:
        del question_data["created_at"]
    if "updated_at" in question_data:
        del question_data["updated_at"]
    
    # 데이터베이스 모델 생성
    db_question = DBQuestion(**question_data)
    
    # 데이터베이스에 저장
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return db_question


def update_question(
    db: Session, 
    question_id: int, 
    question_data: Union[Question, Dict[str, Any]]
) -> Optional[Question]:
    """
    질문을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        question_id: 업데이트할 질문 ID
        question_data: 업데이트할 데이터
        
    Returns:
        업데이트된 질문 객체 또는 None (존재하지 않는 경우)
    """
    # 질문 조회
    db_question = db.query(DBQuestion).filter(DBQuestion.id == question_id).first()
    if not db_question:
        return None
    
    # 딕셔너리로 변환
    if not isinstance(question_data, dict):
        question_data = question_data.dict(exclude_unset=True)
    
    # 업데이트할 필드 설정
    for key, value in question_data.items():
        if hasattr(db_question, key):
            setattr(db_question, key, value)
    
    # 변경사항 저장
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
        성공 여부
    """
    db_question = db.query(DBQuestion).filter(DBQuestion.id == question_id).first()
    if not db_question:
        return False
    
    db.delete(db_question)
    db.commit()
    
    return True


def search_questions(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 100
) -> List[Question]:
    """
    질문을 검색하는 함수
    
    Args:
        db: 데이터베이스 세션
        query: 검색 쿼리
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        
    Returns:
        검색 결과 질문 목록
    """
    # 단순 텍스트 검색 구현 (실제로는 전문 검색 엔진 사용 권장)
    db_questions = db.query(DBQuestion).filter(
        DBQuestion.content.ilike(f"%{query}%")
    ).offset(skip).limit(limit).all()
    
    return db_questions