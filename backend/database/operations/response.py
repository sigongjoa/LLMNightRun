"""
응답 관련 데이터베이스 작업 모듈

LLM 응답 데이터에 대한 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any

from ..models import Response as DBResponse, LLMTypeEnum
from ...models.response import Response, ResponseCreate
from ...models.enums import LLMType


def get_responses(
    db: Session, 
    response_id: Optional[int] = None,
    question_id: Optional[int] = None,
    llm_type: Optional[LLMType] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Response]:
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
    query = db.query(DBResponse)
    
    if response_id:
        query = query.filter(DBResponse.id == response_id)
    
    if question_id:
        query = query.filter(DBResponse.question_id == question_id)
    
    if llm_type:
        # Enum 변환
        db_llm_type = LLMTypeEnum[llm_type.value]
        query = query.filter(DBResponse.llm_type == db_llm_type)
    
    return query.offset(skip).limit(limit).all()


def create_response(db: Session, response: Union[Response, ResponseCreate, Dict[str, Any]]) -> Response:
    """
    새 응답을 생성하는 함수
    
    Args:
        db: 데이터베이스 세션
        response: 생성할 응답 데이터
        
    Returns:
        생성된 응답 객체
    """
    # 딕셔너리인 경우 처리
    if isinstance(response, dict):
        response_data = response
    else:
        response_data = response.dict()
    
    # ID 제거 (자동 생성)
    if "id" in response_data:
        del response_data["id"]
    
    # 생성 시간 및 업데이트 시간 필드 제거
    if "created_at" in response_data:
        del response_data["created_at"]
    if "updated_at" in response_data:
        del response_data["updated_at"]
    
    # LLM 타입 처리 (문자열 -> Enum)
    if "llm_type" in response_data and not isinstance(response_data["llm_type"], LLMTypeEnum):
        llm_type = response_data["llm_type"]
        if isinstance(llm_type, LLMType):
            response_data["llm_type"] = LLMTypeEnum[llm_type.value]
        else:
            response_data["llm_type"] = LLMTypeEnum[llm_type]
    
    # 데이터베이스 모델 생성
    db_response = DBResponse(**response_data)
    
    # 데이터베이스에 저장
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return db_response


def update_response(
    db: Session, 
    response_id: int, 
    response_data: Union[Response, Dict[str, Any]]
) -> Optional[Response]:
    """
    응답을 업데이트하는 함수
    
    Args:
        db: 데이터베이스 세션
        response_id: 업데이트할 응답 ID
        response_data: 업데이트할 데이터
        
    Returns:
        업데이트된 응답 객체 또는 None (존재하지 않는 경우)
    """
    # 응답 조회
    db_response = db.query(DBResponse).filter(DBResponse.id == response_id).first()
    if not db_response:
        return None
    
    # 딕셔너리로 변환
    if not isinstance(response_data, dict):
        response_data = response_data.dict(exclude_unset=True)
    
    # LLM 타입 처리 (문자열 -> Enum)
    if "llm_type" in response_data and not isinstance(response_data["llm_type"], LLMTypeEnum):
        llm_type = response_data["llm_type"]
        if isinstance(llm_type, LLMType):
            response_data["llm_type"] = LLMTypeEnum[llm_type.value]
        else:
            response_data["llm_type"] = LLMTypeEnum[llm_type]
    
    # 업데이트할 필드 설정
    for key, value in response_data.items():
        if hasattr(db_response, key):
            setattr(db_response, key, value)
    
    # 변경사항 저장
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
        성공 여부
    """
    db_response = db.query(DBResponse).filter(DBResponse.id == response_id).first()
    if not db_response:
        return False
    
    db.delete(db_response)
    db.commit()
    
    return True