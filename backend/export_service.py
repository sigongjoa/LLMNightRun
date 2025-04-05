import json
import os
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Union

import markdown
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.operations import (
    get_code_snippets,
    get_questions,
    get_responses,
)
from backend.models import CodeLanguage, LLMType, Question, Response, CodeSnippet


class ExportFormat:
    JSON = "json"
    MARKDOWN = "markdown"
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
    
    # PDF 관련 옵션
    page_size: str = "A4"
    font_size: int = 11


class ExportService:
    """
    데이터 내보내기 기능을 제공하는 서비스 클래스
    """
    
    def __init__(self, db: Session):
        """
        ExportService 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
    
    async def export_question(
        self,
        question_id: int,
        export_format: str = ExportFormat.MARKDOWN,
        options: Optional[ExportOptions] = None
    ) -> Dict:
        """
        질문 및 관련 응답을 내보내기
        
        Args:
            question_id: 질문 ID
            export_format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            내보내기 결과 (내용 및 메타데이터)
        """
        options = options or ExportOptions()
        
        # 질문 가져오기
        question = get_questions(self.db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        # 관련 응답 가져오기
        responses = get_responses(self.db, question_id=question_id)
        
        # 관련 코드 스니펫 가져오기
        code_snippets = get_code_snippets(self.db, question_id=question_id)
        
        # 내보내기 형식에 따라 처리
        if export_format == ExportFormat.JSON:
            return self._export_to_json(question, responses, code_snippets, options)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_to_markdown(question, responses, code_snippets, options)
        elif export_format == ExportFormat.HTML:
            return self._export_to_html(question, responses, code_snippets, options)
        elif export_format == ExportFormat.PDF:
            return self._export_to_pdf(question, responses, code_snippets, options)
        elif export_format == ExportFormat.CODE_PACKAGE:
            return await self._export_to_code_package(question, responses, code_snippets, options)
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 내보내기 형식: {export_format}")
    
    async def export_code_snippet(
        self,
        snippet_id: int,
        export_format: str = ExportFormat.CODE_PACKAGE,
        options: Optional[ExportOptions] = None
    ) -> Dict:
        """
        코드 스니펫 내보내기
        
        Args:
            snippet_id: 스니펫 ID
            export_format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            내보내기 결과 (내용 및 메타데이터)
        """
        options = options or ExportOptions()
        
        # 코드 스니펫 가져오기
        snippets = get_code_snippets(self.db, snippet_id=snippet_id)
        if not snippets:
            raise HTTPException(status_code=404, detail="코드 스니펫을 찾을 수 없습니다")
        
        snippet = snippets[0]
        
        # 연관된 질문/응답 가져오기
        question = None
        response = None
        
        if snippet.question_id:
            question = get_questions(self.db, question_id=snippet.question_id, single=True)
        
        if snippet.response_id:
            responses = get_responses(self.db, response_id=snippet.response_id)
            response = responses[0] if responses else None
        
        # 내보내기 형식에 따라 처리
        if export_format == ExportFormat.JSON:
            return self._export_snippet_to_json(snippet, question, response, options)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_snippet_to_markdown(snippet, question, response, options)
        elif export_format == ExportFormat.CODE_PACKAGE:
            return await self._export_snippet_to_code_package(snippet, question, response, options)
        else:
            raise HTTPException(status_code=400, detail=f"코드 스니펫에 지원하지 않는 내보내기 형식: {export_format}")
    
    async def export_agent_logs(
        self,
        session_id: str,
        export_format: str = ExportFormat.JSON,
        options: Optional[ExportOptions] = None
    ) -> Dict:
        """
        Agent 로그 내보내기
        
        Args:
            session_id: Agent 세션 ID
            export_format: 내보내기 형식
            options: 내보내기 옵션
            
        Returns:
            내보내기 결과 (내용 및 메타데이터)
        """
        options = options or ExportOptions()
        
        # 로그 가져오기 (DB 모델 구현 필요)
        # agent_logs = get_agent_logs(self.db, session_id=session_id)
        
        # 임시 구현: 파일 기반 로그 가져오기
        log_file_path = os.path.join("storage", "logs", f"agent_{session_id}.json")
        
        if not os.path.exists(log_file_path):
            raise HTTPException(status_code=404, detail="Agent 로그를 찾을 수 없습니다")
        
        with open(log_file_path, 'r') as f:
            agent_logs = json.load(f)
        
        # 내보내기 형식에 따라 처리
        if export_format == ExportFormat.JSON:
            return self._export_logs_to_json(agent_logs, options)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_logs_to_markdown(agent_logs, options)
        elif export_format == ExportFormat.HTML:
            return self._export_logs_to_html(agent_logs, options)
        else:
            raise HTTPException(status_code=400, detail=f"Agent 로그에 지원하지 않는 내보내기 형식: {export_format}")
    
    def _export_to_json(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> Dict:
        """JSON 형식으로 내보내기"""
        question_dict = question.dict(exclude_unset=True)
        responses_list = [r.dict(exclude_unset=True) for r in responses]
        snippets_list = [s.dict(exclude_unset=True) for s in code_snippets]
        
        result = {
            "question": question_dict,
            "responses": responses_list,
            "code_snippets": snippets_list,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }
        
        return {
            "content": json.dumps(result, indent=2, ensure_ascii=False),
            "content_type": "application/json",
            "filename": f"question_{question.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        }
    
    def _export_to_markdown(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> Dict:
        """마크다운 형식으로 내보내기"""
        md_content = f"# LLM 응답 비교: {question.content[:50]}...\n\n"
        
        # 메타데이터
        if options.include_metadata:
            md_content += f"내보내기 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 질문 정보
        md_content += f"## 질문\n\n{question.content}\n\n"
        
        if options.include_tags and question.tags:
            md_content += "**태그:** " + ", ".join([f"`{tag}`" for tag in question.tags]) + "\n\n"
        
        if options.include_timestamps and question.created_at:
            md_content += f"**질문 시간:** {question.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 응답 정보
        md_content += "## 응답\n\n"
        
        for response in responses:
            # LLM 유형에 따라 아이콘 선택
            llm_icon = self._get_llm_icon(response.llm_type)
            llm_name = self._get_llm_name(response.llm_type)
            
            md_content += f"### {llm_icon} {llm_name}\n\n"
            
            if options.include_timestamps and response.created_at:
                md_content += f"**응답 시간:** {response.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            md_content += f"```\n{response.content}\n```\n\n"
        
        # 코드 스니펫 정보
        if code_snippets:
            md_content += "## 코드 스니펫\n\n"
            
            for snippet in code_snippets:
                md_content += f"### {snippet.title}\n\n"
                
                if snippet.description:
                    md_content += f"{snippet.description}\n\n"
                
                lang_code = self._get_language_code(snippet.language)
                md_content += f"```{lang_code}\n{snippet.content}\n```\n\n"
                
                if options.include_metadata:
                    if snippet.source_llm:
                        md_content += f"**출처:** {self._get_llm_name(snippet.source_llm)}\n"
                    
                    if options.include_tags and snippet.tags:
                        md_content += "**태그:** " + ", ".join([f"`{tag}`" for tag in snippet.tags]) + "\n"
                    
                    if options.include_timestamps and snippet.created_at:
                        md_content += f"**생성 시간:** {snippet.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return {
            "content": md_content,
            "content_type": "text/markdown",
            "filename": f"question_{question.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
        }
    
    def _export_to_html(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> Dict:
        """HTML 형식으로 내보내기"""
        # 먼저 마크다운 생성
        md_result = self._export_to_markdown(question, responses, code_snippets, options)
        md_content = md_result["content"]
        
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables', 'codehilite'])
        
        # HTML 템플릿에 삽입
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM 응답 비교: {question.content[:30]}...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 16px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
        }}
        h1, h2, h3 {{
            margin-top: 25px;
            margin-bottom: 16px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            padding: 8px 12px;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            text-align: left;
        }}
    </style>
</head>
<body>
    {html_content}
    <footer>
        <p><small>exported by LLMNightRun - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </footer>
</body>
</html>"""
        
        return {
            "content": html,
            "content_type": "text/html",
            "filename": f"question_{question.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.html"
        }
    
    def _export_to_pdf(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> Dict:
        """
        PDF 형식으로 내보내기
        
        참고: 이 기능은 weasyprint 또는 reportlab 라이브러리가 필요합니다.
        """
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF 내보내기 기능을 사용하려면 weasyprint 라이브러리가 필요합니다."
            )
        
        # HTML 형식으로 변환 후 PDF 생성
        html_result = self._export_to_html(question, responses, code_snippets, options)
        html_content = html_result["content"]
        
        # PDF 생성
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        css = CSS(string=f"""
            @page {{
                size: {options.page_size};
                margin: 2cm;
            }}
            body {{
                font-size: {options.font_size}pt;
            }}
        """, font_config=font_config)
        
        # PDF 파일로 저장
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
        pdf_buffer.seek(0)
        
        return {
            "content": pdf_buffer.getvalue(),
            "content_type": "application/pdf",
            "filename": f"question_{question.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        }
    
    async def _export_to_code_package(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> Dict:
        """
        코드 패키지 형식(.zip)으로 내보내기
        """
        if not code_snippets:
            raise HTTPException(status_code=400, detail="내보낼 코드 스니펫이 없습니다.")
        
        # ZIP 파일 생성
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # README.md 추가
            readme_content = self._generate_readme(question, responses, code_snippets, options)
            zip_file.writestr("README.md", readme_content)
            
            # 코드 스니펫 추가
            for i, snippet in enumerate(code_snippets):
                # 파일 이름 생성
                file_ext = self._get_file_extension(snippet.language)
                safe_title = self._sanitize_filename(snippet.title)
                file_name = f"{i+1:02d}_{safe_title[:30]}{file_ext}"
                
                # 코드 내용 추가
                zip_file.writestr(f"code/{file_name}", snippet.content)
                
                # 메타데이터 추가 (옵션)
                if options.include_metadata:
                    meta = {
                        "title": snippet.title,
                        "description": snippet.description,
                        "language": str(snippet.language),
                        "tags": snippet.tags,
                        "source_llm": str(snippet.source_llm) if snippet.source_llm else None,
                        "created_at": snippet.created_at.isoformat() if snippet.created_at else None,
                        "updated_at": snippet.updated_at.isoformat() if snippet.updated_at else None,
                    }
                    zip_file.writestr(f"meta/{file_name}.json", json.dumps(meta, indent=2))
            
            # 전체 질문-응답 JSON 추가
            json_result = self._export_to_json(question, responses, code_snippets, options)
            zip_file.writestr("data.json", json_result["content"])
        
        zip_buffer.seek(0)
        
        return {
            "content": zip_buffer.getvalue(),
            "content_type": "application/zip",
            "filename": f"code_package_{question.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
        }
    
    def _export_snippet_to_json(
        self,
        snippet: CodeSnippet,
        question: Optional[Question],
        response: Optional[Response],
        options: ExportOptions
    ) -> Dict:
        """코드 스니펫을 JSON 형식으로 내보내기"""
        snippet_dict = snippet.dict(exclude_unset=True)
        
        result = {
            "code_snippet": snippet_dict,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }
        
        if question:
            result["question"] = question.dict(exclude_unset=True)
        
        if response:
            result["response"] = response.dict(exclude_unset=True)
        
        return {
            "content": json.dumps(result, indent=2, ensure_ascii=False),
            "content_type": "application/json",
            "filename": f"snippet_{snippet.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        }
    
    def _export_snippet_to_markdown(
        self,
        snippet: CodeSnippet,
        question: Optional[Question],
        response: Optional[Response],
        options: ExportOptions
    ) -> Dict:
        """코드 스니펫을 마크다운 형식으로 내보내기"""
        md_content = f"# 코드 스니펫: {snippet.title}\n\n"
        
        # 메타데이터
        if options.include_metadata:
            md_content += f"내보내기 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 스니펫 설명
        if snippet.description:
            md_content += f"{snippet.description}\n\n"
        
        # 태그
        if options.include_tags and snippet.tags:
            md_content += "**태그:** " + ", ".join([f"`{tag}`" for tag in snippet.tags]) + "\n\n"
        
        # 언어 정보
        lang_code = self._get_language_code(snippet.language)
        lang_name = self._get_language_name(snippet.language)
        md_content += f"**언어:** {lang_name}\n\n"
        
        # 코드 블록
        md_content += f"```{lang_code}\n{snippet.content}\n```\n\n"
        
        # 원본 질문 (있는 경우)
        if question and options.include_metadata:
            md_content += "## 원본 질문\n\n"
            md_content += f"{question.content}\n\n"
            
            if options.include_timestamps and question.created_at:
                md_content += f"**질문 시간:** {question.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 원본 응답 (있는 경우)
        if response and options.include_metadata:
            md_content += "## 원본 응답\n\n"
            
            if options.include_llm_info:
                llm_icon = self._get_llm_icon(response.llm_type)
                llm_name = self._get_llm_name(response.llm_type)
                md_content += f"**응답 소스:** {llm_icon} {llm_name}\n\n"
            
            md_content += f"```\n{response.content}\n```\n\n"
            
            if options.include_timestamps and response.created_at:
                md_content += f"**응답 시간:** {response.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return {
            "content": md_content,
            "content_type": "text/markdown",
            "filename": f"snippet_{snippet.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
        }
    
    async def _export_snippet_to_code_package(
        self,
        snippet: CodeSnippet,
        question: Optional[Question],
        response: Optional[Response],
        options: ExportOptions
    ) -> Dict:
        """코드 스니펫을 코드 패키지 형식(.zip)으로 내보내기"""
        # ZIP 파일 생성
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # README.md 추가
            readme_content = self._generate_snippet_readme(snippet, question, response, options)
            zip_file.writestr("README.md", readme_content)
            
            # 코드 파일 추가
            file_ext = self._get_file_extension(snippet.language)
            safe_title = self._sanitize_filename(snippet.title)
            file_name = f"{safe_title[:30]}{file_ext}"
            zip_file.writestr(file_name, snippet.content)
            
            # 메타데이터 추가 (옵션)
            if options.include_metadata:
                meta = {
                    "title": snippet.title,
                    "description": snippet.description,
                    "language": str(snippet.language),
                    "tags": snippet.tags,
                    "source_llm": str(snippet.source_llm) if snippet.source_llm else None,
                    "created_at": snippet.created_at.isoformat() if snippet.created_at else None,
                    "updated_at": snippet.updated_at.isoformat() if snippet.updated_at else None,
                }
                zip_file.writestr("meta.json", json.dumps(meta, indent=2))
            
            # 원본 질문/응답 추가 (옵션)
            if question and options.include_metadata:
                zip_file.writestr("original_question.txt", question.content)
            
            if response and options.include_metadata:
                zip_file.writestr("original_response.txt", response.content)
        
        zip_buffer.seek(0)
        
        return {
            "content": zip_buffer.getvalue(),
            "content_type": "application/zip",
            "filename": f"snippet_{snippet.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
        }
    
    def _export_logs_to_json(
        self,
        agent_logs: List[Dict],
        options: ExportOptions
    ) -> Dict:
        """Agent 로그를 JSON 형식으로 내보내기"""
        result = {
            "agent_logs": agent_logs,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json",
                "log_count": len(agent_logs)
            }
        }
        
        session_id = agent_logs[0]["session_id"] if agent_logs else "unknown"
        
        return {
            "content": json.dumps(result, indent=2, ensure_ascii=False),
            "content_type": "application/json",
            "filename": f"agent_logs_{session_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        }
    
    def _export_logs_to_markdown(
        self,
        agent_logs: List[Dict],
        options: ExportOptions
    ) -> Dict:
        """Agent 로그를 마크다운 형식으로 내보내기"""
        session_id = agent_logs[0]["session_id"] if agent_logs else "unknown"
        agent_type = agent_logs[0]["agent_type"] if agent_logs else "unknown"
        
        md_content = f"# Agent 실행 로그\n\n"
        
        # 메타데이터
        md_content += f"- **세션 ID:** {session_id}\n"
        md_content += f"- **Agent 유형:** {agent_type}\n"
        md_content += f"- **로그 항목 수:** {len(agent_logs)}\n"
        md_content += f"- **내보내기 시간:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 타임라인 목차
        md_content += "## 타임라인\n\n"
        
        for i, log in enumerate(agent_logs):
            timestamp = log.get("timestamp", "")
            step = log.get("step", i)
            phase = log.get("phase", "unknown")
            
            md_content += f"- [Step {step}: {phase}](#step-{step})\n"
        
        md_content += "\n"
        
        # 세부 로그
        for i, log in enumerate(agent_logs):
            timestamp = log.get("timestamp", "")
            step = log.get("step", i)
            phase = log.get("phase", "unknown")
            
            md_content += f"## Step {step}: {phase} {{{step}}}\n\n"
            
            if timestamp:
                md_content += f"**시간:** {timestamp}\n\n"
            
            # 입력 데이터
            input_data = log.get("input_data")
            if input_data:
                md_content += "### 입력\n\n"
                if isinstance(input_data, str):
                    md_content += f"```\n{input_data}\n```\n\n"
                else:
                    md_content += f"```json\n{json.dumps(input_data, indent=2, ensure_ascii=False)}\n```\n\n"
            
            # 도구 호출
            tool_calls = log.get("tool_calls")
            if tool_calls:
                md_content += "### 도구 호출\n\n"
                for j, tool in enumerate(tool_calls):
                    tool_name = tool.get("name", "unknown_tool")
                    md_content += f"#### {j+1}. {tool_name}\n\n"
                    
                    args = tool.get("arguments")
                    if args:
                        md_content += "**인자:**\n\n"
                        md_content += f"```json\n{json.dumps(args, indent=2, ensure_ascii=False)}\n```\n\n"
            
            # 출력 데이터
            output_data = log.get("output_data")
            if output_data:
                md_content += "### 출력\n\n"
                if isinstance(output_data, str):
                    md_content += f"```\n{output_data}\n```\n\n"
                else:
                    md_content += f"```json\n{json.dumps(output_data, indent=2, ensure_ascii=False)}\n```\n\n"
            
            # 오류 정보
            error = log.get("error")
            if error:
                md_content += "### 오류\n\n"
                md_content += f"```\n{error}\n```\n\n"
            
            md_content += "---\n\n"
        
        return {
            "content": md_content,
            "content_type": "text/markdown",
            "filename": f"agent_logs_{session_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
        }
    
    def _export_logs_to_html(
        self,
        agent_logs: List[Dict],
        options: ExportOptions
    ) -> Dict:
        """Agent 로그를 HTML 형식으로 내보내기"""
        # 먼저 마크다운 생성
        md_result = self._export_logs_to_markdown(agent_logs, options)
        md_content = md_result["content"]
        
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables', 'codehilite'])
        
        session_id = agent_logs[0]["session_id"] if agent_logs else "unknown"
        agent_type = agent_logs[0]["agent_type"] if agent_logs else "unknown"
        
        # HTML 템플릿에 삽입
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent 로그: {agent_type} - {session_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 16px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
        }}
        h1, h2, h3 {{
            margin-top: 25px;
            margin-bottom: 16px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            padding: 8px 12px;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            text-align: left;
        }}
        .error {{
            color: #721c24;
            background-color: #f8d7da;
            padding: 10px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    {html_content}
    <footer>
        <p><small>exported by LLMNightRun - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </footer>
</body>
</html>"""
        
        return {
            "content": html,
            "content_type": "text/html",
            "filename": f"agent_logs_{session_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.html"
        }
    
    def _generate_readme(
        self,
        question: Question,
        responses: List[Response],
        code_snippets: List[CodeSnippet],
        options: ExportOptions
    ) -> str:
        """코드 패키지용 README.md 생성"""
        md_content = f"# LLM 코드 패키지\n\n"
        
        # 질문 정보
        md_content += f"## 원본 질문\n\n{question.content}\n\n"
        
        if options.include_timestamps and question.created_at:
            md_content += f"**질문 시간:** {question.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 코드 스니펫 목록
        md_content += "## 포함된 코드 스니펫\n\n"
        
        for i, snippet in enumerate(code_snippets):
            file_ext = self._get_file_extension(snippet.language)
            safe_title = self._sanitize_filename(snippet.title)
            file_name = f"{i+1:02d}_{safe_title[:30]}{file_ext}"
            
            md_content += f"### {i+1}. {snippet.title}\n\n"
            
            if snippet.description:
                md_content += f"{snippet.description}\n\n"
            
            md_content += f"**파일:** `code/{file_name}`\n\n"
            md_content += f"**언어:** {self._get_language_name(snippet.language)}\n\n"
            
            if options.include_llm_info and snippet.source_llm:
                md_content += f"**생성 모델:** {self._get_llm_name(snippet.source_llm)}\n\n"
        
        # 사용 방법
        md_content += "## 사용 방법\n\n"
        md_content += "이 패키지에는 다음 디렉토리가 포함되어 있습니다:\n\n"
        md_content += "- `code/`: 코드 스니펫 파일\n"
        
        if options.include_metadata:
            md_content += "- `meta/`: 코드 스니펫 메타데이터\n"
        
        md_content += "- `data.json`: 전체 질문-응답 데이터\n\n"
        
        # 추가 정보
        md_content += "## 추가 정보\n\n"
        md_content += f"이 코드 패키지는 LLMNightRun에 의해 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}에 생성되었습니다.\n"
        
        return md_content
    
    def _generate_snippet_readme(
        self,
        snippet: CodeSnippet,
        question: Optional[Question],
        response: Optional[Response],
        options: ExportOptions
    ) -> str:
        """단일 코드 스니펫 패키지용 README.md 생성"""
        md_content = f"# {snippet.title}\n\n"
        
        # 스니펫 설명
        if snippet.description:
            md_content += f"{snippet.description}\n\n"
        
        # 기본 정보
        md_content += "## 기본 정보\n\n"
        md_content += f"- **언어:** {self._get_language_name(snippet.language)}\n"
        md_content += f"- **파일:** `{self._sanitize_filename(snippet.title)}{self._get_file_extension(snippet.language)}`\n"
        
        if options.include_timestamps:
            md_content += f"- **생성 시간:** {snippet.created_at.strftime('%Y-%m-%d %H:%M:%S') if snippet.created_at else 'N/A'}\n"
            md_content += f"- **업데이트 시간:** {snippet.updated_at.strftime('%Y-%m-%d %H:%M:%S') if snippet.updated_at else 'N/A'}\n"
        
        if options.include_tags and snippet.tags:
            md_content += "- **태그:** " + ", ".join([f"`{tag}`" for tag in snippet.tags]) + "\n"
        
        if options.include_llm_info and snippet.source_llm:
            md_content += f"- **생성 모델:** {self._get_llm_name(snippet.source_llm)}\n"
        
        md_content += "\n"
        
        # 사용 예시 (언어별로 다름)
        md_content += "## 사용 방법\n\n"
        
        if snippet.language == CodeLanguage.PYTHON:
            md_content += "이 스니펫은 Python 코드입니다. 다음과 같이 실행할 수 있습니다:\n\n"
            md_content += "```bash\npython " + f"{self._sanitize_filename(snippet.title)}.py\n```\n\n"
        elif snippet.language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            md_content += f"이 스니펫은 {self._get_language_name(snippet.language)} 코드입니다. 다음과 같이 실행할 수 있습니다:\n\n"
            md_content += "```bash\nnode " + f"{self._sanitize_filename(snippet.title)}{self._get_file_extension(snippet.language)}\n```\n\n"
        
        # 원본 질문 (있는 경우)
        if question:
            md_content += "## 원본 질문\n\n"
            md_content += f"{question.content}\n\n"
        
        # 추가 정보
        md_content += "## 추가 정보\n\n"
        md_content += f"이 코드 스니펫은 LLMNightRun에 의해 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}에 내보내졌습니다.\n"
        
        return md_content
    
    def _get_llm_icon(self, llm_type: LLMType) -> str:
        """LLM 유형에 따른 아이콘 반환"""
        icons = {
            LLMType.OPENAI_API: "🤖",
            LLMType.OPENAI_WEB: "🌐",
            LLMType.CLAUDE_API: "🧠",
            LLMType.CLAUDE_WEB: "🌐",
            LLMType.MANUAL: "✍️"
        }
        return icons.get(llm_type, "🔄")
    
    def _get_llm_name(self, llm_type: LLMType) -> str:
        """LLM 유형에 따른 이름 반환"""
        names = {
            LLMType.OPENAI_API: "OpenAI API",
            LLMType.OPENAI_WEB: "OpenAI 웹",
            LLMType.CLAUDE_API: "Claude API",
            LLMType.CLAUDE_WEB: "Claude 웹",
            LLMType.MANUAL: "수동 입력"
        }
        return names.get(llm_type, str(llm_type))
    
    def _get_language_code(self, language: CodeLanguage) -> str:
        """언어에 따른 코드 블록 언어 식별자 반환"""
        codes = {
            CodeLanguage.PYTHON: "python",
            CodeLanguage.JAVASCRIPT: "javascript",
            CodeLanguage.TYPESCRIPT: "typescript",
            CodeLanguage.JAVA: "java",
            CodeLanguage.CSHARP: "csharp",
            CodeLanguage.CPP: "cpp",
            CodeLanguage.GO: "go",
            CodeLanguage.RUST: "rust",
            CodeLanguage.PHP: "php",
            CodeLanguage.RUBY: "ruby",
            CodeLanguage.SWIFT: "swift",
            CodeLanguage.KOTLIN: "kotlin",
            CodeLanguage.OTHER: ""
        }
        return codes.get(language, "")
    
    def _get_language_name(self, language: CodeLanguage) -> str:
        """언어에 따른 표시 이름 반환"""
        names = {
            CodeLanguage.PYTHON: "Python",
            CodeLanguage.JAVASCRIPT: "JavaScript",
            CodeLanguage.TYPESCRIPT: "TypeScript",
            CodeLanguage.JAVA: "Java",
            CodeLanguage.CSHARP: "C#",
            CodeLanguage.CPP: "C++",
            CodeLanguage.GO: "Go",
            CodeLanguage.RUST: "Rust",
            CodeLanguage.PHP: "PHP",
            CodeLanguage.RUBY: "Ruby",
            CodeLanguage.SWIFT: "Swift",
            CodeLanguage.KOTLIN: "Kotlin",
            CodeLanguage.OTHER: "기타"
        }
        return names.get(language, str(language))
    
    def _get_file_extension(self, language: CodeLanguage) -> str:
        """언어에 따른 파일 확장자 반환"""
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
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일 이름에서 특수 문자 제거"""
        # 파일 이름에 사용할 수 없는 특수 문자 제거
        sanitized = "".join(c for c in filename if c.isalnum() or c in " ._-")
        # 공백을 언더스코어로 변환
        sanitized = sanitized.replace(" ", "_")
        # 언더스코어가 연속되는 경우 하나로 통합
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        return sanitized