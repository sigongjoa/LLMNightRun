"""
코드 API 라우터 모듈

코드 스니펫과 템플릿 관련 엔드포인트를 정의합니다.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.connection import get_db
from ..database.operations.code import (
    get_code_snippets, create_code_snippet, update_code_snippet, delete_code_snippet,
    get_code_templates, create_code_template, update_code_template, delete_code_template
)
from ..models.code import (
    CodeSnippet, CodeSnippetCreate, CodeSnippetResponse,
    CodeTemplate, CodeTemplateCreate, CodeTemplateResponse
)
from ..models.enums import CodeLanguage
from ..services.code_service import CodeService

# 로거 설정
logger = logging.getLogger(__name__)

# 코드 스니펫 라우터 생성
router = APIRouter(
    prefix="/code-snippets",
    tags=["code"],
    responses={404: {"description": "찾을 수 없음"}},
)

# 코드 템플릿 라우터 생성
template_router = APIRouter(
    prefix="/code-templates",
    tags=["code"],
    responses={404: {"description": "찾을 수 없음"}},
)

# 메인 라우터에 템플릿 라우터 포함
router.include_router(template_router)


# 코드 스니펫 엔드포인트
@router.post("/", response_model=CodeSnippetResponse)
async def create_snippet(
    snippet: CodeSnippetCreate, 
    db: Session = Depends(get_db)
):
    """
    새로운 코드 스니펫을 생성합니다.
    
    Args:
        snippet: 생성할 코드 스니펫 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 코드 스니펫 정보
    """
    try:
        code_service = CodeService(db)
        return code_service.create_snippet(snippet)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 생성 실패: {str(e)}")


@router.get("/", response_model=List[CodeSnippetResponse])
async def list_snippets(
    question_id: Optional[int] = None,
    response_id: Optional[int] = None,
    language: Optional[CodeLanguage] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    코드 스니펫 목록을 조회합니다.
    
    Args:
        question_id: 질문 ID로 필터링 (선택 사항)
        response_id: 응답 ID로 필터링 (선택 사항)
        language: 언어로 필터링 (선택 사항)
        tag: 태그로 필터링 (선택 사항)
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        db: 데이터베이스 세션
        
    Returns:
        코드 스니펫 목록
    """
    try:
        code_service = CodeService(db)
        return code_service.get_snippets(
            question_id=question_id,
            response_id=response_id,
            language=language,
            tag=tag,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"코드 스니펫 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 목록 조회 실패: {str(e)}")


@router.get("/{snippet_id}", response_model=CodeSnippetResponse)
async def get_snippet(
    snippet_id: int, 
    db: Session = Depends(get_db)
):
    """
    특정 코드 스니펫을 조회합니다.
    
    Args:
        snippet_id: 코드 스니펫 ID
        db: 데이터베이스 세션
        
    Returns:
        코드 스니펫 정보
        
    Raises:
        HTTPException: 코드 스니펫을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        snippet = code_service.get_snippet(snippet_id)
        
        if not snippet:
            raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
        
        return snippet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 조회 실패: {str(e)}")


@router.put("/{snippet_id}", response_model=CodeSnippetResponse)
async def update_snippet(
    snippet_id: int, 
    snippet: CodeSnippet, 
    db: Session = Depends(get_db)
):
    """
    코드 스니펫을 업데이트합니다.
    
    Args:
        snippet_id: 코드 스니펫 ID
        snippet: 업데이트할 코드 스니펫 정보
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 코드 스니펫 정보
        
    Raises:
        HTTPException: 코드 스니펫을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        updated_snippet = code_service.update_snippet(snippet_id, snippet)
        
        if not updated_snippet:
            raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
        
        return updated_snippet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 업데이트 실패: {str(e)}")


@router.delete("/{snippet_id}")
async def delete_snippet(
    snippet_id: int, 
    db: Session = Depends(get_db)
):
    """
    코드 스니펫을 삭제합니다.
    
    Args:
        snippet_id: 코드 스니펫 ID
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException: 코드 스니펫을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        success = code_service.delete_snippet(snippet_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
        
        return {"success": True, "message": f"코드 스니펫 ID {snippet_id}가 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 삭제 실패: {str(e)}")


@router.get("/{snippet_id}/export")
async def export_snippet(
    snippet_id: int,
    format: str = Query("raw", description="내보내기 형식 (raw, markdown, html)"),
    db: Session = Depends(get_db)
):
    """
    코드 스니펫을 파일로 내보냅니다.
    
    Args:
        snippet_id: 코드 스니펫 ID
        format: 내보내기 형식
        db: 데이터베이스 세션
        
    Returns:
        파일 내용
        
    Raises:
        HTTPException: 코드 스니펫을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        result = code_service.export_snippet_to_file(snippet_id, format)
        
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 내보내기 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 내보내기 실패: {str(e)}")


@router.post("/package")
async def package_snippets(
    snippet_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    여러 코드 스니펫을 ZIP 파일로 패키징합니다.
    
    Args:
        snippet_ids: 코드 스니펫 ID 목록
        db: 데이터베이스 세션
        
    Returns:
        ZIP 파일
        
    Raises:
        HTTPException: 코드 스니펫이 하나도 없는 경우
    """
    try:
        if not snippet_ids:
            raise HTTPException(status_code=400, detail="스니펫 ID가 제공되지 않았습니다")
        
        code_service = CodeService(db)
        zip_content = code_service.package_snippets(snippet_ids)
        
        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=code_snippets.zip"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 스니펫 패키징 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 스니펫 패키징 실패: {str(e)}")


# 코드 템플릿 엔드포인트
@template_router.post("/", response_model=CodeTemplateResponse)
async def create_template(
    template: CodeTemplateCreate, 
    db: Session = Depends(get_db)
):
    """
    새로운 코드 템플릿을 생성합니다.
    
    Args:
        template: 생성할 코드 템플릿 정보
        db: 데이터베이스 세션
        
    Returns:
        생성된 코드 템플릿 정보
    """
    try:
        code_service = CodeService(db)
        return code_service.create_template(template)
    except Exception as e:
        logger.error(f"코드 템플릿 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 템플릿 생성 실패: {str(e)}")


@template_router.get("/", response_model=List[CodeTemplateResponse])
async def list_templates(
    language: Optional[CodeLanguage] = None,
    tag: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    코드 템플릿 목록을 조회합니다.
    
    Args:
        language: 언어로 필터링 (선택 사항)
        tag: 태그로 필터링 (선택 사항)
        skip: 건너뛸 항목 수
        limit: 최대 조회 항목 수
        db: 데이터베이스 세션
        
    Returns:
        코드 템플릿 목록
    """
    try:
        code_service = CodeService(db)
        return code_service.get_templates(
            language=language,
            tag=tag,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"코드 템플릿 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 템플릿 목록 조회 실패: {str(e)}")


@template_router.get("/{template_id}", response_model=CodeTemplateResponse)
async def get_template(
    template_id: int, 
    db: Session = Depends(get_db)
):
    """
    특정 코드 템플릿을 조회합니다.
    
    Args:
        template_id: 코드 템플릿 ID
        db: 데이터베이스 세션
        
    Returns:
        코드 템플릿 정보
        
    Raises:
        HTTPException: 코드 템플릿을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        template = code_service.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"코드 템플릿 ID {template_id}를 찾을 수 없습니다")
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 템플릿 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 템플릿 조회 실패: {str(e)}")


@template_router.put("/{template_id}", response_model=CodeTemplateResponse)
async def update_template(
    template_id: int, 
    template: CodeTemplate, 
    db: Session = Depends(get_db)
):
    """
    코드 템플릿을 업데이트합니다.
    
    Args:
        template_id: 코드 템플릿 ID
        template: 업데이트할 코드 템플릿 정보
        db: 데이터베이스 세션
        
    Returns:
        업데이트된 코드 템플릿 정보
        
    Raises:
        HTTPException: 코드 템플릿을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        updated_template = code_service.update_template(template_id, template)
        
        if not updated_template:
            raise HTTPException(status_code=404, detail=f"코드 템플릿 ID {template_id}를 찾을 수 없습니다")
        
        return updated_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 템플릿 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 템플릿 업데이트 실패: {str(e)}")


@template_router.delete("/{template_id}")
async def delete_template(
    template_id: int, 
    db: Session = Depends(get_db)
):
    """
    코드 템플릿을 삭제합니다.
    
    Args:
        template_id: 코드 템플릿 ID
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException: 코드 템플릿을 찾을 수 없는 경우
    """
    try:
        code_service = CodeService(db)
        success = code_service.delete_template(template_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"코드 템플릿 ID {template_id}를 찾을 수 없습니다")
        
        return {"success": True, "message": f"코드 템플릿 ID {template_id}가 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 템플릿 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"코드 템플릿 삭제 실패: {str(e)}")