"""
문서 관리 API 모듈

이 모듈은 문서 관리 관련 API 엔드포인트를 제공합니다.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status
from fastapi.responses import JSONResponse

from ..models.document import (
    Document, DocumentCreateRequest, DocumentUpdateRequest, 
    DocumentGenerateRequest, DocumentPublishRequest,
    DocumentResponse, DocumentListResponse, DocumentType, DocumentStatus
)
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)


# 문서 서비스 의존성
def get_document_service():
    return DocumentService()


# GitHub 서비스 의존성
def get_github_service():
    return GitHubService()


@router.get("/types", response_model=Dict[str, str])
async def get_document_types():
    """
    사용 가능한 문서 유형 목록 조회
    """
    return {t.name: t.value for t in DocumentType}


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    document_type: Optional[str] = Query(None, description="문서 유형 필터"),
    status: Optional[str] = Query(None, description="문서 상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    문서 목록 조회
    """
    try:
        # 문서 유형 필터 변환
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType(document_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 문서 유형: {document_type}"
                )
        
        # 문서 상태 필터 변환
        doc_status = None
        if status:
            try:
                doc_status = DocumentStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 문서 상태: {status}"
                )
        
        # 문서 목록 조회
        documents, total = document_service.list_documents(
            document_type=doc_type,
            status=doc_status,
            page=page,
            page_size=page_size
        )
        
        # 응답 구성
        return DocumentListResponse(
            documents=[DocumentResponse(**doc.dict()) for doc in documents],
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"문서 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="문서 ID"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    특정 문서 조회
    """
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"ID가 {document_id}인 문서를 찾을 수 없습니다."
            )
        return DocumentResponse(**document.dict())
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"문서 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreateRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    새 문서 생성
    """
    try:
        # 문서 생성
        document = Document(
            id=f"doc_{uuid.uuid4().hex[:8]}",
            type=request.type,
            title=request.title,
            content=request.content or "",
            status=request.status,
            github_path=request.github_path,
            doc_info=request.metadata,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        created_document = document_service.create_document(document)
        return DocumentResponse(**created_document.dict())
    
    except Exception as e:
        logger.error(f"문서 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str = Path(..., description="문서 ID"),
    request: DocumentUpdateRequest = Body(...),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    기존 문서 업데이트
    """
    try:
        # 문서 존재 여부 확인
        existing_document = document_service.get_document(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=404,
                detail=f"ID가 {document_id}인 문서를 찾을 수 없습니다."
            )
        
        # 업데이트할 필드 적용
        update_data = request.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        # 문서 업데이트
        updated_document = document_service.update_document(document_id, update_data)
        return DocumentResponse(**updated_document.dict())
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"문서 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str = Path(..., description="문서 ID"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    문서 삭제
    """
    try:
        # 문서 존재 여부 확인
        existing_document = document_service.get_document(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=404,
                detail=f"ID가 {document_id}인 문서를 찾을 수 없습니다."
            )
        
        # 문서 삭제
        document_service.delete_document(document_id)
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/generate", response_model=DocumentResponse)
async def generate_document(
    request: DocumentGenerateRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    LLM을 사용하여 문서 자동 생성
    """
    try:
        # 문서 생성
        document = document_service.generate_document(
            doc_type=request.type,
            force_regenerate=request.force_regenerate,
            custom_params=request.custom_params
        )
        return DocumentResponse(**document.dict())
    
    except Exception as e:
        logger.error(f"문서 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/publish", response_model=Dict[str, Any])
async def publish_documents(
    request: DocumentPublishRequest,
    document_service: DocumentService = Depends(get_document_service),
    github_service: GitHubService = Depends(get_github_service)
):
    """
    문서를 GitHub에 게시
    """
    try:
        # GitHub 설정 확인
        if not github_service.is_github_configured():
            raise HTTPException(
                status_code=400,
                detail="GitHub 설정이 구성되지 않았습니다. 먼저 GitHub 설정을 구성해주세요."
            )
        
        # 문서 ID 유효성 확인
        for doc_id in request.document_ids:
            if not document_service.get_document(doc_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"ID가 {doc_id}인 문서를 찾을 수 없습니다."
                )
        
        # 문서 게시
        result = github_service.publish_documents(
            document_ids=request.document_ids,
            commit_message=request.commit_message,
            auto_message=request.auto_message,
            branch_name=request.branch_name,
            create_pr=request.create_pr,
            pr_title=request.pr_title,
            pr_description=request.pr_description
        )
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"문서 게시 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 게시 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/preview/{document_type}", response_model=Dict[str, Any])
async def preview_document(
    document_type: str = Path(..., description="문서 유형"),
    custom_params: Dict[str, Any] = Body({}, embed=True),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    문서 미리보기 생성 (저장하지 않음)
    """
    try:
        # 문서 유형 확인
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 문서 유형: {document_type}"
            )
        
        # 문서 미리보기 생성
        preview_content = document_service.preview_document(
            doc_type=doc_type,
            custom_params=custom_params
        )
        
        return {
            "type": doc_type.value,
            "content": preview_content
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"문서 미리보기 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 미리보기 생성 중 오류가 발생했습니다: {str(e)}"
        )
