"""
열거형 타입 정의 모듈

애플리케이션 전체에서 사용되는 열거형 타입을 정의합니다.
"""

from enum import Enum


class LLMType(str, Enum):
    """LLM 유형 정의"""
    OPENAI_API = "openai_api"
    OPENAI_WEB = "openai_web"
    CLAUDE_API = "claude_api"
    CLAUDE_WEB = "claude_web"
    MANUAL = "manual"  # 수동으로 입력한 경우


class CodeLanguage(str, Enum):
    """코드 언어 유형"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    OTHER = "other"


class IndexingStatus(str, Enum):
    """인덱싱 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexingFrequency(str, Enum):
    """인덱싱 주기"""
    MANUAL = "manual"
    ON_COMMIT = "on_commit"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class AgentPhase(str, Enum):
    """에이전트 단계"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    INITIALIZE = "initialize"
    FINISH = "finish"
    ERROR = "error"


class AgentState(str, Enum):
    """에이전트 상태"""
    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"


class ToolChoice(str, Enum):
    """도구 선택 모드"""
    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"