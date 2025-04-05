"""
응답 API 라우터 모듈

LLM 응답 관련 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..database.connection import get_db
from ..database.operations.respone import get_responses, create_response, update_response, delete_response
from ..models.response import Response, ResponseCreate, ResponseResponse
from ..models.enums import LLMType
from ..services.llm_service import LLMService

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/responses",
    tags=["responses"],
    responses={404: {"description": "찾을 수 없음"}},
)


@router.post("/", response_model=ResponseResponse)
async def create_response_endpoint(
    response: ResponseCreate, 
    db: Session = Depends(get_db)
):
    """
    새로운 응답을 생성합니다.
    
    Args:
        response: 응답 내용 및 관련 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 응답 정보
    """
    try:
        # 응답 생성
        db_response = create_response(db, response)
        return db_response
    except Exception as e:
        logger.error(f"응답 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")


@router.get("/", response_model=List[ResponseResponse])
async def list_responses(
    question_id: Optional[int] = None,
    llm_type: Optional[LLMType] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    응답 목록을 조회합니다.
    
    Args:
        question_id: 질문 ID로 필터링 (선택 사항)
        llm_type: LLM 유형으로 필터링 (선택 사항)
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        db: 데이터베이스 세션
        
    Returns:
        응답 목록
    """
    try:
        responses = get_responses(
            db, 
            question_id=question_id, 
            llm_type=llm_type,
            skip=skip, 
            limit=limit
        )
        return responses
    except Exception as e:
        logger.error(f"응답 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 목록 조회 실패: {str(e)}")


@router.get("/{response_id}", response_model=ResponseResponse)
async def get_response_by_id(
    response_id: int, 
    db: Session = Depends(get_db)
):
    """
    특정 응답을 조회합니다.
    
    Args:
        response_id: 응답 ID
        db: 데이터베이스 세션
        
    Returns:
        응답 정보
        
    Raises:
        HTTPException: 응답을 찾을 수 없는 경우
    """
    try:
        response = get_responses(db, response_id=response_id)
        if not response or len(response) == 0:
            raise HTTPException(status_code=404, detail=f"응답 ID {response_id}를 찾을 수 없습니다")
        return response[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"응답 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 조회 실패: {str(e)}")


@router.put("/{response_id}", response_model=ResponseResponse)
async def update_response_endpoint(
    response_id: int, 
    response: Response, 
    db: Session = Depends(get_db)
):
    """
    응답을 업데이트합니다.
    
    Args:
        response_id: 응답 ID
        response: 업데이트할 응답 정보
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 응답 정보
        
    Raises:
        HTTPException: 응답을 찾을 수 없는 경우
    """
    try:
        updated_response = update_response(db, response_id, response)
        if not updated_response:
            raise HTTPException(status_code=404, detail=f"응답 ID {response_id}를 찾을 수 없습니다")
        return updated_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"응답 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 업데이트 실패: {str(e)}")


@router.delete("/{response_id}")
async def delete_response_endpoint(
    response_id: int, 
    db: Session = Depends(get_db)
):
    """
    응답을 삭제합니다.
    
    Args:
        response_id: 응답 ID
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException: 응답을 찾을 수 없는 경우
    """
    try:
        success = delete_response(db, response_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"응답 ID {response_id}를 찾을 수 없습니다")
        return {"success": True, "message": f"응답 ID {response_id}가 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"응답 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응답 삭제 실패: {str(e)}")


@router.post("/ask/{llm_type}")
async def ask_llm(
    llm_type: LLMType,
    question: ResponseCreate,
    db: Session = Depends(get_db)
):
    """
    LLM에 질문을 요청하고 응답을 저장합니다.
    
    Args:
        llm_type: LLM 유형 (openai_api, claude_api 등)
        question: 질문 내용
        db: 데이터베이스 세션
        
    Returns:
        질문 및 LLM의 응답
    """
    try:
        # LLM 서비스 초기화
        llm_service = LLMService()
        
        # LLM에 질문 요청
        content = await llm_service.get_response(llm_type, question.content)
        
        # 응답 생성 및 저장
        response_data = {
            "question_id": question.question_id,
            "llm_type": llm_type,
            "content": content
        }
        
        db_response = create_response(db, response_data)
        
        # 결과 반환
        return {
            "question_id": question.question_id,
            "response": db_response
        }
    except Exception as e:
        logger.error(f"LLM 요청 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 요청 실패: {str(e)}")