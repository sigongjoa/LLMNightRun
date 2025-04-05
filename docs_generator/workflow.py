"""
워크플로우 관리 모듈

이 모듈은 Git 변경 감지, 코드 분석, 문서 생성의 전체 워크플로우를 관리합니다.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set
import time

from .git_handler import GitHandler
from .code_analyzer import CodeAnalyzer
from .document_builder import DocumentBuilder
from .llm_client import LLMClient

# 로깅 설정
logger = logging.getLogger(__name__)


class DocumentationWorkflow:
    """문서화 워크플로우를 관리하는 클래스"""

    def __init__(self, 
                repo_path: str = ".",
                push_changes: bool = False):
        """
        워크플로우 관리자 초기화
        
        Args:
            repo_path: Git 저장소 경로
            push_changes: 변경사항 자동 푸시 여부
        """
        self.repo_path = os.path.abspath(repo_path)
        self.push_changes = push_changes
        
        # 컴포넌트 초기화
        self.git = GitHandler(repo_path)
        self.analyzer = CodeAnalyzer()
        self.llm_client = LLMClient()
        self.doc_builder = DocumentBuilder(repo_path, self.llm_client)
        
        logger.info(f"워크플로우 초기화 완료: {repo_path}")
        
    def run(self, force_all: bool = False) -> bool:
        """
        문서화 워크플로우 실행
        
        Args:
            force_all: 모든 문서 강제 업데이트 여부
            
        Returns:
            성공 여부
        """
        try:
            logger.info("문서화 워크플로우 시작")
            
            # 1. 변경된 파일 감지
            changed_files = self._detect_changes()
            if not changed_files and not force_all:
                logger.info("변경된 파일이 없습니다. 워크플로우를 종료합니다.")
                return True
            
            # 2. 파일 분류
            classified_changes = self.git.classify_changes(changed_files)
            logger.info(f"변경 파일 분류 결과: {classified_changes}")
            
            # 3. 영향받는 문서 식별
            if force_all:
                # 모든 문서 유형 포함
                affected_docs = {"README", "API", "MODELS", "DATABASE", 
                               "ARCHITECTURE", "TESTING", "CHANGELOG", "CONFIGURATION"}
            else:
                affected_docs = self.doc_builder.get_affected_docs(classified_changes)
            
            logger.info(f"영향받는 문서: {affected_docs}")
            
            # 4. 파일 분석
            analysis_results = self._analyze_files(changed_files, force_all)
            
            # 5. 문서 업데이트
            updated_docs = self._update_documents(affected_docs, analysis_results)
            
            # 6. 변경사항 커밋
            if updated_docs:
                success = self._commit_changes(updated_docs)
                
                # 7. 변경사항 푸시 (설정된 경우)
                if success and self.push_changes:
                    branch = self.git.get_branch_name()
                    self.git.push_changes(branch=branch)
                
                return success
            else:
                logger.info("업데이트된 문서가 없습니다.")
                return True
            
        except Exception as e:
            logger.error(f"워크플로우 실행 중 오류 발생: {str(e)}")
            return False
        
    def _detect_changes(self) -> List[str]:
        """
        변경된 파일 감지
        
        Returns:
            변경된 파일 경로 목록
        """
        # 스테이징된 파일 확인
        staged_files = self.git.get_staged_files()
        
        # 워킹 디렉토리의 변경 사항 확인
        unstaged_files = self.git.get_uncommitted_changes()
        
        # 모든 변경 파일 병합 (중복 제거)
        all_changes = list(set(staged_files + unstaged_files))
        
        # 문서 파일 제외
        non_doc_changes = [f for f in all_changes if not f.endswith('.md')]
        
        logger.info(f"감지된 변경 파일: {non_doc_changes}")
        return non_doc_changes
    
    def _analyze_files(self, 
                     changed_files: List[str], 
                     analyze_all: bool = False) -> Dict[str, Any]:
        """
        파일 내용 분석
        
        Args:
            changed_files: 변경된 파일 목록
            analyze_all: 전체 코드베이스 분석 여부
            
        Returns:
            분석 결과 딕셔너리
        """
        analysis_results = {
            "python_files": [],
            "routers": [],
            "models": [],
            "database": [],
            "tests": [],
            "configs": [],
            "endpoints": [],
            "model_definitions": [],
            "database_models": []
        }
        
        files_to_analyze = changed_files
        
        # 전체 코드베이스 분석이 필요한 경우
        if analyze_all:
            # 모든 Python 파일 찾기
            import glob
            files_to_analyze = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
            files_to_analyze = [os.path.relpath(f, self.repo_path) for f in files_to_analyze]
            
            # 설정 파일 추가
            config_patterns = [
                "*.yml", "*.yaml", "*.json", "*.toml", "*.ini", "*.env"
            ]
            for pattern in config_patterns:
                config_files = glob.glob(f"{self.repo_path}/**/{pattern}", recursive=True)
                files_to_analyze.extend([os.path.relpath(f, self.repo_path) for f in config_files])
        
        # 파일 내용 분석
        for file_path in files_to_analyze:
            try:
                # 파일 내용 읽기
                full_path = os.path.join(self.repo_path, file_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 파일 분석
                result = self.analyzer.analyze_file(file_path, content)
                
                # 분석 결과 분류
                if result["type"] == "python":
                    analysis_results["python_files"].append(result)
                    
                    # API 라우터 분석
                    if result["is_router"]:
                        analysis_results["routers"].append(result)
                        if "endpoints" in result and result["endpoints"]:
                            analysis_results["endpoints"].extend(result["endpoints"])
                    
                    # 모델 분석
                    if result["is_model"]:
                        analysis_results["models"].append(result)
                        if "models" in result and result["models"]:
                            analysis_results["model_definitions"].extend(result["models"])
                    
                    # 데이터베이스 분석
                    if result["is_database"]:
                        analysis_results["database"].append(result)
                        if "models" in result and result["models"]:
                            analysis_results["database_models"].extend(result["models"])
                    
                    # 테스트 분석
                    if result["is_test"]:
                        analysis_results["tests"].append(result)
                
                # 설정 파일 분석
                elif result["type"] == "configuration":
                    analysis_results["configs"].append(result)
                
            except Exception as e:
                logger.error(f"파일 분석 중 오류 발생 ({file_path}): {str(e)}")
        
        return analysis_results
    
    def _update_documents(self, 
                        affected_docs: Set[str], 
                        analysis_results: Dict[str, Any]) -> List[str]:
        """
        영향받는 문서 업데이트
        
        Args:
            affected_docs: 영향받는 문서 유형 집합
            analysis_results: 코드 분석 결과
            
        Returns:
            업데이트된 문서 경로 목록
        """
        updated_docs = []
        
        for doc_type in affected_docs:
            logger.info(f"{doc_type} 문서 업데이트 중...")
            
            # 문서 업데이트
            success, doc_path = self.doc_builder.update_document(doc_type, analysis_results)
            
            if success:
                logger.info(f"{doc_type} 문서 업데이트 완료: {doc_path}")
                updated_docs.append(doc_path)
            else:
                logger.error(f"{doc_type} 문서 업데이트 실패")
        
        return updated_docs
    
    def _commit_changes(self, updated_docs: List[str]) -> bool:
        """
        변경된 문서 커밋
        
        Args:
            updated_docs: 업데이트된 문서 경로 목록
            
        Returns:
            성공 여부
        """
        try:
            # 문서 파일 스테이징
            self.git.stage_files(updated_docs)
            
            # 커밋 메시지 생성
            commit_message = self._generate_commit_message(updated_docs)
            
            # 변경사항 커밋
            success = self.git.commit_changes(commit_message)
            
            if success:
                logger.info(f"문서 변경사항 커밋 완료: {commit_message}")
            else:
                logger.error("문서 변경사항 커밋 실패")
            
            return success
        
        except Exception as e:
            logger.error(f"변경사항 커밋 중 오류 발생: {str(e)}")
            return False
    
    def _generate_commit_message(self, updated_docs: List[str]) -> str:
        """
        문서 변경에 대한 커밋 메시지 생성
        
        Args:
            updated_docs: 업데이트된 문서 경로 목록
            
        Returns:
            생성된 커밋 메시지
        """
        # 문서 유형 추출
        doc_types = []
        for doc_path in updated_docs:
            doc_name = os.path.basename(doc_path)
            doc_type = os.path.splitext(doc_name)[0]
            doc_types.append(doc_type)
        
        # 간단한 기본 메시지 생성
        if len(doc_types) == 1:
            return f"docs: Update {doc_types[0]} documentation"
        else:
            doc_list = ", ".join(doc_types)
            return f"docs: Update documentation ({doc_list})"


def run_workflow(repo_path: str = ".", force_all: bool = False, push_changes: bool = False) -> bool:
    """
    문서화 워크플로우 실행 헬퍼 함수
    
    Args:
        repo_path: Git 저장소 경로
        force_all: 모든 문서 강제 업데이트 여부
        push_changes: 변경사항 자동 푸시 여부
        
    Returns:
        성공 여부
    """
    workflow = DocumentationWorkflow(repo_path, push_changes)
    return workflow.run(force_all)