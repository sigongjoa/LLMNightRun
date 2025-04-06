from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database.connection import get_db
from backend.services.export_service import ExportService, ExportFormat, ExportOptions


router = APIRouter(
    prefix="/export",
    tags=["export"],
    responses={404: {"description": "리소스를 찾을 수 없음"}},
)


@router.get("/question/{question_id}")
async def export_question(
    question_id: int,
    format: str = Query(ExportFormat.MARKDOWN, description="내보내기 형식"),
    include_metadata: bool = Query(True, description="메타데이터 포함 여부"),
    include_tags: bool = Query(True, description="태그 포함 여부"),
    include_timestamps: bool = Query(True, description="타임스탬프 포함 여부"),
    include_llm_info: bool = Query(True, description="LLM 정보 포함 여부"),
    code_highlighting: bool = Query(True, description="코드 하이라이팅 여부"),
    db: Session = Depends(get_db)
):
    """
    질문과 관련된 모든 응답 및 코드 스니펫을 내보냅니다.
    
    Args:
        question_id: 질문 ID
        format: 내보내기 형식 (markdown, json, html, pdf, code_package)
        include_metadata: 메타데이터 포함 여부
        include_tags: 태그 포함 여부
        include_timestamps: 타임스탬프 포함 여부
        include_llm_info: LLM 정보 포함 여부
        code_highlighting: 코드 하이라이팅 여부
        db: 데이터베이스 세션
        
    Returns:
        형식에 맞는 내보내기 파일
    """
    try:
        # 내보내기 옵션 설정
        options = ExportOptions(
            include_metadata=include_metadata,
            include_tags=include_tags,
            include_timestamps=include_timestamps,
            include_llm_info=include_llm_info,
            code_highlighting=code_highlighting
        )
        
        # 내보내기 서비스 초기화
        export_service = ExportService(db)
        
        # 내보내기 실행
        result = await export_service.export_question(question_id, format, options)
        
        # 결과 반환
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내보내기 오류: {str(e)}")


@router.get("/code-snippet/{snippet_id}")
async def export_code_snippet(
    snippet_id: int,
    format: str = Query(ExportFormat.CODE_PACKAGE, description="내보내기 형식"),
    include_metadata: bool = Query(True, description="메타데이터 포함 여부"),
    include_tags: bool = Query(True, description="태그 포함 여부"),
    include_timestamps: bool = Query(True, description="타임스탬프 포함 여부"),
    include_llm_info: bool = Query(True, description="LLM 정보 포함 여부"),
    db: Session = Depends(get_db)
):
    """
    특정 코드 스니펫을 내보냅니다.
    
    Args:
        snippet_id: 코드 스니펫 ID
        format: 내보내기 형식 (markdown, json, code_package)
        include_metadata: 메타데이터 포함 여부
        include_tags: 태그 포함 여부
        include_timestamps: 타임스탬프 포함 여부
        include_llm_info: LLM 정보 포함 여부
        db: 데이터베이스 세션
        
    Returns:
        형식에 맞는 내보내기 파일
    """
    try:
        # 내보내기 옵션 설정
        options = ExportOptions(
            include_metadata=include_metadata,
            include_tags=include_tags,
            include_timestamps=include_timestamps,
            include_llm_info=include_llm_info
        )
        
        # 내보내기 서비스 초기화
        export_service = ExportService(db)
        
        # 내보내기 실행
        result = await export_service.export_code_snippet(snippet_id, format, options)
        
        # 결과 반환
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내보내기 오류: {str(e)}")


@router.get("/agent-logs/{session_id}")
async def export_agent_logs(
    session_id: str,
    format: str = Query(ExportFormat.JSON, description="내보내기 형식"),
    include_timestamps: bool = Query(True, description="타임스탬프 포함 여부"),
    db: Session = Depends(get_db)
):
    """
    Agent 실행 로그를 내보냅니다.
    
    Args:
        session_id: Agent 세션 ID
        format: 내보내기 형식 (json, markdown, html)
        include_timestamps: 타임스탬프 포함 여부
        db: 데이터베이스 세션
        
    Returns:
        형식에 맞는 내보내기 파일
    """
    try:
        # 내보내기 옵션 설정
        options = ExportOptions(
            include_timestamps=include_timestamps
        )
        
        # 내보내기 서비스 초기화
        export_service = ExportService(db)
        
        # 내보내기 실행
        result = await export_service.export_agent_logs(session_id, format, options)
        
        # 결과 반환
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내보내기 오류: {str(e)}")


@router.post("/batch")
async def export_batch(
    item_ids: List[dict],
    format: str = Query(ExportFormat.MARKDOWN, description="내보내기 형식"),
    include_metadata: bool = Query(True, description="메타데이터 포함 여부"),
    include_tags: bool = Query(True, description="태그 포함 여부"),
    include_timestamps: bool = Query(True, description="타임스탬프 포함 여부"),
    include_llm_info: bool = Query(True, description="LLM 정보 포함 여부"),
    db: Session = Depends(get_db)
):
    """
    여러 항목을 일괄 내보내기합니다.
    
    요청 형식:
    ```
    [
        {"type": "question", "id": 1},
        {"type": "code_snippet", "id": 2},
        {"type": "agent_logs", "id": "session_xyz"}
    ]
    ```
    
    Args:
        item_ids: 내보낼 항목 목록
        format: 내보내기 형식
        include_metadata: 메타데이터 포함 여부
        include_tags: 태그 포함 여부
        include_timestamps: 타임스탬프 포함 여부
        include_llm_info: LLM 정보 포함 여부
        db: 데이터베이스 세션
        
    Returns:
        zip 파일 형태로 모든 내보내기 항목을 포함
    """
    try:
        import zipfile
        from io import BytesIO
        
        # 내보내기 옵션 설정
        options = ExportOptions(
            include_metadata=include_metadata,
            include_tags=include_tags,
            include_timestamps=include_timestamps,
            include_llm_info=include_llm_info
        )
        
        # 내보내기 서비스 초기화
        export_service = ExportService(db)
        
        # ZIP 파일 준비
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 각 항목 내보내기
            for item in item_ids:
                item_type = item.get("type")
                item_id = item.get("id")
                
                if not item_type or not item_id:
                    continue
                
                if item_type == "question":
                    result = await export_service.export_question(item_id, format, options)
                elif item_type == "code_snippet":
                    result = await export_service.export_code_snippet(item_id, format, options)
                elif item_type == "agent_logs":
                    result = await export_service.export_agent_logs(item_id, format, options)
                else:
                    continue
                
                # ZIP 파일에 추가
                zip_file.writestr(result["filename"], result["content"])
        
        zip_buffer.seek(0)
        
        # 결과 반환
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"batch_export_{timestamp}.zip"
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일괄 내보내기 오류: {str(e)}")