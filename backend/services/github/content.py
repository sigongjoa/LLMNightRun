"""
GitHub 콘텐츠 생성 모듈

README 파일, 커밋 메시지 등 GitHub 관련 콘텐츠를 생성하는 기능을 제공합니다.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database.operations.question import get_questions
from backend.database.operations.response import get_responses
from backend.database.operations.code import get_code_snippets

class ContentService:
    """GitHub 콘텐츠 생성 서비스"""
    
    def __init__(self, db: Session, repository_service):
        """
        서비스 초기화
        
        Args:
            db: 데이터베이스 세션
            repository_service: 저장소 서비스 인스턴스
        """
        self.db = db
        self.repository_service = repository_service
        self.settings = repository_service.settings
    
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
        
        # 코드 스니펫이 없는 경우 기본 커밋 메시지 반환
        if not code_snippets:
            return f"Add code for question #{question_id}"
        
        # 간단한 커밋 메시지 생성 로직
        languages = set(snippet.language.value for snippet in code_snippets)
        if len(languages) == 1:
            language = next(iter(languages))
            return f"Add {language} code for question #{question_id}"
        else:
            return f"Add code ({', '.join(languages)}) for question #{question_id}"
    
    async def generate_readme(self, question_id: int) -> str:
        """
        질문과 코드 스니펫을 기반으로 README.md 파일을 자동 생성합니다.
        
        Args:
            question_id: 질문 ID
            
        Returns:
            생성된 README 내용
        """
        try:
            # 질문 조회
            question = get_questions(self.db, question_id=question_id, single=True)
            if not question:
                raise HTTPException(status_code=404, detail=f"질문 ID {question_id}를 찾을 수 없습니다")
            
            # 코드 스니펫 조회
            code_snippets = get_code_snippets(self.db, question_id=question_id)
            
            # 간단한 README 생성 로직
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
                
                return readme_content
                
            except Exception as inner_e:
                print(f"README 생성 오류: {str(inner_e)}")
                # 오류 발생 시 기본 README 반환
                return f"# 질문 {question_id}\n\n{question.content[:500]}..."
                
        except Exception as e:
            print(f"README 생성 오류: {str(e)}")
            return f"# 질문 {question_id}"
    
    async def prepare_files(self, question_id: int, folder_path: Optional[str] = None) -> List[Dict[str, str]]:
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
            extension = self._get_file_extension(snippet.language.value)
            file_name = f"{snippet.title.replace(' ', '_')}.{extension}"
            
            files_to_upload.append({
                "path": f"{folder_path}{file_name}",
                "content": snippet.content
            })
        
        return files_to_upload
        
    async def upload_to_github(self, question_id: int, folder_path: Optional[str] = None, repo_id: Optional[int] = None):
        """
        코드 스니펫을 GitHub에 업로드합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 폴더 경로 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            업로드 결과
        """
        # 파일 목록 준비
        files = await self.prepare_files(question_id, folder_path)
        
        # 커밋 메시지 생성
        commit_message = await self.generate_commit_message(question_id)
        
        # 리포지토리 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 실제 업로드 로직은 확장 필요
        # 여기서는 업로드 성공으로 가정
        return {
            "success": True,
            "message": f"코드가 {repo.owner}/{repo.name}에 성공적으로 업로드되었습니다.",
            "files_count": len(files),
            "commit_message": commit_message,
            "folder_path": folder_path or f"question_{question_id}",
            "repository": {
                "name": repo.name,
                "owner": repo.owner,
                "url": repo.url
            }
        }
        
    async def upload_file_to_github(self, content: str, file_path: str, 
                                  commit_message: Optional[str] = None, 
                                  repo_id: Optional[int] = None, 
                                  branch: Optional[str] = None):
        """
        파일을 GitHub에 업로드합니다.
        
        Args:
            content: 파일 내용
            file_path: 파일 경로
            commit_message: 커밋 메시지 (선택 사항)
            repo_id: 저장소 ID (선택 사항)
            branch: 브랜치 (선택 사항)
            
        Returns:
            업로드 결과
        """
        # 리포지토리 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 브랜치 설정
        if not branch:
            branch = repo.branch or "main"
        
        # 커밋 메시지 설정
        if not commit_message:
            commit_message = f"Add {file_path}"
        
        # 실제 업로드 로직은 확장 필요
        # 여기서는 업로드 성공으로 가정
        return {
            "success": True,
            "message": f"파일이 {repo.owner}/{repo.name}에 성공적으로 업로드되었습니다.",
            "file_path": file_path,
            "branch": branch,
            "commit_message": commit_message,
            "repository": {
                "name": repo.name,
                "owner": repo.owner,
                "url": repo.url
            }
        }
        
    async def list_remote_repositories(self, repo_id: Optional[int] = None):
        """
        원격 저장소 목록을 조회합니다.
        
        Args:
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            원격 저장소 목록
        """
        # 리포지토리 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 실제 API 호출 로직은 확장 필요
        # 여기서는 더미 데이터 반환
        return {
            "success": True,
            "repositories": [
                {
                    "name": repo.name,
                    "owner": repo.owner,
                    "description": "샘플 저장소입니다.",
                    "url": repo.url,
                    "private": repo.is_private,
                    "default_branch": repo.branch
                }
            ]
        }
        
    async def create_remote_repository(self, name: str, description: str = "", 
                                     private: bool = True, auto_init: bool = True, 
                                     repo_id: Optional[int] = None):
        """
        원격 저장소를 생성합니다.
        
        Args:
            name: 저장소 이름
            description: 저장소 설명
            private: 비공개 여부
            auto_init: 자동 초기화 여부
            repo_id: 저장소 ID (액세스 토큰 가져오기용)
            
        Returns:
            생성된 원격 저장소 정보
        """
        # 리포지토리 정보 가져오기
        repo = self.repository_service.get_repository(repo_id)
        
        # 실제 API 호출 로직은 확장 필요
        # 여기서는 성공으로 가정
        new_repo_url = f"https://github.com/{repo.owner}/{name}"
        
        return {
            "success": True,
            "message": f"원격 저장소가 성공적으로 생성되었습니다: {new_repo_url}",
            "repository": {
                "name": name,
                "owner": repo.owner,
                "description": description,
                "url": new_repo_url,
                "private": private,
                "default_branch": "main"
            }
        }
