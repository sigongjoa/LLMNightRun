"""
열거형 정의 모듈
"""

from enum import Enum, auto


class ToolChoice(str, Enum):
    """도구 선택 모드 열거형"""
    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


class LLMType(str, Enum):
    openai_api = "openai_api"
    openai_web = "openai_web"
    claude_api = "claude_api"
    claude_web = "claude_web"
    local_llm = "local_llm"
    manual = "manual"


class CodeLanguage(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    csharp = "csharp"
    cpp = "cpp"
    go = "go"
    rust = "rust"
    php = "php"
    ruby = "ruby"
    swift = "swift"
    kotlin = "kotlin"
    other = "other"


class IndexingStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class IndexingFrequency(str, Enum):
    manual = "manual"
    on_commit = "on_commit"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"


class AgentPhase(str, Enum):
    think = "think"
    act = "act"
    observe = "observe"
    initialize = "initialize"
    finish = "finish"
    error = "error"


class AgentState(str, Enum):
    """에이전트 상태 열거형"""
    idle = "idle"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"
    waiting = "waiting"
    interrupted = "interrupted"
    finished = "finished"
    error = "error"
