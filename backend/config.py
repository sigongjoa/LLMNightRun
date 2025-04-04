"""
LLMNightRun 설정 모듈

프로젝트 전체에서 사용되는 설정값 및 환경 변수를 관리합니다.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    """LLM 관련 설정"""
    openai_api_key: Optional[str] = Field(default=None)
    claude_api_key: Optional[str] = Field(default=None)
    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1500)
    timeout: int = Field(default=120)


class SandboxSettings(BaseModel):
    """Docker 샌드박스 설정"""
    image: str = Field(default="python:3.10-slim")
    work_dir: str = Field(default="/workspace")
    memory_limit: str = Field(default="512m")
    cpu_limit: float = Field(default=1.0)
    network_enabled: bool = Field(default=False)
    timeout: int = Field(default=30)


class GithubSettings(BaseModel):
    """GitHub 관련 설정"""
    token: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    repo: Optional[str] = Field(default=None)


class BrowserSettings(BaseModel):
    """브라우저 자동화 설정"""
    headless: bool = Field(default=True)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
    timeout: int = Field(default=30)
    screenshot_width: int = Field(default=1280)
    screenshot_height: int = Field(default=800)


class Config(BaseModel):
    """전역 설정 클래스"""
    # 기본 경로 설정
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    workspace_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "workspace"
    )
    
    # 컴포넌트별 설정
    llm: LLMSettings = Field(default_factory=LLMSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    github: GithubSettings = Field(default_factory=GithubSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    
    # 환경 설정
    debug: bool = Field(default=False)
    port: int = Field(default=8000)
    host: str = Field(default="0.0.0.0")
    
    def __init__(self, **data):
        """환경 변수에서 설정 로드"""
        # 환경 변수에서 설정 로드
        openai_api_key = os.getenv("OPENAI_API_KEY")
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        github_username = os.getenv("GITHUB_USERNAME")
        github_repo = os.getenv("GITHUB_REPO")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        # 초기 데이터 설정
        initial_data = {
            "debug": debug,
            "port": port,
            "host": host,
            "llm": {
                "openai_api_key": openai_api_key,
                "claude_api_key": claude_api_key,
            },
            "github": {
                "token": github_token,
                "username": github_username,
                "repo": github_repo,
            },
        }
        
        # 사용자 제공 데이터와 병합
        merged_data = {**initial_data, **data}
        
        # 디렉토리 생성
        workspace_path = Path(merged_data.get("workspace_root", self.workspace_root))
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        super().__init__(**merged_data)


class LLMSettings(BaseModel):
    """LLM 관련 설정"""
    openai_api_key: Optional[str] = Field(default=None)
    claude_api_key: Optional[str] = Field(default=None)
    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1500)
    timeout: int = Field(default=120)


class SandboxSettings(BaseModel):
    """Docker 샌드박스 설정"""
    image: str = Field(default="python:3.10-slim")
    work_dir: str = Field(default="/workspace")
    memory_limit: str = Field(default="512m")
    cpu_limit: float = Field(default=1.0)
    network_enabled: bool = Field(default=False)
    timeout: int = Field(default=30)


class GithubSettings(BaseModel):
    """GitHub 관련 설정"""
    token: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    repo: Optional[str] = Field(default=None)


class BrowserSettings(BaseModel):
    """브라우저 자동화 설정"""
    headless: bool = Field(default=True)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
    timeout: int = Field(default=30)
    screenshot_width: int = Field(default=1280)
    screenshot_height: int = Field(default=800)


class Config(BaseModel):
    """전역 설정 클래스"""
    # 기본 경로 설정
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    workspace_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "workspace"
    )
    
    # 컴포넌트별 설정
    llm: LLMSettings = Field(default_factory=LLMSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    github: GithubSettings = Field(default_factory=GithubSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    
    # 환경 설정
    debug: bool = Field(default=False)
    port: int = Field(default=8000)
    host: str = Field(default="0.0.0.0")
    
    def __init__(self, **data):
        """환경 변수에서 설정 로드"""
        # 환경 변수에서 설정 로드
        openai_api_key = os.getenv("OPENAI_API_KEY")
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        github_username = os.getenv("GITHUB_USERNAME")
        github_repo = os.getenv("GITHUB_REPO")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        # 초기 데이터 설정
        initial_data = {
            "debug": debug,
            "port": port,
            "host": host,
            "llm": {
                "openai_api_key": openai_api_key,
                "claude_api_key": claude_api_key,
            },
            "github": {
                "token": github_token,
                "username": github_username,
                "repo": github_repo,
            },
        }
        
        # 사용자 제공 데이터와 병합
        merged_data = {**initial_data, **data}
        
        # 디렉토리 생성
        workspace_path = Path(merged_data.get("workspace_root", self.workspace_root))
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        super().__init__(**merged_data)


# 전역 설정 인스턴스
config = Config()