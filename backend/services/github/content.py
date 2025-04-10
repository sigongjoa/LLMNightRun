"""
GitHub 콘텐츠 생성 모듈

README 파일, 커밋 메시지 등 GitHub 관련 콘텐츠를 생성하는 기능을 제공합니다.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ...database.operations.question import get_questions
from ...database.operations.response import get_responses
from ...database.operations.code import get_code_snippets
from ...database.operations.settings import get_settings
from ...llm import generate_from_openai, generate_from_claude
from ...llm_studio import generate_from_local_llm


class ContentService:
    """GitHub 콘텐츠 생성 서비스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        self.settings = get_settings(db)
    
    def _get_file_extension(self, language: str) -> str:
        """
        프로그래밍 언어에 해당하는 파일 확장자를 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            파일 확장자
        """
        language_extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "jsx": "jsx",
            "tsx": "tsx",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "csharp": "cs",
            "go": "go",
            "ruby": "rb",
            "rust": "rs",
            "swift": "swift",
            "kotlin": "kt",
            "php": "php",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "sql": "sql",
            "markdown": "md",
            "shell": "sh",
            "bash": "sh",
            "powershell": "ps1",
            "json": "json",
            "yaml": "yaml",
            "xml": "xml",
            "dart": "dart",
            "r": "r"
        }
        
        return language_extensions.get(language.lower(), "txt")
    
    async def generate_commit_message(self, question_id: int) -> str:
        """
        질문과 코드 스니펫을 기반으로 적절한 커밋 메시지를 자동 생성합니다.
        
        Args:
            question_id: 질문 ID
            
        Returns:
            생성된 커밋 메시지
        """
        # 질문 조회
        question = get_questions(self.db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        
        # 코드 스니펫 조회
        code_snippets = get_code_snippets(self.db, question_id=question_id)
        code_content = ""
        
        if code_snippets:
            for snippet in code_snippets:
                code_content += f"파일명: {snippet.title}.{self._get_file_extension(snippet.language)}\n"
                code_content += f"언어: {snippet.language}\n"
                code_content += f"설명: {snippet.description or '없음'}\n"
                code_content += f"코드:\n{snippet.content}\n\n"
        
        # 프롬프트 구성
        prompt = f"""
질문과 코드를 기반으로 GitHub 커밋 메시지를 작성해주세요.
커밋 메시지는 첫 줄에 간결한 제목(50자 이내)과 그 다음 줄에 상세 설명을 포함해야 합니다.
제목은 명령형으로 작성하고 마침표를 사용하지 않습니다.

질문:
{question.content}

코드:
{code_content}

커밋 메시지:
"""
        
        try:
            # 로컬 LLM (LM Studio) 사용 시도
            try:
                from backend.config.settings import settings
                if hasattr(settings, "llm") and settings.llm.get("local_llm_enabled", False):
                    try:
                        # LM Studio를 통한 로컬 LLM 사용
                        commit_message = await generate_from_local_llm([{"role": "user", "content": prompt}])
                        if commit_message and commit_message.strip():
                            return commit_message.strip()
                    except Exception as local_e:
                        print(f"로컬 LLM 커밋 메시지 생성 오류: {str(local_e)}")
            except Exception as e:
                print(f"로컬 LLM 설정 확인 오류: {str(e)}")
                
            # 그 다음 Claude API로 시도
            if self.settings and self.settings.claude_api_key:
                commit_message = await generate_from_claude(prompt)
                return commit_message.strip()
            
            # 마지막으로 OpenAI API 사용
            elif self.settings and self.settings.openai_api_key:
                commit_message = await generate_from_openai(prompt)
                return commit_message.strip()
            
            # API 키가 설정되지 않은 경우
            else:
                return f"Add code for question #{question_id}"
        
        except Exception as e:
            print(f"커밋 메시지 생성 오류: {str(e)}")
            return f"Add code for question #{question_id}"
    
    async def generate_readme(self, question_id: int) -> str:
        """
        질문과 코드 스니펫을 기반으로 README.md 파일을 자동 생성합니다.
        
        Args:
            question_id: 질문 ID
            
        Returns:
            생성된 README 내용
        """
        # 질문 조회
        question = get_questions(self.db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        
        # 응답 조회
        responses = get_responses(self.db, question_id=question_id)
        
        # 코드 스니펫 조회
        code_snippets = get_code_snippets(self.db, question_id=question_id)
        
        # 프롬프트 구성
        prompt = f"""
질문, 응답, 코드 스니펫을 기반으로 프로젝트 README.md 파일을 작성해주세요.
README는 마크다운 형식으로 작성해주세요.

README에 포함되어야 할 내용:
1. 프로젝트 제목
2. 개요 (질문에서 추출)
3. 주요 기능
4. 설치 방법 (필요한 경우)
5. 사용 방법
6. 코드 구조 설명
7. 주의사항 (있는 경우)

질문:
{question.content}
"""
        
        # 응답 내용 추가
        if responses:
            prompt += "응답:\n"
            for i, response in enumerate(responses):
                prompt += f"응답 {i+1}:\n{response.content[:1000]}...\n\n"  # 응답 내용 축소
        
        # 코드 스니펫 추가
        if code_snippets:
            prompt += "코드 스니펫:\n"
            for i, snippet in enumerate(code_snippets):
                prompt += f"스니펫 {i+1}:\n"
                prompt += f"제목: {snippet.title}\n"
                prompt += f"언어: {snippet.language}\n"
                
                # 스니펫 내용 축소
                content_preview = snippet.content[:500] + ("..." if len(snippet.content) > 500 else "")
                prompt += f"코드:\n{content_preview}\n\n"
        
        prompt += "\nREADME.md:"
        
        try:
            # 로컬 LLM 사용을 우선적으로 시도
            try:
                from backend.config.settings import settings
                if hasattr(settings, "llm") and settings.llm.get("local_llm_enabled", False):
                    try:
                        readme_content = await generate_from_local_llm([{"role": "user", "content": prompt}])
                        if readme_content and readme_content.strip():
                            return readme_content.strip()
                    except Exception as local_e:
                        print(f"로컬 LLM README 생성 오류: {str(local_e)}")
            except Exception as e:
                print(f"로컬 LLM 설정 확인 오류: {str(e)}")
            
            # 백업 방법: 간단한 README 생성
            try:
                # 안전하게 제목 추출 시도
                question_title = question.content.split('\n')[0] if '\n' in question.content else question.content[:50]
                question_title = question_title.strip()
                if not question_title:
                    question_title = f"프로젝트 {question_id}"
                
                # 기본 README 템플릿 생성
                readme_content = f"""# {question_title}

## 개요
{question.content[:200]}...

## 주요 기능
"""
                
                # 코드 스니펫 기반 기능 추가
                if code_snippets:
                    for snippet in code_snippets:
                        snippet_title = snippet.title if snippet.title else "코드 스니펫"
                        readme_content += f"- {snippet_title}\n"
                    
                    # 설치 및 사용 방법 섹션 추가
                    readme_content += "\n## 설치 방법\n```\n# 의존성 설치\npip install -r requirements.txt\n```\n\n"
                    readme_content += "## 사용 방법\n```\n# 예시 실행\npython main.py\n```\n\n"
                    
                    # 코드 구조 설명
                    readme_content += "## 코드 구조\n"
                    for snippet in code_snippets:
                        snippet_title = snippet.title if snippet.title else "코드 스니펫"
                        snippet_desc = snippet.description if snippet.description else "코드 스니펫"
                        readme_content += f"- **{snippet_title}** - {snippet_desc}\n"
            except Exception as inner_e:
                print(f"README 백업 생성 오류: {str(inner_e)}")
                # 최후의 백업
                readme_content = f"# 질문 {question_id}\n\n{question.content[:500]}..."
            
            return readme_content
        
        except Exception as e:
            print(f"README 생성 오류: {str(e)}")
            return f"# Question {question_id}\n\n{question.content}"
    
    async def prepare_files(self, question_id: int, folder_path: Optional[str] = None) -> list:
        """
        질문에 연결된 코드 스니펫을 GitHub에 업로드하기 위한 파일 목록을 준비합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 저장할 폴더 경로 (선택 사항)
            
        Returns:
            업로드할 파일 목록
        """
        # 질문 조회
        question = get_questions(self.db, question_id=question_id, single=True)
        if not question:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
        
        # 코드 스니펫 조회
        code_snippets = get_code_snippets(self.db, question_id=question_id)
        if not code_snippets:
            raise HTTPException(status_code=404, detail=f"질문 ID {question_id}에 연결된 코드 스니펫이 없습니다")
        
        # 폴더 경로 설정
        if not folder_path:
            folder_path = f"question_{question_id}"
        
        # 경로 시작과 끝의 슬래시 처리
        folder_path = folder_path.strip('/')
        if folder_path:
            folder_path += '/'
        
        # README.md 생성
        readme_content = await self.generate_readme(question_id)
        
        # 파일 업로드를 위한 데이터 준비
        files_to_upload = []
        
        # README.md 추가
        files_to_upload.append({
            "path": f"{folder_path}README.md",
            "content": readme_content
        })
        
        # 코드 스니펫 파일 추가
        for snippet in code_snippets:
            extension = self._get_file_extension(snippet.language)
            file_name = f"{snippet.title.replace(' ', '_')}.{extension}"
            
            files_to_upload.append({
                "path": f"{folder_path}{file_name}",
                "content": snippet.content
            })
        
        return files_to_upload
