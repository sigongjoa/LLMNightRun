"""
질문 API 라우터 모듈 (수정된 버전)

기존 코드에서 project_id 컬럼 관련 문제를 해결하기 위한 임시 모듈입니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from ..database.connection import get_db
from ..database.operations.question_fix import (
    get_questions, create_question, update_question, 
    delete_question, search_questions
)
from ..models.question import Question, QuestionCreate, QuestionResponse

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/questions",
    tags=["questions"],
    responses={
        404: {"description": "질문을 찾을 수 없음"},
        500: {"description": "서버 내부 오류"}
    },
)


@router.post("/", response_model=QuestionResponse)
async def submit_question(
    question: QuestionCreate, 
    db: Session = Depends(get_db)
) -> QuestionResponse:
    """
    새로운 질문을 데이터베이스에 저장합니다.
    
    Args:
        question: 질문 내용 및 태그
        db: 데이터베이스 세션
        
    Returns:
        QuestionResponse: 생성된 질문 정보
        
    Raises:
        HTTPException: 질문 생성 중 오류 발생 시
    """
    try:
        return create_question(db, question)
    except Exception as e:
        logger.error(f"질문 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 생성 실패: {str(e)}")


@router.get("/", response_model=List[QuestionResponse])
async def list_questions(
    skip: int = 0, 
    limit: int = 100, 
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[QuestionResponse]:
    """
    질문 목록을 페이지네이션과 필터링 옵션으로 조회합니다.
    
    Args:
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        tag: 필터링할 태그 (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        List[QuestionResponse]: 질문 목록
        
    Raises:
        HTTPException: 질문 목록 조회 중 오류 발생 시
    """
    try:
        return get_questions(db, tag=tag, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"질문 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 목록 조회 실패: {str(e)}")


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int, 
    db: Session = Depends(get_db)
) -> QuestionResponse:
    """
    특정 ID의 질문을 조회합니다.
    
    Args:
        question_id: 질문 ID
        db: 데이터베이스 세션
        
    Returns:
        QuestionResponse: 질문 정보
        
    Raises:
        HTTPException: 질문을 찾을 수 없거나 조회 중 오류 발생 시
    """
    try:
        question = get_questions(db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"질문 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 조회 실패: {str(e)}")


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question_endpoint(
    question_id: int, 
    question: Question, 
    db: Session = Depends(get_db)
) -> QuestionResponse:
    """
    특정 ID의 질문을 업데이트합니다.
    
    Args:
        question_id: 질문 ID
        question: 업데이트할 질문 정보
        db: 데이터베이스 세션
        
    Returns:
        QuestionResponse: 업데이트된 질문 정보
        
    Raises:
        HTTPException: 질문을 찾을 수 없거나 업데이트 중 오류 발생 시
    """
    try:
        updated_question = update_question(db, question_id, question)
        if not updated_question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        return updated_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"질문 업데이트 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 업데이트 실패: {str(e)}")


@router.delete("/{question_id}")
async def delete_question_endpoint(
    question_id: int, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 ID의 질문을 삭제합니다.
    
    Args:
        question_id: 질문 ID
        db: 데이터베이스 세션
        
    Returns:
        Dict[str, Any]: 삭제 성공 메시지
        
    Raises:
        HTTPException: 질문을 찾을 수 없거나 삭제 중 오류 발생 시
    """
    try:
        success = delete_question(db, question_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        return {"success": True, "message": f"질문 ID {question_id}가 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"질문 삭제 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 삭제 실패: {str(e)}")


@router.get("/search/", response_model=List[QuestionResponse])
async def search_questions_endpoint(
    query: str = Query(..., min_length=2, description="검색어"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[QuestionResponse]:
    """
    질문을 검색어를 기준으로 검색합니다.
    
    Args:
        query: 검색어 (최소 2글자)
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        db: 데이터베이스 세션
        
    Returns:
        List[QuestionResponse]: 검색된 질문 목록
        
    Raises:
        HTTPException: 검색 중 오류 발생 시
    """
    try:
        return search_questions(db, query, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"질문 검색 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 검색 실패: {str(e)}")
