"""
문서 관리 서비스

이 모듈은 문서 생성, 관리, 저장을 위한 서비스를 제공합니다.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from ..models.document import Document, DocumentType, DocumentStatus
from ..database.document_repository import DocumentRepository
from ..tool.llm_tool import LLMTool

# 로거 설정
logger = logging.getLogger(__name__)


class DocumentService:
    """문서 관리 서비스 클래스"""

    def __init__(self):
        """서비스 초기화"""
        self.repo = DocumentRepository()
        self.llm_tool = LLMTool()
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs_generator", "templates")
    
    def list_documents(self, 
                      document_type: Optional[DocumentType] = None,
                      status: Optional[DocumentStatus] = None,
                      page: int = 1,
                      page_size: int = 10) -> Tuple[List[Document], int]:
        """
        문서 목록 조회
        
        Args:
            document_type: 필터링할 문서 유형
            status: 필터링할 문서 상태
            page: 페이지 번호
            page_size: 페이지 크기
            
        Returns:
            문서 목록과 총 문서 수 튜플
        """
        filters = {}
        if document_type:
            filters["type"] = document_type
        if status:
            filters["status"] = status
            
        offset = (page - 1) * page_size
        documents, total = self.repo.list_documents(
            filters=filters,
            offset=offset,
            limit=page_size
        )
        
        return documents, total
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        문서 조회
        
        Args:
            document_id: 문서 ID
            
        Returns:
            문서 객체 또는 None
        """
        return self.repo.get_document(document_id)
    
    def create_document(self, document: Document) -> Document:
        """
        문서 생성
        
        Args:
            document: 생성할 문서 객체
            
        Returns:
            생성된 문서 객체
        """
        return self.repo.create_document(document)
    
    def update_document(self, document_id: str, update_data: Dict[str, Any]) -> Document:
        """
        문서 업데이트
        
        Args:
            document_id: 문서 ID
            update_data: 업데이트할 데이터
            
        Returns:
            업데이트된 문서 객체
        """
        return self.repo.update_document(document_id, update_data)
    
    def delete_document(self, document_id: str) -> bool:
        """
        문서 삭제
        
        Args:
            document_id: 문서 ID
            
        Returns:
            성공 여부
        """
        return self.repo.delete_document(document_id)
    
    def generate_document(self, 
                         doc_type: DocumentType,
                         force_regenerate: bool = False,
                         custom_params: Dict[str, Any] = None) -> Document:
        """
        LLM을 사용하여 문서 자동 생성
        
        Args:
            doc_type: 문서 유형
            force_regenerate: 기존 문서 강제 재생성 여부
            custom_params: 커스텀 파라미터
            
        Returns:
            생성된 문서 객체
        """
        # 커스텀 파라미터 정규화
        custom_params = custom_params or {}
        
        # 기존 문서 확인
        existing_document = None
        if not force_regenerate:
            # 해당 유형의 문서 찾기
            documents, _ = self.repo.list_documents(filters={"type": doc_type}, limit=1)
            if documents:
                existing_document = documents[0]
        
        # 템플릿 로드
        template = self._load_template(doc_type)
        
        # 프로젝트 분석 데이터 수집
        analysis_data = self._collect_project_data(doc_type, custom_params)
        
        # LLM으로 문서 생성
        content = self._generate_content_with_llm(
            doc_type=doc_type,
            template=template,
            analysis_data=analysis_data,
            existing_content=existing_document.content if existing_document else None,
            custom_params=custom_params
        )
        
        # 문서 제목 결정
        title = self._get_document_title(doc_type)
        
        if existing_document:
            # 기존 문서 업데이트
            update_data = {
                "content": content,
                "updated_at": datetime.now(),
                "status": DocumentStatus.GENERATED
            }
            
            return self.repo.update_document(existing_document.id, update_data)
        else:
            # 새 문서 생성
            new_document = Document(
                id=f"doc_{uuid.uuid4().hex[:8]}",
                type=doc_type,
                title=title,
                content=content,
                status=DocumentStatus.GENERATED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={
                    "generated": True,
                    "generation_params": custom_params
                }
            )
            
            return self.repo.create_document(new_document)
    
    def preview_document(self, 
                        doc_type: DocumentType,
                        custom_params: Dict[str, Any] = None) -> str:
        """
        문서 미리보기 생성 (저장하지 않음)
        
        Args:
            doc_type: 문서 유형
            custom_params: 커스텀 파라미터
            
        Returns:
            생성된 문서 내용
        """
        # 커스텀 파라미터 정규화
        custom_params = custom_params or {}
        
        # 템플릿 로드
        template = self._load_template(doc_type)
        
        # 프로젝트 분석 데이터 수집
        analysis_data = self._collect_project_data(doc_type, custom_params)
        
        # LLM으로 문서 생성
        content = self._generate_content_with_llm(
            doc_type=doc_type,
            template=template,
            analysis_data=analysis_data,
            existing_content=None,
            custom_params=custom_params
        )
        
        return content
    
    def _load_template(self, doc_type: DocumentType) -> str:
        """
        문서 템플릿 로드
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            템플릿 내용
        """
        template_name = f"{doc_type.value.lower()}_template.md"
        template_path = os.path.join(self.templates_dir, template_name)
        
        # 템플릿 파일이 없는 경우 기본 템플릿 사용
        if not os.path.exists(template_path):
            logger.warning(f"템플릿 파일 '{template_name}'을 찾을 수 없습니다. 기본 템플릿을 사용합니다.")
            return f"# {doc_type.value} 문서\n\n## 개요\n\n이 문서는 자동으로 생성되었습니다.\n"
        
        # 템플릿 파일 읽기
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            return template
        except Exception as e:
            logger.error(f"템플릿 파일 읽기 실패: {str(e)}")
            return f"# {doc_type.value} 문서\n\n## 개요\n\n이 문서는 자동으로 생성되었습니다.\n"
    
    def _collect_project_data(self, 
                            doc_type: DocumentType, 
                            custom_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 분석 데이터 수집
        
        Args:
            doc_type: 문서 유형
            custom_params: 커스텀 파라미터
            
        Returns:
            분석 데이터
        """
        # 분석 데이터 초기화
        analysis_data = {
            "project_name": "LLMNightRun",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "custom_params": custom_params
        }
        
        # 문서 유형별 추가 데이터 수집
        if doc_type == DocumentType.API_DOC:
            # API 관련 데이터 수집
            analysis_data.update(self._collect_api_data())
        elif doc_type == DocumentType.DATABASE:
            # 데이터베이스 관련 데이터 수집
            analysis_data.update(self._collect_database_data())
        elif doc_type == DocumentType.ARCHITECTURE:
            # 아키텍처 관련 데이터 수집
            analysis_data.update(self._collect_architecture_data())
        elif doc_type == DocumentType.SETUP:
            # 설치 관련 데이터 수집
            analysis_data.update(self._collect_setup_data())
        
        return analysis_data
    
    def _collect_api_data(self) -> Dict[str, Any]:
        """API 관련 데이터 수집"""
        # 여기서 FastAPI 앱에서 엔드포인트 목록 수집 로직 구현
        # 실제 구현은 프로젝트에 맞게 조정 필요
        return {
            "endpoints": [
                {"path": "/api/example", "method": "GET", "description": "예시 API"}
            ]
        }
    
    def _collect_database_data(self) -> Dict[str, Any]:
        """데이터베이스 관련 데이터 수집"""
        # 데이터베이스 스키마 정보 수집 로직 구현
        return {
            "database_type": "SQLite",
            "models": []
        }
    
    def _collect_architecture_data(self) -> Dict[str, Any]:
        """아키텍처 관련 데이터 수집"""
        # 프로젝트 구조 및 아키텍처 정보 수집 로직 구현
        return {
            "backend_framework": "FastAPI",
            "frontend_framework": "Next.js"
        }
    
    def _collect_setup_data(self) -> Dict[str, Any]:
        """설치 관련 데이터 수집"""
        # 설치 및 설정 관련 데이터 수집 로직 구현
        return {
            "python_version": "3.8+",
            "node_version": "14+"
        }
    
    def _generate_content_with_llm(self, 
                                 doc_type: DocumentType,
                                 template: str,
                                 analysis_data: Dict[str, Any],
                                 existing_content: Optional[str] = None,
                                 custom_params: Dict[str, Any] = None) -> str:
        """
        LLM을 사용하여 문서 내용 생성
        
        Args:
            doc_type: 문서 유형
            template: 템플릿 내용
            analysis_data: 분석 데이터
            existing_content: 기존 문서 내용
            custom_params: 커스텀 파라미터
            
        Returns:
            생성된 문서 내용
        """
        # LLM 프롬프트 생성
        prompt = self._create_llm_prompt(
            doc_type=doc_type,
            template=template,
            analysis_data=analysis_data,
            existing_content=existing_content,
            custom_params=custom_params
        )
        
        # LLM 호출
        try:
            content = self.llm_tool.generate_document(prompt)
            return content
        except Exception as e:
            logger.error(f"LLM 문서 생성 실패: {str(e)}")
            
            # 오류 시 템플릿 기반으로 기본 문서 반환
            return template.replace("[프로젝트명]", "LLMNightRun")
    
    def _create_llm_prompt(self, 
                          doc_type: DocumentType,
                          template: str,
                          analysis_data: Dict[str, Any],
                          existing_content: Optional[str] = None,
                          custom_params: Dict[str, Any] = None) -> str:
        """
        LLM 프롬프트 생성
        
        Args:
            doc_type: 문서 유형
            template: 템플릿 내용
            analysis_data: 분석 데이터
            existing_content: 기존 문서 내용
            custom_params: 커스텀 파라미터
            
        Returns:
            생성된 프롬프트
        """
        prompt = f"""
당신은 소프트웨어 문서화 전문가입니다. 제공된 정보를 기반으로 LLMNightRun 프로젝트의 {doc_type.value} 문서를 작성해주세요.
문서는 마크다운 형식으로 작성되어야 하며, 내용은 명확하고 구조적이어야 합니다.

### 문서 유형: {doc_type.value}

### 분석 데이터:
```json
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}
```

### 템플릿:
```markdown
{template}
```
"""

        # 기존 문서가 있는 경우, 업데이트 지침 추가
        if existing_content:
            prompt += f"""
### 기존 문서 내용:
```markdown
{existing_content}
```

위의 기존 문서를 참고하여 내용을 업데이트해주세요. 기존의 중요한 정보는 유지하면서 필요한 내용을 추가하거나 수정해주세요.
가능한 한 문서의 톤과 스타일을 일관되게 유지해주세요.
"""
        else:
            prompt += "\n주어진 템플릿을 기반으로 새로운 문서를 작성해주세요. 이 문서는 프로젝트의 주요 참고자료가 될 것입니다."

        # 커스텀 파라미터가 있는 경우 추가
        if custom_params:
            prompt += f"""
### 커스텀 요구사항:
```json
{json.dumps(custom_params, indent=2, ensure_ascii=False)}
```
위의 커스텀 요구사항을 문서 생성 과정에 반영해주세요.
"""

        # 응답 형식 지침 추가
        prompt += """
### 응답 형식:
마크다운 형식으로만 문서를 작성해주세요. 문법적으로 정확하고 가독성이 좋은 문서를 작성해주세요.
추가 설명 없이 바로 마크다운 문서 내용만 반환해주세요.
"""
        
        return prompt
    
    def _get_document_title(self, doc_type: DocumentType) -> str:
        """
        문서 제목 결정
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            문서 제목
        """
        # 문서 유형에 따른 기본 제목 매핑
        title_map = {
            DocumentType.README: "README",
            DocumentType.API_DOC: "API 문서",
            DocumentType.ARCHITECTURE: "시스템 아키텍처",
            DocumentType.DESIGN: "UI/UX 설계",
            DocumentType.DATABASE: "데이터베이스 설계",
            DocumentType.SETUP: "설치 및 설정 가이드",
            DocumentType.DEPLOYMENT: "배포 가이드",
            DocumentType.CONFIGURATION: "환경 설정 가이드",
            DocumentType.CHANGELOG: "변경 이력"
        }
        
        return title_map.get(doc_type, f"{doc_type.value} 문서")