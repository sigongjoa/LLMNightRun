"""
LLMNightRun 설정 모듈

프로젝트 전체에서 사용되는 설정값 및 환경 변수를 관리합니다.
다양한 환경(개발, 테스트, 프로덕션)에 맞게 설정을 유연하게 구성할 수 있습니다.
"""

import os
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union, List, Any, Set
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class EnvironmentType(str, Enum):
    """애플리케이션 실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LoggingSettings(BaseSettings):
    """로깅 관련 설정"""
    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_enabled: bool = Field(True, env="LOG_FILE_ENABLED")
    file_path: Optional[str] = Field(None, env="LOG_FILE_PATH")
    json_enabled: bool = Field(True, env="LOG_JSON_ENABLED")
    console_enabled: bool = Field(True, env="LOG_CONSOLE_ENABLED")
    
    model_config = SettingsConfigDict(env_prefix="LOG_")


class LLMSettings(BaseSettings):
    """LLM 관련 설정"""
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    claude_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    local_llm_base_url: Optional[str] = Field("http://127.0.0.1:1234", env="LOCAL_LLM_URL")
    local_llm_model_id: Optional[str] = Field("deepseek-r1-distill-qwen-7b", env="LOCAL_LLM_MODEL_ID")
    local_llm_temperature: float = 0.7
    local_llm_max_tokens: int = 1500
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1500
    timeout: int = 120
    cache_enabled: bool = Field(True, env="LLM_CACHE_ENABLED")
    cache_ttl: int = Field(3600, env="LLM_CACHE_TTL")  # 1시간
    
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        """온도 값이 0~1 사이인지 확인"""
        if v < 0 or v > 1:
            raise ValueError("온도는 0~1 사이의 값이어야 합니다")
        return v


class SandboxSettings(BaseSettings):
    """Docker 샌드박스 설정"""
    enabled: bool = Field(True, env="SANDBOX_ENABLED")
    image: str = "python:3.10-slim"
    work_dir: str = "/workspace"
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    network_enabled: bool = False
    timeout: int = 30
    allowed_packages: List[str] = []
    
    model_config = SettingsConfigDict(env_prefix="SANDBOX_")
    
    @field_validator('allowed_packages')
    @classmethod
    def parse_allowed_packages(cls, v):
        """문자열인 경우 목록으로 파싱"""
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                v = [pkg.strip() for pkg in v.split(',') if pkg.strip()]
        return v


class GitHubSettings(BaseSettings):
    """GitHub 관련 설정"""
    token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    username: Optional[str] = Field(None, env="GITHUB_USERNAME")
    repo: Optional[str] = Field(None, env="GITHUB_REPO")
    api_url: str = "https://api.github.com"
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1시간
    
    model_config = SettingsConfigDict(env_prefix="GITHUB_")


class BrowserSettings(BaseSettings):
    """브라우저 자동화 설정"""
    headless: bool = Field(True, env="HEADLESS")
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    timeout: int = 30
    screenshot_width: int = 1280
    screenshot_height: int = 800
    
    model_config = SettingsConfigDict(env_prefix="BROWSER_")


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""
    url: str = Field("sqlite:///./llmnightrun.db", env="DATABASE_URL")
    connect_args: Dict = Field(default_factory=dict)
    min_pool_size: int = Field(5, env="DB_MIN_POOL_SIZE")
    max_pool_size: int = Field(20, env="DB_MAX_POOL_SIZE")
    pool_recycle: int = Field(3600, env="DB_POOL_RECYCLE")
    echo: bool = Field(False, env="DB_ECHO")
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class CorsSettings(BaseSettings):
    """CORS 설정"""
    allow_origins: List[str] = Field(["*"], env="CORS_ALLOW_ORIGINS")
    allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    allow_methods: List[str] = Field(["*"], env="CORS_ALLOW_METHODS")
    allow_headers: List[str] = Field(["*"], env="CORS_ALLOW_HEADERS")
    
    model_config = SettingsConfigDict(env_prefix="CORS_")
    
    @field_validator('allow_origins', 'allow_methods', 'allow_headers')
    @classmethod
    def parse_list(cls, v):
        """문자열인 경우 목록으로 파싱"""
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                v = [item.strip() for item in v.split(',') if item.strip()]
        return v


class SecuritySettings(BaseSettings):
    """보안 관련 설정"""
    api_key_enabled: bool = Field(False, env="SECURITY_API_KEY_ENABLED")
    api_key: Optional[str] = Field(None, env="SECURITY_API_KEY")
    secret_key: str = Field("09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7", env="SECURITY_SECRET_KEY")
    jwt_secret: Optional[str] = Field(None, env="SECURITY_JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="SECURITY_JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(60 * 24, env="SECURITY_JWT_EXPIRE_MINUTES")  # 24시간
    password_reset_token_expire_hours: int = Field(24, env="SECURITY_PASSWORD_RESET_TOKEN_EXPIRE_HOURS")
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class CacheSettings(BaseSettings):
    """캐싱 관련 설정"""
    enabled: bool = Field(True, env="CACHE_ENABLED")
    backend: str = Field("memory", env="CACHE_BACKEND")
    ttl: int = Field(3600, env="CACHE_TTL")  # 1시간
    
    model_config = SettingsConfigDict(env_prefix="CACHE_")


class MCPSettings(BaseSettings):
    """MCP 관련 설정"""
    enabled: bool = Field(True, env="MCP_ENABLED")
    websocket_ping_interval: int = Field(30, env="MCP_WS_PING_INTERVAL")
    
    model_config = SettingsConfigDict(env_prefix="MCP_")


class Settings(BaseSettings):
    """전역 설정 클래스"""
    # 기본 경로 설정
    base_dir: Path = Path(__file__).parent.parent.parent
    workspace_root: Path = Field(default=Path(__file__).parent.parent / "workspace")
    
    # 환경 설정
    env: EnvironmentType = Field(EnvironmentType.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    port: int = Field(8000, env="PORT")
    host: str = Field("0.0.0.0", env="HOST")
    root_path: str = Field("", env="ROOT_PATH")
    
    # 애플리케이션 정보
    app_name: str = Field("LLMNightRun", env="APP_NAME")
    app_version: str = Field("0.1.0", env="APP_VERSION")
    app_description: str = Field("멀티 LLM 통합 자동화 플랫폼", env="APP_DESCRIPTION")
    
    # 컴포넌트별 설정
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        validate_default=True
    )
    
    @model_validator(mode="after")
    def setup_directories_and_paths(self):
        """디렉토리 및 경로 설정 검증"""
        # 작업 공간 디렉토리 생성
        os.makedirs(self.workspace_root, exist_ok=True)
        
        # 로그 디렉토리 설정
        if self.logging.file_enabled and not self.logging.file_path:
            log_dir = self.base_dir / "logs"
            os.makedirs(log_dir, exist_ok=True)
            self.logging.file_path = str(log_dir / "llmnightrun.log")
        
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
        
        return self
    
    def get_log_level(self) -> int:
        """로그 레벨을 파이썬 로깅 레벨로 변환"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.logging.level.upper(), logging.INFO)
    
    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.env == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """테스트 환경인지 확인"""
        return self.env == EnvironmentType.TESTING
    
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.env == EnvironmentType.PRODUCTION


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스를 가져오는 함수 (캐싱 지원)"""
    return Settings()


# 쉬운 접근을 위한 전역 변수
settings = get_settings()
