"""
LLMNightRun 예외 모듈

애플리케이션 전체에서 사용되는 사용자 정의 예외를 정의합니다.
"""


class LLMNightRunError(Exception):
    """LLMNightRun 기본 예외"""
    pass


class ConfigError(LLMNightRunError):
    """설정 관련 오류"""
    pass


class LLMError(LLMNightRunError):
    """LLM 관련 오류"""
    pass


class TokenLimitExceeded(LLMError):
    """토큰 제한 초과 오류"""
    pass


class AgentError(LLMNightRunError):
    """에이전트 관련 오류"""
    pass


class ToolError(LLMNightRunError):
    """도구 관련 오류"""
    pass


class SandboxError(LLMNightRunError):
    """샌드박스 관련 오류"""
    pass


class SandboxTimeoutError(SandboxError):
    """샌드박스 실행 타임아웃 오류"""
    pass


class GitHubError(LLMNightRunError):
    """GitHub 관련 오류"""
    pass