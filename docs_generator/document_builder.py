"""
문서 생성 모듈

이 모듈은 코드 분석 결과를 기반으로 다양한 형식의 문서를 생성합니다.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from .llm_client import LLMClient

# 로깅 설정
logger = logging.getLogger(__name__)


class DocumentBuilder:
    """문서 생성을 위한 클래스"""

    def __init__(self, 
                repo_path: str = ".",
                llm_client: Optional[LLMClient] = None):
        """
        문서 생성기 초기화
        
        Args:
            repo_path: 저장소 경로
            llm_client: LLM 클라이언트 인스턴스 (None인 경우 자동 생성)
        """
        self.repo_path = os.path.abspath(repo_path)
        self.docs_dir = os.path.join(self.repo_path, "docs")
        self.llm_client = llm_client or LLMClient()
        
        # docs 디렉토리가 없으면 생성
        os.makedirs(self.docs_dir, exist_ok=True)
        
    def get_document_path(self, doc_type: str) -> str:
        """
        문서 파일 경로 생성
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            문서 파일 전체 경로
        """
        # 문서 파일명 생성 (대소문자 구분 없이 일관되게)
        filename = f"{doc_type.upper()}.md"
        
        # 문서 위치 결정 (README는 루트, 나머지는 docs 디렉토리)
        if doc_type.upper() == "README":
            return os.path.join(self.repo_path, "README.md")
        else:
            return os.path.join(self.docs_dir, filename)
    
    def document_exists(self, doc_type: str) -> bool:
        """
        문서 파일 존재 여부 확인
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            문서 파일 존재 여부
        """
        path = self.get_document_path(doc_type)
        return os.path.exists(path)
    
    def read_document(self, doc_type: str) -> Optional[str]:
        """
        기존 문서 내용 읽기
        
        Args:
            doc_type: 문서 유형
            
        Returns:
            문서 내용 또는 None (파일이 없는 경우)
        """
        path = self.get_document_path(doc_type)
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"문서 파일 읽기 실패: {str(e)}")
                return None
        
        return None
    
    def write_document(self, doc_type: str, content: str) -> bool:
        """
        문서 파일 쓰기
        
        Args:
            doc_type: 문서 유형
            content: 문서 내용
            
        Returns:
            성공 여부
        """
        path = self.get_document_path(doc_type)
        
        try:
            # 디렉토리 확인 및 생성
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 파일 쓰기
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"문서 파일 저장 완료: {path}")
            return True
        
        except Exception as e:
            logger.error(f"문서 파일 쓰기 실패: {str(e)}")
            return False
    
    def update_document(self, 
                       doc_type: str, 
                       code_analysis: Dict[str, Any]) -> Tuple[bool, str]:
        """
        문서 생성 또는 업데이트
        
        Args:
            doc_type: 문서 유형
            code_analysis: 코드 분석 결과
            
        Returns:
            (성공 여부, 문서 경로) 튜플
        """
        # 기존 문서 내용 읽기
        existing_content = self.read_document(doc_type)
        
        try:
            # LLM을 사용하여 문서 생성
            new_content = self.llm_client.generate_document(
                doc_type=doc_type,
                code_analysis=code_analysis,
                existing_content=existing_content
            )
            
            # 문서 저장
            success = self.write_document(doc_type, new_content)
            return success, self.get_document_path(doc_type)
        
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {str(e)}")
            return False, ""
    
    def get_affected_docs(self, classified_changes: Dict[str, List[str]]) -> Set[str]:
        """
        코드 변경에 영향받는 문서 유형 식별
        
        Args:
            classified_changes: 유형별로 분류된 변경 파일 목록
            
        Returns:
            업데이트가 필요한 문서 유형 집합
        """
        affected_docs = set()
        
        # 영향을 받는 문서 매핑
        if classified_changes["router"]:
            affected_docs.add("API")
            
        if classified_changes["model"]:
            affected_docs.add("MODELS")
            
        if classified_changes["database"]:
            affected_docs.add("DATABASE")
            
        if classified_changes["test"]:
            affected_docs.add("TESTING")
            
        if classified_changes["config"]:
            affected_docs.add("CONFIGURATION")
            
        # README는 모든 주요 변경에 영향을 받음
        if (classified_changes["router"] or 
            classified_changes["model"] or 
            classified_changes["database"] or 
            classified_changes["python"]):
            affected_docs.add("README")
            
        # 변경된 파일이 많으면 아키텍처 문서도 영향받을 수 있음
        if (len(classified_changes["router"]) > 2 or 
            len(classified_changes["model"]) > 2 or 
            len(classified_changes["database"]) > 2 or 
            len(classified_changes["python"]) > 5):
            affected_docs.add("ARCHITECTURE")
            
        # CHANGELOG는 항상 업데이트
        affected_docs.add("CHANGELOG")
        
        return affected_docs