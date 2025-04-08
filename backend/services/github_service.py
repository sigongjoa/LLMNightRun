"""
GitHub 서비스 모듈

GitHub 리포지토리에 파일을 업로드하고 커밋 메시지를 자동 생성하는 기능을 제공합니다.
또한 저장소 목록 조회, 저장소 생성, 문서 생성 등의 GitHub 관련 기능을 제공합니다.
"""

import os
import base64
import json
import requests
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import BaseModel

from ..database.operations.question import get_questions
from ..database.operations.response import get_responses
from ..database.operations.code import get_code_snippets
from ..database.operations.settings import get_settings
from ..llm import generate_from_openai, generate_from_claude
from ..llm_studio import generate_from_local_llm


class GitHubService:
    """GitHub 서비스 클래스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        self.settings = get_settings(db)
        
        if not self.settings or not self.settings.github_token:
            raise HTTPException(status_code=400, detail="GitHub 토큰이 설정되지 않았습니다. 설정에서 GitHub 토큰을 먼저 설정해주세요.")
        
        if not self.settings.github_username or not self.settings.github_repo:
            raise HTTPException(status_code=400, detail="GitHub 계정 및 리포지토리 정보가 설정되지 않았습니다. 설정에서 정보를 먼저 설정해주세요.")
        
        self.github_token = self.settings.github_token
        self.github_username = self.settings.github_username
        self.github_repo = self.settings.github_repo
        
        # GitHub API 기본 설정
        self.api_base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
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
            if self.settings.claude_api_key:
                commit_message = await generate_from_claude(prompt)
                return commit_message.strip()
            
            # 마지막으로 OpenAI API 사용
            elif self.settings.openai_api_key:
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
                prompt += f"응답 {i+1}:\n{response.content}\n\n"
        
        # 코드 스니펫 추가
        if code_snippets:
            prompt += "코드 스니펫:\n"
            for i, snippet in enumerate(code_snippets):
                prompt += f"스니펫 {i+1}:\n"
                prompt += f"제목: {snippet.title}\n"
                prompt += f"언어: {snippet.language}\n"
                prompt += f"설명: {snippet.description or '없음'}\n"
                prompt += f"코드:\n{snippet.content}\n\n"
        
        prompt += "\nREADME.md:"
        
        try:
            # 로컬 LLM (LM Studio) 사용 시도
            try:
                from backend.config.settings import settings
                if hasattr(settings, "llm") and settings.llm.get("local_llm_enabled", False):
                    try:
                        # LM Studio를 통한 로컬 LLM 사용
                        readme_content = await generate_from_local_llm([{"role": "user", "content": prompt}])
                        if readme_content and readme_content.strip():
                            return readme_content.strip()
                    except Exception as local_e:
                        print(f"로컬 LLM README 생성 오류: {str(local_e)}")
            except Exception as e:
                print(f"로컬 LLM 설정 확인 오류: {str(e)}")
            
            # 그 다음 Claude API로 시도
            if self.settings.claude_api_key:
                readme_content = await generate_from_claude(prompt)
                return readme_content.strip()
            
            # 마지막으로 OpenAI API 사용
            elif self.settings.openai_api_key:
                readme_content = await generate_from_openai(prompt)
                return readme_content.strip()
            
            # API 키가 설정되지 않은 경우
            else:
                return f"# Question {question_id}\n\n{question.content}"
        
        except Exception as e:
            print(f"README 생성 오류: {str(e)}")
            return f"# Question {question_id}\n\n{question.content}"
    
    async def upload_to_github(self, question_id: int, folder_path: Optional[str] = None) -> Dict[str, str]:
        """
        질문에 연결된 코드 스니펫을 GitHub 리포지토리에 업로드합니다.
        
        Args:
            question_id: 질문 ID
            folder_path: 저장할 폴더 경로 (선택 사항)
            
        Returns:
            업로드 결과 정보
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
        
        # 커밋 메시지 생성
        commit_message = await self.generate_commit_message(question_id)
        
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
        
        # 파일 업로드
        try:
            # 현재 리포지토리의 기본 브랜치 정보 가져오기
            repo_info_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}"
            repo_response = requests.get(repo_info_url, headers=self.headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            default_branch = repo_data["default_branch"]
            
            # 최신 커밋 SHA 가져오기
            reference_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/refs/heads/{default_branch}"
            ref_response = requests.get(reference_url, headers=self.headers)
            ref_response.raise_for_status()
            ref_data = ref_response.json()
            base_sha = ref_data["object"]["sha"]
            
            # 최신 커밋의 트리 가져오기
            commit_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/commits/{base_sha}"
            commit_response = requests.get(commit_url, headers=self.headers)
            commit_response.raise_for_status()
            commit_data = commit_response.json()
            base_tree_sha = commit_data["tree"]["sha"]
            
            # 새 트리 생성
            tree_entries = []
            for file_data in files_to_upload:
                # 파일 blob 생성
                blob_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/blobs"
                blob_data = {
                    "content": file_data["content"],
                    "encoding": "utf-8"
                }
                blob_response = requests.post(blob_url, headers=self.headers, json=blob_data)
                blob_response.raise_for_status()
                blob_sha = blob_response.json()["sha"]
                
                # 트리 항목 추가
                tree_entries.append({
                    "path": file_data["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
            
            # 새 트리 생성
            tree_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/trees"
            tree_data = {
                "base_tree": base_tree_sha,
                "tree": tree_entries
            }
            tree_response = requests.post(tree_url, headers=self.headers, json=tree_data)
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]
            
            # 새 커밋 생성
            new_commit_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/commits"
            commit_data = {
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_sha]
            }
            commit_response = requests.post(new_commit_url, headers=self.headers, json=commit_data)
            commit_response.raise_for_status()
            new_commit_sha = commit_response.json()["sha"]
            
            # reference 업데이트
            update_ref_url = f"{self.api_base_url}/repos/{self.github_username}/{self.github_repo}/git/refs/heads/{default_branch}"
            update_data = {
                "sha": new_commit_sha,
                "force": False
            }
            update_response = requests.patch(update_ref_url, headers=self.headers, json=update_data)
            update_response.raise_for_status()
            
            # 결과 반환
            return {
                "message": "파일이 성공적으로 GitHub에 업로드되었습니다.",
                "repo_url": f"https://github.com/{self.github_username}/{self.github_repo}",
                "folder_path": folder_path,
                "commit_message": commit_message
            }
        
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def list_repositories(self) -> List[Dict[str, Any]]:
        """
        사용자의 GitHub 저장소 목록을 가져옵니다.
        
        Returns:
            저장소 목록 (이름, 설명, URL 등)
        """
        try:
            # GitHub API 호출
            repos_url = f"{self.api_base_url}/user/repos?sort=updated&per_page=100"
            response = requests.get(repos_url, headers=self.headers)
            response.raise_for_status()
            
            # 결과 파싱
            repos = response.json()
            result = []
            
            for repo in repos:
                result.append({
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "default_branch": repo["default_branch"],
                    "private": repo["private"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "language": repo["language"],
                    "size": repo["size"]
                })
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def create_repository(self, name: str, description: str = "", private: bool = True, auto_init: bool = True) -> Dict[str, Any]:
        """
        새 GitHub 저장소를 생성합니다.
        
        Args:
            name: 저장소 이름
            description: 저장소 설명
            private: 비공개 여부
            auto_init: README.md 파일로 초기화 여부
            
        Returns:
            생성된 저장소 정보
        """
        try:
            # GitHub API 호출
            create_url = f"{self.api_base_url}/user/repos"
            data = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": auto_init
            }
            
            response = requests.post(create_url, headers=self.headers, json=data)
            response.raise_for_status()
            
            # 결과 파싱
            repo = response.json()
            
            return {
                "message": "저장소가 성공적으로 생성되었습니다.",
                "name": repo["name"],
                "full_name": repo["full_name"],
                "url": repo["html_url"],
                "description": repo["description"],
                "private": repo["private"],
                "default_branch": repo["default_branch"]
            }
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def upload_to_github(
        self, 
        content: str, 
        repo_name: str, 
        file_path: Optional[str] = None, 
        commit_message: Optional[str] = None,
        is_private: bool = True,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        코드 또는 텍스트를 GitHub 저장소에 업로드합니다.
        
        Args:
            content: 업로드할 내용
            repo_name: 저장소 이름
            file_path: 파일 경로 (없을 경우 기본값 사용)
            commit_message: 커밋 메시지 (없을 경우 기본값 사용)
            is_private: 저장소 생성 시 비공개 여부
            branch: 브랜치 이름
            
        Returns:
            업로드 결과 정보
        """
        try:
            if not file_path:
                file_path = "generated_content.txt"
            
            if not commit_message:
                commit_message = "LLMNightRun에서 업로드된 파일"
            
            # 저장소 존재 여부 확인
            repo_info_url = f"{self.api_base_url}/repos/{self.github_username}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=self.headers)
            
            # 저장소가 없으면 생성
            if repo_response.status_code == 404:
                await self.create_repository(
                    name=repo_name,
                    description="LLMNightRun에서 생성된 저장소",
                    private=is_private,
                    auto_init=True
                )
            else:
                repo_response.raise_for_status()
            
            # 파일 존재 여부 확인
            file_url = f"{self.api_base_url}/repos/{self.github_username}/{repo_name}/contents/{file_path}"
            file_params = {"ref": branch}
            file_response = requests.get(file_url, headers=self.headers, params=file_params)
            file_exists = file_response.status_code == 200
            
            # 파일 업로드 또는 업데이트
            upload_data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": branch
            }
            
            # 기존 파일 업데이트라면 SHA 추가
            if file_exists:
                upload_data["sha"] = file_response.json()["sha"]
            
            # API 요청 보내기
            upload_response = requests.put(file_url, headers=self.headers, json=upload_data)
            upload_response.raise_for_status()
            result = upload_response.json()
            
            return {
                "message": "파일이 성공적으로 GitHub에 업로드되었습니다.",
                "repo_url": f"https://github.com/{self.github_username}/{repo_name}",
                "file_url": result["content"]["html_url"],
                "file_path": file_path,
                "commit_message": commit_message
            }
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"GitHub API 오류: {error_message}")
    
    async def generate_documentation(
        self,
        code: Optional[str] = None,
        snippet_id: Optional[int] = None,
        repo_url: Optional[str] = None,
        doc_format: str = "markdown",
        include_examples: bool = True,
        upload_to_github: bool = False,
        repo_name: Optional[str] = None,
        file_path: Optional[str] = "docs/README.md"
    ) -> Dict[str, Any]:
        """
        코드 기반으로 문서를 생성하고 선택적으로 GitHub에 업로드합니다.
        
        Args:
            code: 문서 생성 대상 코드
            snippet_id: 문서 생성 대상 코드 스니펫 ID
            repo_url: 문서 생성 대상 저장소 URL
            doc_format: 문서 형식 (markdown, html, restructuredtext)
            include_examples: 예제 코드 포함 여부
            upload_to_github: GitHub 업로드 여부
            repo_name: 업로드할 저장소 이름
            file_path: 업로드할 파일 경로
            
        Returns:
            생성된 문서 정보 및 GitHub URL
        """
        # 문서 생성 대상 코드 확보
        document_code = ""
        
        if code:
            document_code = code
        elif snippet_id:
            # 코드 스니펫 조회
            code_snippet = get_code_snippets(self.db, snippet_id=snippet_id, single=True)
            if not code_snippet:
                raise HTTPException(status_code=404, detail=f"코드 스니펫 ID {snippet_id}를 찾을 수 없습니다")
            
            document_code = code_snippet.content
        elif repo_url:
            # 저장소 코드 분석 및 문서 생성 로직 (생략 - 실제 구현 시 저장소 클론 후 분석 필요)
            raise HTTPException(status_code=400, detail="저장소 기반 문서 생성은 아직 지원되지 않습니다")
        else:
            raise HTTPException(status_code=400, detail="문서 생성을 위한 코드, 스니펫 ID 또는 저장소 URL이 필요합니다")
        
        # 문서 형식에 따른 프롬프트 구성
        format_instructions = ""
        if doc_format == "markdown":
            format_instructions = "마크다운 형식으로 작성해주세요."
        elif doc_format == "html":
            format_instructions = "HTML 형식으로 작성해주세요."
        elif doc_format == "restructuredtext":
            format_instructions = "reStructuredText 형식으로 작성해주세요."
        else:
            format_instructions = "마크다운 형식으로 작성해주세요."
        
        # 예제 코드 관련 지침
        examples_instructions = "코드의 각 부분에 대한 사용 예제를 포함해주세요." if include_examples else ""
        
        # 프롬프트 구성
        prompt = f"""
다음 코드를 분석하여 자세한 개발 문서를 작성해주세요. {format_instructions}

문서에 포함되어야 할 내용:
1. 코드 개요 및 목적
2. 주요 기능 및 구성 요소 설명
3. 각 함수/클래스/메서드에 대한 상세 설명 (파라미터, 반환값, 예외 등)
4. 사용 방법
5. 의존성 및 요구 사항
{examples_instructions}

코드:
```
{document_code}
```

개발 문서:
"""
        
        try:
            # 로컬 LLM (LM Studio) 사용 시도
            try:
                from backend.config.settings import settings
                if hasattr(settings, "llm") and settings.llm.get("local_llm_enabled", False):
                    try:
                        # LM Studio를 통한 로컬 LLM 사용
                        documentation = await generate_from_local_llm([{"role": "user", "content": prompt}])
                        if documentation and documentation.strip():
                            doc_content = documentation.strip()
                        else:
                            raise Exception("로컬 LLM이 문서를 생성하지 못했습니다")
                    except Exception as local_e:
                        print(f"로컬 LLM 문서 생성 오류: {str(local_e)}")
                        raise
            except Exception as e:
                print(f"로컬 LLM 설정 확인 오류: {str(e)}")
                
                # 그 다음 Claude API로 시도
                if self.settings.claude_api_key:
                    documentation = await generate_from_claude(prompt)
                    doc_content = documentation.strip()
                
                # 마지막으로 OpenAI API 사용
                elif self.settings.openai_api_key:
                    documentation = await generate_from_openai(prompt)
                    doc_content = documentation.strip()
                
                # API 키가 설정되지 않은 경우
                else:
                    raise HTTPException(status_code=400, detail="문서 생성을 위한 LLM API 키가 설정되지 않았습니다")
            
            # 결과
            result = {
                "message": "문서가 성공적으로 생성되었습니다.",
                "format": doc_format,
                "content": doc_content
            }
            
            # GitHub 업로드 if 요청됨
            if upload_to_github and repo_name:
                upload_result = await self.upload_to_github(
                    content=doc_content,
                    repo_name=repo_name,
                    file_path=file_path,
                    commit_message="문서 생성: LLMNightRun에서 자동 생성된 문서"
                )
                
                result["github_url"] = upload_result["file_url"]
                result["repo_url"] = upload_result["repo_url"]
            
            return result
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            
            print(f"문서 생성 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"문서 생성 오류: {str(e)}")
    
    def _get_file_extension(self, language: str) -> str:
        """언어에 따른 파일 확장자 반환"""
        language_map = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "csharp": "cs",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rust": "rs",
            "php": "php",
            "ruby": "rb",
            "swift": "swift",
            "kotlin": "kt",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "yaml": "yml",
            "json": "json",
            "xml": "xml",
            "markdown": "md",
            "shell": "sh",
            "bash": "sh",
            "powershell": "ps1"
        }
        
        # 항상 소문자로 변환하여 비교
        language_lower = language.lower()
        return language_map.get(language_lower, "txt")