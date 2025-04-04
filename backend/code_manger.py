import os
import re
import logging
import json
import difflib
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import hashlib

from models import CodeSnippet, CodeTemplate, CodeLanguage, LLMType
from database.operations import (
    get_code_snippets, 
    create_code_snippet, 
    update_code_snippet,
    get_code_templates,
    create_code_template
)
from database.connection import SessionLocal
from github_uploader import upload_code_to_github

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeManager:
    """코드 조각 관리 클래스"""
    
    def __init__(self):
        """코드 관리자 초기화"""
        self.db = SessionLocal()
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    def extract_code_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        LLM 응답에서 코드 조각을 추출합니다.
        
        Args:
            response_text: LLM 응답 텍스트
            
        Returns:
            추출된 코드 조각 목록 (언어, 코드 내용, 설명 포함)
        """
        # 코드 블록 추출 패턴 (```, ``` 사이의 내용)
        code_blocks = []
        
        # 마크다운 코드 블록 패턴 (```language ... ```)
        md_pattern = r"```(\w*)\n([\s\S]*?)```"
        md_matches = re.finditer(md_pattern, response_text)
        
        for match in md_matches:
            language = match.group(1).strip().lower()
            code = match.group(2).strip()
            
            # 언어 매핑 (사용자가 입력한 언어 이름을 CodeLanguage enum 값으로 변환)
            mapped_language = self._map_language(language)
            
            # 코드 블록의 위치 전후 텍스트 찾기 (설명으로 사용)
            start_pos = match.start()
            end_pos = match.end()
            
            # 코드 블록 이전 텍스트 (최대 200자)
            pre_text = response_text[max(0, start_pos - 200):start_pos].strip()
            
            # 코드 블록 이후 텍스트 (최대 200자)
            post_text = response_text[end_pos:min(len(response_text), end_pos + 200)].strip()
            
            # 가능한 제목 찾기 (코드 블록 이전의 마지막 줄 또는 이전 텍스트의 마지막 문장)
            title = None
            pre_lines = pre_text.split('\n')
            if pre_lines:
                last_line = pre_lines[-1].strip()
                if last_line and not last_line.endswith("```"):
                    title = last_line
            
            if not title:
                # 마지막 문장 사용
                pre_sentences = re.split(r'[.!?]\s+', pre_text)
                if pre_sentences and pre_sentences[-1]:
                    title = pre_sentences[-1].strip()
            
            # 최종 제목이 없거나 너무 길면 기본값 사용
            if not title or len(title) > 100:
                title = f"Code Snippet ({mapped_language})"
            
            # 설명 생성
            description = f"{pre_text}\n\n{post_text}"
            if len(description) > 500:
                description = description[:497] + "..."
            
            code_blocks.append({
                "language": mapped_language,
                "code": code,
                "title": title,
                "description": description
            })
        
        return code_blocks
    
    def _map_language(self, language: str) -> CodeLanguage:
        """
        텍스트 언어명을 CodeLanguage enum으로 매핑합니다.
        
        Args:
            language: 코드 블록에 지정된 언어 이름
            
        Returns:
            매핑된 CodeLanguage enum 값
        """
        language = language.lower().strip()
        
        # 언어 매핑 사전
        language_map = {
            "python": CodeLanguage.PYTHON,
            "py": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "js": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT,
            "ts": CodeLanguage.TYPESCRIPT,
            "java": CodeLanguage.JAVA,
            "csharp": CodeLanguage.CSHARP,
            "cs": CodeLanguage.CSHARP,
            "c#": CodeLanguage.CSHARP,
            "cpp": CodeLanguage.CPP,
            "c++": CodeLanguage.CPP,
            "go": CodeLanguage.GO,
            "golang": CodeLanguage.GO,
            "rust": CodeLanguage.RUST,
            "php": CodeLanguage.PHP,
            "ruby": CodeLanguage.RUBY,
            "rb": CodeLanguage.RUBY,
            "swift": CodeLanguage.SWIFT,
            "kotlin": CodeLanguage.KOTLIN,
            "kt": CodeLanguage.KOTLIN
        }
        
        return language_map.get(language, CodeLanguage.OTHER)
    
    def save_code_snippet(
        self, 
        code: str, 
        language: CodeLanguage, 
        title: str, 
        description: Optional[str] = None,
        source_llm: Optional[LLMType] = None,
        question_id: Optional[int] = None,
        response_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> CodeSnippet:
        """
        코드 스니펫을 저장합니다.
        
        Args:
            code: 코드 내용
            language: 프로그래밍 언어
            title: 제목
            description: 설명 (선택 사항)
            source_llm: 소스 LLM 유형 (선택 사항)
            question_id: 관련 질문 ID (선택 사항)
            response_id: 관련 응답 ID (선택 사항)
            tags: 태그 목록 (선택 사항)
            
        Returns:
            저장된 코드 스니펫 객체
        """
        if tags is None:
            tags = []
        
        # 코드 스니펫 생성
        snippet = CodeSnippet(
            title=title,
            description=description,
            content=code,
            language=language,
            source_llm=source_llm,
            question_id=question_id,
            response_id=response_id,
            tags=tags,
            version=1
        )
        
        # 데이터베이스에 저장
        return create_code_snippet(self.db, snippet)
    
    def process_llm_response(
        self, 
        response_text: str, 
        source_llm: LLMType,
        question_id: Optional[int] = None,
        response_id: Optional[int] = None
    ) -> List[CodeSnippet]:
        """
        LLM 응답에서 코드를 추출하고 저장합니다.
        
        Args:
            response_text: LLM 응답 텍스트
            source_llm: LLM 유형
            question_id: 질문 ID (선택 사항)
            response_id: 응답 ID (선택 사항)
            
        Returns:
            저장된 코드 스니펫 객체 목록
        """
        # 코드 추출
        code_blocks = self.extract_code_from_response(response_text)
        saved_snippets = []
        
        for block in code_blocks:
            # 코드 스니펫 저장
            snippet = self.save_code_snippet(
                code=block["code"],
                language=block["language"],
                title=block["title"],
                description=block["description"],
                source_llm=source_llm,
                question_id=question_id,
                response_id=response_id
            )
            saved_snippets.append(snippet)
        
        return saved_snippets
    
    def compare_code_snippets(self, snippet1_id: int, snippet2_id: int) -> Dict[str, Any]:
        """
        두 코드 스니펫을 비교합니다.
        
        Args:
            snippet1_id: 첫 번째 스니펫 ID
            snippet2_id: 두 번째 스니펫 ID
            
        Returns:
            비교 결과 (유사성 점수, 차이점 등)
        """
        # 스니펫 가져오기
        snippets = get_code_snippets(self.db, snippet_id=[snippet1_id, snippet2_id])
        
        if len(snippets) != 2:
            raise ValueError(f"하나 또는 두 개의 스니펫을 찾을 수 없습니다: {snippet1_id}, {snippet2_id}")
        
        snippet1 = snippets[0]
        snippet2 = snippets[1]
        
        # 코드 비교
        code1 = snippet1.content.splitlines()
        code2 = snippet2.content.splitlines()
        
        # 차이점 계산
        diff = list(difflib.unified_diff(
            code1, code2,
            fromfile=f'snippet_{snippet1.id}',
            tofile=f'snippet_{snippet2.id}',
            lineterm=''
        ))
        
        # 유사성 계산 (SequenceMatcher 사용)
        similarity = difflib.SequenceMatcher(None, snippet1.content, snippet2.content).ratio()
        
        return {
            "snippet1": {
                "id": snippet1.id,
                "title": snippet1.title,
                "language": snippet1.language
            },
            "snippet2": {
                "id": snippet2.id,
                "title": snippet2.title,
                "language": snippet2.language
            },
            "similarity": similarity,
            "diff": diff,
            "diff_count": len(diff)
        }
    
    def create_template_from_snippet(
        self, 
        snippet_id: int, 
        template_name: str, 
        template_description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> CodeTemplate:
        """
        기존 코드 스니펫에서 템플릿을 생성합니다.
        
        Args:
            snippet_id: 스니펫 ID
            template_name: 템플릿 이름
            template_description: 템플릿 설명 (선택 사항)
            tags: 태그 목록 (선택 사항)
            
        Returns:
            생성된 템플릿 객체
        """
        if tags is None:
            tags = []
        
        # 스니펫 가져오기
        snippets = get_code_snippets(self.db, snippet_id=snippet_id)
        
        if not snippets:
            raise ValueError(f"코드 스니펫을 찾을 수 없습니다: {snippet_id}")
        
        snippet = snippets[0]
        
        # 템플릿 생성
        template = CodeTemplate(
            name=template_name,
            description=template_description or snippet.description,
            content=snippet.content,
            language=snippet.language,
            tags=tags
        )
        
        # 데이터베이스에 저장
        return create_code_template(self.db, template)
    
    def find_similar_snippets(self, code: str, language: Optional[CodeLanguage] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        주어진 코드와 유사한 스니펫을 찾습니다.
        
        Args:
            code: 비교할 코드
            language: 언어 필터 (선택 사항)
            limit: 최대 결과 수
            
        Returns:
            유사한 코드 스니펫 목록 (유사성 점수 포함)
        """
        # 모든 스니펫 가져오기 (선택적으로 언어로 필터링)
        snippets = get_code_snippets(self.db, language=language.value if language else None)
        
        results = []
        
        for snippet in snippets:
            # 유사성 계산
            similarity = difflib.SequenceMatcher(None, code, snippet.content).ratio()
            
            # 결과 저장
            results.append({
                "snippet": snippet,
                "similarity": similarity
            })
        
        # 유사성으로 정렬하고 상위 결과 반환
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def search_code_by_content(self, query: str, language: Optional[CodeLanguage] = None, limit: int = 10) -> List[CodeSnippet]:
        """
        코드 내용에서 텍스트를 검색합니다.
        
        Args:
            query: 검색 쿼리
            language: 언어 필터 (선택 사항)
            limit: 최대 결과 수
            
        Returns:
            일치하는 코드 스니펫 목록
        """
        # 모든 스니펫 가져오기 (선택적으로 언어로 필터링)
        snippets = get_code_snippets(self.db, language=language.value if language else None)
        
        results = []
        query = query.lower()
        
        for snippet in snippets:
            # 코드 내용에서 쿼리 검색
            if query in snippet.content.lower() or (snippet.description and query in snippet.description.lower()):
                results.append(snippet)
        
        return results[:limit]
    
    def generate_code_hash(self, code: str) -> str:
        """
        코드의 해시를 생성합니다 (중복 감지에 사용).
        
        Args:
            code: 코드 내용
            
        Returns:
            코드의 SHA-256 해시 (16자리 축약)
        """
        # 공백 제거 및 정규화
        normalized_code = re.sub(r'\s+', ' ', code).strip()
        
        # SHA-256 해시 생성
        sha256 = hashlib.sha256(normalized_code.encode('utf-8')).hexdigest()
        
        # 16자리 축약 반환
        return sha256[:16]
    
    def detect_duplicates(self, code: str, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        유사하거나 중복된 코드 스니펫을 감지합니다.
        
        Args:
            code: 확인할 코드
            threshold: 유사성 임계값 (0.0 ~ 1.0)
            
        Returns:
            중복 스니펫 목록 (유사성 점수 포함)
        """
        # 코드 해시 생성
        code_hash = self.generate_code_hash(code)
        
        # 모든 스니펫 가져오기
        snippets = get_code_snippets(self.db)
        
        duplicates = []
        
        for snippet in snippets:
            # 해시 비교
            snippet_hash = self.generate_code_hash(snippet.content)
            
            if code_hash == snippet_hash:
                # 정확한 중복
                duplicates.append({
                    "snippet": snippet,
                    "similarity": 1.0,
                    "exact_match": True
                })
            else:
                # 유사성 검사
                similarity = difflib.SequenceMatcher(None, code, snippet.content).ratio()
                
                if similarity >= threshold:
                    duplicates.append({
                        "snippet": snippet,
                        "similarity": similarity,
                        "exact_match": False
                    })
        
        return duplicates
    
    def save_to_github(self, snippet_id: int, filename: Optional[str] = None) -> Optional[str]:
        """
        코드 스니펫을 GitHub에 저장합니다.
        
        Args:
            snippet_id: 저장할 스니펫 ID
            filename: 파일 이름 (지정하지 않으면 자동 생성)
            
        Returns:
            GitHub 파일 URL 또는 None (실패 시)
        """
        # 스니펫 가져오기
        snippets = get_code_snippets(self.db, snippet_id=snippet_id)
        
        if not snippets:
            raise ValueError(f"코드 스니펫을 찾을 수 없습니다: {snippet_id}")
        
        snippet = snippets[0]
        
        # 파일 이름 생성 (지정되지 않은 경우)
        if not filename:
            # 제목에서 파일 이름 생성 (특수 문자 제거 및 공백을 언더스코어로 변환)
            title_part = ''.join(c for c in snippet.title if c.isalnum() or c.isspace()).strip().replace(' ', '_')
            title_part = title_part[:30]  # 최대 30자
            
            # 언어별 확장자 추가
            extension = self._get_file_extension(snippet.language)
            filename = f"code/{title_part}_{snippet.id}{extension}"
        
        # 커밋 메시지 생성
        commit_message = f"Add code snippet: {snippet.title}"
        
        # GitHub에 업로드
        return upload_code_to_github(snippet.content, filename, commit_message)
    
    def _get_file_extension(self, language: CodeLanguage) -> str:
        """
        언어에 따른 파일 확장자를 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            파일 확장자 (점 포함)
        """
        extensions = {
            CodeLanguage.PYTHON: ".py",
            CodeLanguage.JAVASCRIPT: ".js",
            CodeLanguage.TYPESCRIPT: ".ts",
            CodeLanguage.JAVA: ".java",
            CodeLanguage.CSHARP: ".cs",
            CodeLanguage.CPP: ".cpp",
            CodeLanguage.GO: ".go",
            CodeLanguage.RUST: ".rs",
            CodeLanguage.PHP: ".php",
            CodeLanguage.RUBY: ".rb",
            CodeLanguage.SWIFT: ".swift",
            CodeLanguage.KOTLIN: ".kt",
            CodeLanguage.OTHER: ".txt"
        }
        
        return extensions.get(language, ".txt")