import os
import base64
import requests
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models import Question, Response, LLMType
from backend.database.operations import get_settings
from backend.database.connection import SessionLocal

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_github_settings():
    """데이터베이스에서 GitHub 설정을 가져옵니다."""
    db = SessionLocal()
    try:
        settings = get_settings(db)
        if settings:
            return {
                "github_token": settings.github_token,
                "github_repo": settings.github_repo,
                "github_username": settings.github_username
            }
        return {}
    finally:
        db.close()

def format_responses_to_markdown(question: Question, responses: List[Response]) -> str:
    """
    질문과 응답을 마크다운 형식으로 변환합니다.
    
    Args:
        question: 질문 객체
        responses: 응답 객체 리스트
        
    Returns:
        마크다운 형식의 문자열
    """
    # 현재 시간
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # 마크다운 헤더
    markdown = f"# LLM 응답 비교\n\n"
    markdown += f"생성 시간: {current_time}\n\n"
    
    # 질문 부분
    markdown += f"## 질문\n\n"
    markdown += f"{question.content}\n\n"
    
    if question.tags and len(question.tags) > 0:
        markdown += "**태그:** " + ", ".join([f"`{tag}`" for tag in question.tags]) + "\n\n"
    
    # 각 LLM 응답
    markdown += f"## 응답\n\n"
    
    for response in responses:
        # LLM 유형에 따라 아이콘 선택
        icon = ""
        if response.llm_type == LLMType.OPENAI_API:
            icon = "🤖 OpenAI API"
        elif response.llm_type == LLMType.OPENAI_WEB:
            icon = "🌐 OpenAI 웹"
        elif response.llm_type == LLMType.CLAUDE_API:
            icon = "🧠 Claude API"
        elif response.llm_type == LLMType.CLAUDE_WEB:
            icon = "🌐 Claude 웹"
        elif response.llm_type == LLMType.MANUAL:
            icon = "✍️ 수동 입력"
        
        # 생성 시간
        response_time = response.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if response.created_at else "알 수 없음"
        
        markdown += f"### {icon}\n\n"
        markdown += f"**생성 시간:** {response_time}\n\n"
        markdown += f"```\n{response.content}\n```\n\n"
    
    # 비교 및 분석 (필요 시 추가)
    markdown += f"## 비교 분석\n\n"
    markdown += f"_자동 생성된 문서입니다._\n\n"
    
    return markdown

def upload_to_github(question: Question, responses: List[Response]) -> str:
    """
    질문과 응답을 GitHub에 업로드합니다.
    
    Args:
        question: 질문 객체
        responses: 응답 객체 리스트
        
    Returns:
        업로드된 파일의 URL
    """
    # GitHub 설정 가져오기
    settings = get_github_settings()
    github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
    github_repo = settings.get("github_repo") or os.getenv("GITHUB_REPO")
    github_username = settings.get("github_username") or os.getenv("GITHUB_USERNAME")
    
    if not all([github_token, github_repo, github_username]):
        raise ValueError("GitHub 설정이 완료되지 않았습니다.")
    
    # API 헤더
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 마크다운 변환
    markdown_content = format_responses_to_markdown(question, responses)
    
    # 파일 이름 생성 (타임스탬프 포함)
    timestamp = int(time.time())
    # 질문의 첫 20자를 파일명으로 사용 (특수문자 제거)
    question_prefix = ''.join(c for c in question.content[:20] if c.isalnum() or c.isspace()).strip().replace(' ', '_')
    filename = f"responses/{question_prefix}_{timestamp}.md"
    
    # GitHub API URL
    api_url = f"https://api.github.com/repos/{github_username}/{github_repo}/contents/{filename}"
    
    # 파일 내용을 Base64로 인코딩
    encoded_content = base64.b64encode(markdown_content.encode("utf-8")).decode("utf-8")
    
    # 커밋 데이터
    data = {
        "message": f"Add LLM comparison for: {question.content[:50]}...",
        "content": encoded_content,
        "branch": "main"  # 또는 다른 브랜치
    }
    
    try:
        # API 요청
        response = requests.put(api_url, headers=headers, data=json.dumps(data))
        
        if response.status_code not in [200, 201]:
            logger.error(f"GitHub API 오류: {response.status_code}, {response.text}")
            raise Exception(f"GitHub 업로드 실패: {response.status_code}")
        
        # 생성된 파일의 URL 반환
        result = response.json()
        return result.get("content", {}).get("html_url", "")
    except Exception as e:
        logger.error(f"GitHub 업로드 중 오류 발생: {str(e)}")
        raise

def upload_code_to_github(
    code_content: str,
    filename: str,
    commit_message: str,
    branch_name: Optional[str] = None
) -> Optional[str]:
    """
    코드 파일을 GitHub에 업로드합니다.
    
    Args:
        code_content: 업로드할 코드 내용
        filename: 파일 이름 (경로 포함)
        commit_message: 커밋 메시지
        branch_name: 브랜치 이름 (선택 사항, 기본값: main)
        
    Returns:
        업로드된 파일의 URL 또는 None (실패 시)
    """
    # GitHub 설정 가져오기
    settings = get_github_settings()
    github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
    github_repo = settings.get("github_repo") or os.getenv("GITHUB_REPO")
    github_username = settings.get("github_username") or os.getenv("GITHUB_USERNAME")
    
    if not all([github_token, github_repo, github_username]):
        raise ValueError("GitHub 설정이 완료되지 않았습니다.")
    
    # 브랜치 설정
    if not branch_name:
        branch_name = "main"
    
    # API 헤더
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # GitHub API URL
    api_url = f"https://api.github.com/repos/{github_username}/{github_repo}/contents/{filename}"
    
    # 파일 내용을 Base64로 인코딩
    encoded_content = base64.b64encode(code_content.encode("utf-8")).decode("utf-8")
    
    # 커밋 데이터
    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch_name
    }
    
    try:
        # 기존 파일 확인 (선택 사항)
        check_response = requests.get(api_url, headers=headers, params={"ref": branch_name})
        
        if check_response.status_code == 200:
            # 파일이 이미 존재하는 경우, SHA 포함
            sha = check_response.json().get("sha")
            data["sha"] = sha
        
        # API 요청
        response = requests.put(api_url, headers=headers, data=json.dumps(data))
        
        if response.status_code not in [200, 201]:
            logger.error(f"GitHub API 오류: {response.status_code}, {response.text}")
            return None
        
        # 생성된 파일의 URL 반환
        result = response.json()
        return result.get("content", {}).get("html_url")
    except Exception as e:
        logger.error(f"GitHub 업로드 중 오류 발생: {str(e)}")
        return None

def create_github_branch(branch_name: str) -> bool:
    """
    GitHub에 새 브랜치를 생성합니다.
    
    Args:
        branch_name: 생성할 브랜치 이름
        
    Returns:
        성공 여부를 나타내는 불리언 값
    """
    # GitHub 설정 가져오기
    settings = get_github_settings()
    github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
    github_repo = settings.get("github_repo") or os.getenv("GITHUB_REPO")
    github_username = settings.get("github_username") or os.getenv("GITHUB_USERNAME")
    
    if not all([github_token, github_repo, github_username]):
        raise ValueError("GitHub 설정이 완료되지 않았습니다.")
    
    # API 헤더
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # 1. 현재 main 브랜치의 최신 커밋 SHA 가져오기
        sha_url = f"https://api.github.com/repos/{github_username}/{github_repo}/git/refs/heads/main"
        sha_response = requests.get(sha_url, headers=headers)
        
        if sha_response.status_code != 200:
            logger.error(f"GitHub API 오류: {sha_response.status_code}, {sha_response.text}")
            return False
        
        sha = sha_response.json()["object"]["sha"]
        
        # 2. 새 브랜치 생성
        branch_url = f"https://api.github.com/repos/{github_username}/{github_repo}/git/refs"
        branch_data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        
        branch_response = requests.post(branch_url, headers=headers, data=json.dumps(branch_data))
        
        if branch_response.status_code != 201:
            logger.error(f"GitHub API 오류: {branch_response.status_code}, {branch_response.text}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"GitHub 브랜치 생성 중 오류 발생: {str(e)}")
        return False

def create_github_pull_request(
    branch_name: str, 
    title: str, 
    body: str, 
    base_branch: str = "main"
) -> Optional[str]:
    """
    GitHub에 PR을 생성합니다.
    
    Args:
        branch_name: PR의 소스 브랜치
        title: PR 제목
        body: PR 설명
        base_branch: 대상 브랜치 (기본값: main)
        
    Returns:
        생성된 PR의 URL 또는 None (실패 시)
    """
    # GitHub 설정 가져오기
    settings = get_github_settings()
    github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
    github_repo = settings.get("github_repo") or os.getenv("GITHUB_REPO")
    github_username = settings.get("github_username") or os.getenv("GITHUB_USERNAME")
    
    if not all([github_token, github_repo, github_username]):
        raise ValueError("GitHub 설정이 완료되지 않았습니다.")
    
    # API 헤더
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # PR 데이터
    pr_data = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": base_branch
    }
    
    try:
        # PR 생성
        pr_url = f"https://api.github.com/repos/{github_username}/{github_repo}/pulls"
        pr_response = requests.post(pr_url, headers=headers, data=json.dumps(pr_data))
        
        if pr_response.status_code != 201:
            logger.error(f"GitHub API 오류: {pr_response.status_code}, {pr_response.text}")
            return None
        
        # 생성된 PR의 URL 반환
        return pr_response.json().get("html_url")
    except Exception as e:
        logger.error(f"GitHub PR 생성 중 오류 발생: {str(e)}")
        return None