"""
LLMNightRun 설정 모듈

프로젝트 전체에서 사용되는 설정값 및 환경 변수를 관리합니다.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class LLMSettings(BaseSettings):
    """LLM 관련 설정"""
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    claude_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    local_llm_url: Optional[str] = Field("http://127.0.0.1:11434", env="LOCAL_LLM_URL")
    local_llm_model_id: Optional[str] = Field("deepseek-r1-distill-qwen-7b", env="LOCAL_LLM_MODEL_ID")
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1500
    timeout: int = 120


class SandboxSettings(BaseSettings):
    """Docker 샌드박스 설정"""
    image: str = "python:3.10-slim"
    work_dir: str = "/workspace"
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    network_enabled: bool = False
    timeout: int = 30


class GitHubSettings(BaseSettings):
    """GitHub 관련 설정"""
    token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    username: Optional[str] = Field(None, env="GITHUB_USERNAME")
    repo: Optional[str] = Field(None, env="GITHUB_REPO")


class BrowserSettings(BaseSettings):
    """브라우저 자동화 설정"""
    headless: bool = Field(True, env="HEADLESS")
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    timeout: int = 30
    screenshot_width: int = 1280
    screenshot_height: int = 800


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""
    url: str = Field("sqlite:///./llmnightrun.db", env="DATABASE_URL")
    connect_args: Dict = {}  # SQLite에서 사용될 추가 연결 인자
    
    class Config:
        env_prefix = "DB_"


class Settings(BaseSettings):
    """전역 설정 클래스"""
    # 기본 경로 설정
    base_dir: Path = Path(__file__).parent.parent.parent
    workspace_root: Path = Field(default=Path(__file__).parent.parent / "workspace")
    
    # 환경 설정
    debug: bool = Field(False, env="DEBUG")
    port: int = Field(8000, env="PORT")
    host: str = Field("0.0.0.0", env="HOST")
    
    # 컴포넌트별 설정
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # SQLite 데이터베이스 파일 경로 설정
        if self.database.url.startswith("sqlite:///"):
            # 상대 경로를 절대 경로로 변환
            sqlite_path = self.database.url.replace("sqlite:///", "")
            if not os.path.isabs(sqlite_path):
                absolute_path = os.path.join(self.base_dir, sqlite_path)
                self.database.url = f"sqlite:///{absolute_path}"
            
            # SQLite 특화 연결 설정
            if "check_same_thread" not in self.database.connect_args:
                self.database.connect_args["check_same_thread"] = False
        
        # 작업 공간 디렉토리 생성
        os.makedirs(self.workspace_root, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스를 가져오는 함수 (캐싱 지원)"""
    return Settings()


# 쉬운 접근을 위한 전역 변수
settings = get_settings()