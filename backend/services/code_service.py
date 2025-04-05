"""
코드 서비스 모듈

코드 스니펫 및 템플릿 처리를 위한 서비스를 제공합니다.
"""

import os
import tempfile
import zipfile
import logging
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..database.operations.code import (
    get_code_snippets, create_code_snippet, update_code_snippet, delete_code_snippet,
    get_code_templates, create_code_template, update_code_template, delete_code_template
)
from ..models.code import (
    CodeSnippet, CodeSnippetCreate, CodeTemplate, CodeTemplateCreate
)
from ..models.enums import CodeLanguage

# 로거 설정
logger = logging.getLogger(__name__)


class CodeService:
    """코드 스니펫과 템플릿을 관리하는 서비스 클래스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
    
    # 코드 스니펫 관련 메서드
    def get_snippet(self, snippet_id: int) -> Optional[CodeSnippet]:
        """
        코드 스니펫을 조회합니다.
        
        Args:
            snippet_id: 코드 스니펫 ID
            
        Returns:
            코드 스니펫 또는 None (존재하지 않는 경우)
        """
        snippets = get_code_snippets(self.db, snippet_id=snippet_id)
        return snippets[0] if snippets else None
    
    def get_snippets(
        self, 
        question_id: Optional[int] = None,
        response_id: Optional[int] = None,
        language: Optional[CodeLanguage] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeSnippet]:
        """
        조건에 맞는 코드 스니펫 목록을 조회합니다.
        
        Args:
            question_id: 질문 ID로 필터링 (선택 사항)
            response_id: 응답 ID로 필터링 (선택 사항)
            language: 언어로 필터링 (선택 사항)
            tag: 태그로 필터링 (선택 사항)
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수
            
        Returns:
            코드 스니펫 목록
        """
        return get_code_snippets(
            self.db,
            question_id=question_id,
            response_id=response_id,
            language=language,
            tag=tag,
            skip=skip,
            limit=limit
        )
    
    def create_snippet(self, snippet: Union[CodeSnippetCreate, Dict[str, Any]]) -> CodeSnippet:
        """
        새 코드 스니펫을 생성합니다.
        
        Args:
            snippet: 생성할 코드 스니펫 정보
            
        Returns:
            생성된 코드 스니펫
        """
        try:
            return create_code_snippet(self.db, snippet)
        except Exception as e:
            logger.error(f"코드 스니펫 생성 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 스니펫 생성 실패: {str(e)}")
    
    def update_snippet(self, snippet_id: int, snippet: Union[CodeSnippet, Dict[str, Any]]) -> Optional[CodeSnippet]:
        """
        코드 스니펫을 업데이트합니다.
        
        Args:
            snippet_id: 코드 스니펫 ID
            snippet: 업데이트할 정보
            
        Returns:
            업데이트된 코드 스니펫 또는 None (존재하지 않는 경우)
        """
        try:
            return update_code_snippet(self.db, snippet_id, snippet)
        except Exception as e:
            logger.error(f"코드 스니펫 업데이트 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 스니펫 업데이트 실패: {str(e)}")
    
    def delete_snippet(self, snippet_id: int) -> bool:
        """
        코드 스니펫을 삭제합니다.
        
        Args:
            snippet_id: 코드 스니펫 ID
            
        Returns:
            성공 여부
        """
        try:
            return delete_code_snippet(self.db, snippet_id)
        except Exception as e:
            logger.error(f"코드 스니펫 삭제 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 스니펫 삭제 실패: {str(e)}")
    
    def export_snippet_to_file(self, snippet_id: int, format: str = "raw") -> Dict[str, Any]:
        """
        코드 스니펫을 파일로 내보냅니다.
        
        Args:
            snippet_id: 코드 스니펫 ID
            format: 내보내기 형식 (raw, markdown, html)
            
        Returns:
            파일 정보 및 내용
        """
        # 스니펫 조회
        snippet = self.get_snippet(snippet_id)
        if not snippet:
            raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
        
        # 파일 이름 생성
        extension_map = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "csharp": "cs",
            "cpp": "cpp",
            "go": "go",
            "rust": "rs",
            "php": "php",
            "ruby": "rb",
            "swift": "swift",
            "kotlin": "kt",
            "other": "txt"
        }
        
        language = snippet.language if isinstance(snippet.language, str) else snippet.language.value
        extension = extension_map.get(language.lower(), "txt")
        
        file_name = f"{snippet.title.replace(' ', '_').lower()}.{extension}"
        
        # 형식에 따라 내용 처리
        if format == "raw":
            content = snippet.content
            content_type = "text/plain"
        elif format == "markdown":
            content = f"# {snippet.title}\n\n"
            if snippet.description:
                content += f"{snippet.description}\n\n"
            content += f"```{language}\n{snippet.content}\n```\n"
            content_type = "text/markdown"
        elif format == "html":
            content = f"<html><head><title>{snippet.title}</title></head><body>\n"
            if snippet.description:
                content += f"<h2>{snippet.description}</h2>\n"
            content += f"<pre><code class=\"language-{language}\">{snippet.content}</code></pre>\n"
            content += "</body></html>"
            content_type = "text/html"
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {format}")
        
        return {
            "filename": file_name,
            "content": content,
            "content_type": content_type
        }
    
    def package_snippets(self, snippet_ids: List[int]) -> bytes:
        """
        여러 코드 스니펫을 ZIP 파일로 패키징합니다.
        
        Args:
            snippet_ids: 코드 스니펫 ID 목록
            
        Returns:
            ZIP 파일 바이트 데이터
        """
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # ZIP 파일 준비
            zip_path = os.path.join(temp_dir, "code_snippets.zip")
            
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                for snippet_id in snippet_ids:
                    try:
                        # 각 스니펫을 파일로 내보내기
                        snippet_file = self.export_snippet_to_file(snippet_id, "raw")
                        
                        # ZIP에 추가
                        zip_file.writestr(snippet_file["filename"], snippet_file["content"])
                    except HTTPException as e:
                        if e.status_code == 404:
                            logger.warning(f"스니펫 ID {snippet_id}를 찾을 수 없습니다. 건너뜁니다.")
                            continue
                        raise
                    except Exception as e:
                        logger.error(f"스니펫 ID {snippet_id} 처리 중 오류 발생: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"스니펫 패키징 실패: {str(e)}")
            
            # ZIP 파일 읽기
            with open(zip_path, "rb") as f:
                return f.read()
    
    # 코드 템플릿 관련 메서드
    def get_template(self, template_id: int) -> Optional[CodeTemplate]:
        """
        코드 템플릿을 조회합니다.
        
        Args:
            template_id: 코드 템플릿 ID
            
        Returns:
            코드 템플릿 또는 None (존재하지 않는 경우)
        """
        templates = get_code_templates(self.db, template_id=template_id)
        return templates[0] if templates else None
    
    def get_templates(
        self, 
        language: Optional[CodeLanguage] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CodeTemplate]:
        """
        조건에 맞는 코드 템플릿 목록을 조회합니다.
        
        Args:
            language: 언어로 필터링 (선택 사항)
            tag: 태그로 필터링 (선택 사항)
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수
            
        Returns:
            코드 템플릿 목록
        """
        return get_code_templates(
            self.db,
            language=language,
            tag=tag,
            skip=skip,
            limit=limit
        )
    
    def create_template(self, template: Union[CodeTemplateCreate, Dict[str, Any]]) -> CodeTemplate:
        """
        새 코드 템플릿을 생성합니다.
        
        Args:
            template: 생성할 코드 템플릿 정보
            
        Returns:
            생성된 코드 템플릿
        """
        try:
            return create_code_template(self.db, template)
        except Exception as e:
            logger.error(f"코드 템플릿 생성 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 템플릿 생성 실패: {str(e)}")
    
    def update_template(self, template_id: int, template: Union[CodeTemplate, Dict[str, Any]]) -> Optional[CodeTemplate]:
        """
        코드 템플릿을 업데이트합니다.
        
        Args:
            template_id: 코드 템플릿 ID
            template: 업데이트할 정보
            
        Returns:
            업데이트된 코드 템플릿 또는 None (존재하지 않는 경우)
        """
        try:
            return update_code_template(self.db, template_id, template)
        except Exception as e:
            logger.error(f"코드 템플릿 업데이트 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 템플릿 업데이트 실패: {str(e)}")
    
    def delete_template(self, template_id: int) -> bool:
        """
        코드 템플릿을 삭제합니다.
        
        Args:
            template_id: 코드 템플릿 ID
            
        Returns:
            성공 여부
        """
        try:
            return delete_code_template(self.db, template_id)
        except Exception as e:
            logger.error(f"코드 템플릿 삭제 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 템플릿 삭제 실패: {str(e)}")