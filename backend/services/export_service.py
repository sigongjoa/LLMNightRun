"""
내보내기 서비스 모듈

다양한 형식으로 데이터를 내보내는 기능을 제공합니다.
"""

import os
import json
import tempfile
import zipfile
import markdown
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import BaseModel

from ..database.operations.question import get_questions
from ..database.operations.respone import get_responses
from ..database.operations.code import get_code_snippets
from ..database.operations.agent import get_agent_logs, get_agent_session


class ExportFormat(str, Enum):
    """내보내기 형식"""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    CODE_PACKAGE = "code_package"


class ExportOptions(BaseModel):
    """내보내기 옵션"""
    include_metadata: bool = True
    include_tags: bool = True
    include_timestamps: bool = True
    include_llm_info: bool = True
    code_highlighting: bool = True


class ExportService:
    """내보내기 서비스 클래스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        
    def _convert_markdown_to_html(self, markdown_content: str, title: str) -> str:
        """Markdown을 HTML로 변환"""
        try:
            # Markdown을 HTML로 변환
            html_body = markdown.markdown(
                markdown_content,
                extensions=['fenced_code', 'codehilite', 'tables', 'toc']
            )
            
            # 기본 스타일 및 HTML 문서 구조
            html = f"""<!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    code {{ font-family: 'Courier New', monospace; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ background-color: #f2f2f2; text-align: left; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                {html_body}
            </body>
            </html>"""
            
            return html
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Markdown을 HTML로 변환하는 중 오류 발생: {str(e)}"
            )
    
    def _get_language_extension(self, language) -> str:
        """언어에 따른 파일 확장자 반환"""
        if isinstance(language, Enum):
            language = language.value.lower()
        else:
            language = str(language).lower()
        
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
            "html": "html",
            "css": "css",
            "sql": "sql"
        }
        
        return extension_map.get(language, "txt")
    
    def _get_comment_marker(self, language) -> str:
        """언어에 따른 주석 마커 반환"""
        if isinstance(language, Enum):
            language = language.value.lower()
        else:
            language = str(language).lower()
        
        comment_map = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "java": "//",
            "csharp": "//",
            "cpp": "//",
            "go": "//",
            "rust": "//",
            "php": "//",
            "ruby": "#",
            "swift": "//",
            "kotlin": "//",
            "html": "<!--",
            "css": "/*",
            "sql": "--"
        }
        
        return comment_map.get(language, "#")
    
    async def export_question(
        self, 
        question_id: int, 
        format: str, 
        options: ExportOptions
    ) -> Dict[str, Any]:
        """
        질문과 관련 응답을 내보내는 함수
        
        Args:
            question_id: 질문 ID
            format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            파일 정보 및 내용
            
        Raises:
            HTTPException: 질문을 찾을 수 없거나 형식이 지원되지 않는 경우
        """
        # 질문 조회
        question = get_questions(self.db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        
        # 관련 응답 조회
        responses = get_responses(self.db, question_id=question_id)
        
        # 관련 코드 스니펫 조회
        code_snippets = get_code_snippets(self.db, question_id=question_id)
        
        # 데이터 준비
        data = {
            "question": question.dict() if hasattr(question, "dict") else question,
            "responses": [r.dict() if hasattr(r, "dict") else r for r in responses],
            "code_snippets": [c.dict() if hasattr(c, "dict") else c for c in code_snippets]
        }
        
        # 타임스탬프
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # 형식에 따라 내용 생성
        if format.lower() == ExportFormat.JSON.value:
            # JSON 형식
            content = json.dumps(data, indent=2, default=str)
            content_type = "application/json"
            filename = f"question_{question_id}_{timestamp}.json"
        
        elif format.lower() == ExportFormat.MARKDOWN.value:
            # Markdown 형식
            content = self._generate_markdown_question(question, responses, code_snippets, options)
            content_type = "text/markdown"
            filename = f"question_{question_id}_{timestamp}.md"
        
        elif format.lower() == ExportFormat.HTML.value:
            # HTML 형식 (Markdown을 HTML로 변환)
            md_content = self._generate_markdown_question(question, responses, code_snippets, options)
            content = self._convert_markdown_to_html(md_content, f"질문 #{question_id}")
            content_type = "text/html"
            filename = f"question_{question_id}_{timestamp}.html"
        
        elif format.lower() == ExportFormat.PDF.value:
            # PDF 형식 (HTML로 변환 후 PDF로 렌더링)
            try:
                from weasyprint import HTML
                
                md_content = self._generate_markdown_question(question, responses, code_snippets, options)
                html_content = self._convert_markdown_to_html(md_content, f"질문 #{question_id}")
                
                # HTML을 PDF로 변환
                pdf_bytes = BytesIO()
                HTML(string=html_content).write_pdf(pdf_bytes)
                pdf_bytes.seek(0)
                
                content = pdf_bytes.getvalue()
                content_type = "application/pdf"
                filename = f"question_{question_id}_{timestamp}.pdf"
            except ImportError:
                raise HTTPException(
                    status_code=500, 
                    detail="PDF 내보내기에 필요한 WeasyPrint 라이브러리가 설치되지 않았습니다"
                )
        
        elif format.lower() == ExportFormat.CODE_PACKAGE.value:
            # 코드 패키지 (ZIP 파일)
            if not code_snippets:
                raise HTTPException(
                    status_code=404, 
                    detail=f"질문 ID {question_id}에 관련된 코드 스니펫이 없습니다"
                )
            
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # ZIP 파일 준비
                zip_path = os.path.join(temp_dir, f"question_{question_id}_code_{timestamp}.zip")
                
                with zipfile.ZipFile(zip_path, "w") as zip_file:
                    # README 파일 추가
                    readme_content = self._generate_markdown_question(question, responses, [], options)
                    zip_file.writestr("README.md", readme_content)
                    
                    # 코드 스니펫 추가
                    for i, snippet in enumerate(code_snippets):
                        # 파일 확장자 결정
                        extension = self._get_language_extension(snippet.language)
                        
                        # 파일명 생성
                        filename = f"snippet_{i+1}_{snippet.title.replace(' ', '_').lower()}.{extension}"
                        
                        # ZIP에 추가
                        zip_file.writestr(filename, snippet.content)
                
                # ZIP 파일 읽기
                with open(zip_path, "rb") as f:
                    content = f.read()
                
                content_type = "application/zip"
                filename = f"question_{question_id}_code_{timestamp}.zip"
        
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {format}")
        
        return {
            "content": content,
            "content_type": content_type,
            "filename": filename
        }
    
    async def export_code_snippet(
        self, 
        snippet_id: int, 
        format: str, 
        options: ExportOptions
    ) -> Dict[str, Any]:
        """
        코드 스니펫을 내보내는 함수
        
        Args:
            snippet_id: 코드 스니펫 ID
            format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            파일 정보 및 내용
            
        Raises:
            HTTPException: 스니펫을 찾을 수 없거나 형식이 지원되지 않는 경우
        """
        # 코드 스니펫 조회
        snippets = get_code_snippets(self.db, snippet_id=snippet_id)
        if not snippets or len(snippets) == 0:
            raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
        
        snippet = snippets[0]
        
        # 타임스탬프
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # 형식에 따라 내용 생성
        if format.lower() == ExportFormat.JSON.value:
            # JSON 형식
            content = json.dumps(
                snippet.dict() if hasattr(snippet, "dict") else snippet, 
                indent=2, 
                default=str
            )
            content_type = "application/json"
            filename = f"snippet_{snippet_id}_{timestamp}.json"
        
        elif format.lower() == ExportFormat.MARKDOWN.value:
            # Markdown 형식
            content = self._generate_markdown_snippet(snippet, options)
            content_type = "text/markdown"
            filename = f"snippet_{snippet_id}_{timestamp}.md"
        
        elif format.lower() == ExportFormat.CODE_PACKAGE.value:
            # 코드 파일로 직접 내보내기
            extension = self._get_language_extension(snippet.language)
            
            content = snippet.content
            if options.include_metadata:
                # 메타데이터를 주석으로 포함
                comment_marker = self._get_comment_marker(snippet.language)
                metadata = f"{comment_marker} Title: {snippet.title}\n"
                if snippet.description:
                    metadata += f"{comment_marker} Description: {snippet.description}\n"
                if options.include_timestamps and hasattr(snippet, "created_at") and snippet.created_at:
                    metadata += f"{comment_marker} Created: {snippet.created_at}\n"
                if options.include_tags and snippet.tags:
                    metadata += f"{comment_marker} Tags: {', '.join(snippet.tags)}\n"
                
                content = f"{metadata}\n{content}"
            
            content_type = "text/plain"
            filename = f"{snippet.title.replace(' ', '_').lower()}.{extension}"
        
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {format}")
        
        return {
            "content": content,
            "content_type": content_type,
            "filename": filename
        }
    
    async def export_agent_logs(
        self, 
        session_id: str, 
        format: str, 
        options: ExportOptions
    ) -> Dict[str, Any]:
        """
        에이전트 로그를 내보내는 함수
        
        Args:
            session_id: 에이전트 세션 ID
            format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            파일 정보 및 내용
            
        Raises:
            HTTPException: 세션을 찾을 수 없거나 형식이 지원되지 않는 경우
        """
        # 세션 조회
        session = get_agent_session(self.db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"에이전트 세션 ID {session_id}를 찾을 수 없습니다")
        
        # 로그 조회
        logs = get_agent_logs(self.db, session_id=session_id)
        
        # 데이터 준비
        data = {
            "session": session.dict() if hasattr(session, "dict") else session,
            "logs": [log.dict() if hasattr(log, "dict") else log for log in logs]
        }
        
        # 타임스탬프
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # 형식에 따라 내용 생성
        if format.lower() == ExportFormat.JSON.value:
            # JSON 형식
            content = json.dumps(data, indent=2, default=str)
            content_type = "application/json"
            filename = f"agent_logs_{session_id}_{timestamp}.json"
        
        elif format.lower() == ExportFormat.MARKDOWN.value:
            # Markdown 형식
            content = self._generate_markdown_agent_logs(session, logs, options)
            content_type = "text/markdown"
            filename = f"agent_logs_{session_id}_{timestamp}.md"
        
        elif format.lower() == ExportFormat.HTML.value:
            # HTML 형식 (Markdown을 HTML로 변환)
            md_content = self._generate_markdown_agent_logs(session, logs, options)
            content = self._convert_markdown_to_html(md_content, f"에이전트 세션 {session_id}")
            content_type = "text/html"
            filename = f"agent_logs_{session_id}_{timestamp}.html"
        
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {format}")
        
        return {
            "content": content,
            "content_type": content_type,
            "filename": filename
        }
    
    def _generate_markdown_question(
        self,
        question,
        responses,
        code_snippets,
        options: ExportOptions
    ) -> str:
        """질문과 응답을 Markdown 형식으로 변환"""
        md = f"# 질문: {question.content}\n\n"
        
        # 메타데이터
        if options.include_metadata:
            md += "## 메타데이터\n\n"
            if options.include_tags and question.tags:
                md += f"- **태그**: {', '.join(question.tags)}\n"
            if options.include_timestamps and hasattr(question, "created_at") and question.created_at:
                md += f"- **생성 시간**: {question.created_at}\n"
            md += "\n"
        
        # 응답
        if responses:
            md += "## 응답\n\n"
            for i, response in enumerate(responses):
                md += f"### 응답 {i+1}\n\n"
                md += f"{response.content}\n\n"
                
                if options.include_metadata:
                    if options.include_llm_info and hasattr(response, "llm_type"):
                        md += f"- **LLM 유형**: {response.llm_type}\n"
                    if options.include_timestamps and hasattr(response, "created_at") and response.created_at:
                        md += f"- **생성 시간**: {response.created_at}\n"
                md += "\n"
        
        # 코드 스니펫
        if code_snippets:
            md += "## 코드 스니펫\n\n"
            for i, snippet in enumerate(code_snippets):
                md += f"### {snippet.title}\n\n"
                
                if snippet.description:
                    md += f"{snippet.description}\n\n"
                
                # 언어 결정
                language = snippet.language
                if isinstance(language, Enum):
                    language = language.value
                
                # 코드 하이라이팅
                md += f"```{language}\n{snippet.content}\n```\n\n"
                
                if options.include_metadata:
                    if options.include_tags and snippet.tags:
                        md += f"- **태그**: {', '.join(snippet.tags)}\n"
                    if options.include_llm_info and hasattr(snippet, "source_llm") and snippet.source_llm:
                        md += f"- **소스 LLM**: {snippet.source_llm}\n"
                    if options.include_timestamps:
                        if hasattr(snippet, "created_at") and snippet.created_at:
                            md += f"- **생성 시간**: {snippet.created_at}\n"
                        if hasattr(snippet, "updated_at") and snippet.updated_at:
                            md += f"- **수정 시간**: {snippet.updated_at}\n"
                    if hasattr(snippet, "version") and snippet.version:
                        md += f"- **버전**: {snippet.version}\n"
                md += "\n"
        
        return md
    
    def _generate_markdown_snippet(self, snippet, options: ExportOptions) -> str:
        """코드 스니펫을 Markdown 형식으로 변환"""
        md = f"# {snippet.title}\n\n"
        
        if snippet.description:
            md += f"{snippet.description}\n\n"
        
        # 메타데이터
        if options.include_metadata:
            md += "## 메타데이터\n\n"
            if options.include_tags and snippet.tags:
                md += f"- **태그**: {', '.join(snippet.tags)}\n"
            if options.include_llm_info and hasattr(snippet, "source_llm") and snippet.source_llm:
                md += f"- **소스 LLM**: {snippet.source_llm}\n"
            if options.include_timestamps:
                if hasattr(snippet, "created_at") and snippet.created_at:
                    md += f"- **생성 시간**: {snippet.created_at}\n"
                if hasattr(snippet, "updated_at") and snippet.updated_at:
                    md += f"- **수정 시간**: {snippet.updated_at}\n"
            if hasattr(snippet, "version") and snippet.version:
                md += f"- **버전**: {snippet.version}\n"
            if hasattr(snippet, "question_id") and snippet.question_id:
                md += f"- **관련 질문 ID**: {snippet.question_id}\n"
            if hasattr(snippet, "response_id") and snippet.response_id:
                md += f"- **관련 응답 ID**: {snippet.response_id}\n"
            md += "\n"
        
        # 언어 결정
        language = snippet.language
        if isinstance(language, Enum):
            language = language.value
        
        # 코드 하이라이팅
        md += "## 코드\n\n"
        md += f"```{language}\n{snippet.content}\n```\n\n"
        
        return md
    
    def _generate_markdown_agent_logs(self, session, logs, options: ExportOptions) -> str:
        """에이전트 로그를 Markdown 형식으로 변환"""
        md = f"# 에이전트 세션: {session.session_id}\n\n"
        
        # 세션 정보
        md += "## 세션 정보\n\n"
        md += f"- **에이전트 유형**: {session.agent_type}\n"
        md += f"- **상태**: {session.status}\n"
        if options.include_timestamps:
            if hasattr(session, "start_time") and session.start_time:
                md += f"- **시작 시간**: {session.start_time}\n"
            if hasattr(session, "end_time") and session.end_time:
                md += f"- **종료 시간**: {session.end_time}\n"
        md += f"- **총 단계 수**: {session.total_steps}\n"
        
        # 파라미터 정보
        if hasattr(session, "parameters") and session.parameters:
            md += "\n### 파라미터\n\n"
            params = session.parameters
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except:
                    pass
            
            if isinstance(params, dict):
                for key, value in params.items():
                    md += f"- **{key}**: {value}\n"
            else:
                md += f"{params}\n"
        md += "\n"
        
        # 로그 정보
        if logs:
            md += "## 로그\n\n"
            for log in logs:
                # 단계 및 단계 정보
                phase = log.phase
                if isinstance(phase, Enum):
                    phase = phase.value
                
                md += f"### 단계 {log.step}: {phase}\n\n"
                
                # 타임스탬프
                if options.include_timestamps and hasattr(log, "timestamp") and log.timestamp:
                    md += f"**시간**: {log.timestamp}\n\n"
                
                # 입력 데이터
                if hasattr(log, "input_data") and log.input_data:
                    md += "#### 입력 데이터\n\n"
                    if isinstance(log.input_data, dict):
                        for key, value in log.input_data.items():
                            md += f"- **{key}**: {value}\n"
                    else:
                        md += f"```json\n{json.dumps(log.input_data, indent=2, default=str)}\n```\n"
                    md += "\n"
                
                # 도구 호출
                if hasattr(log, "tool_calls") and log.tool_calls:
                    md += "#### 도구 호출\n\n"
                    tool_calls = log.tool_calls
                    if isinstance(tool_calls, str):
                        try:
                            tool_calls = json.loads(tool_calls)
                        except:
                            pass
                    
                    if isinstance(tool_calls, list):
                        for i, call in enumerate(tool_calls):
                            md += f"##### 도구 호출 {i+1}\n\n"
                            if isinstance(call, dict):
                                md += f"- **도구**: {call.get('name', 'Unknown')}\n"
                                md += f"- **인자**: \n```json\n{json.dumps(call.get('arguments', {}), indent=2, default=str)}\n```\n"
                            else:
                                md += f"{call}\n"
                            md += "\n"
                    else:
                        md += f"```json\n{json.dumps(tool_calls, indent=2, default=str)}\n```\n"
                    md += "\n"
                
                # 출력 데이터
                if hasattr(log, "output_data") and log.output_data:
                    md += "#### 출력 데이터\n\n"
                    if isinstance(log.output_data, dict):
                        for key, value in log.output_data.items():
                            md += f"- **{key}**: {value}\n"
                    else:
                        md += f"```json\n{json.dumps(log.output_data, indent=2, default=str)}\n```\n"
                    md += "\n"
                
                # 오류
                if hasattr(log, "error") and log.error:
                    md += "#### 오류\n\n"
                    md += f"```\n{log.error}\n```\n\n"
        
        return md