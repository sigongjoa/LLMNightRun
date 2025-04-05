"""
LLMNightRun 예외 모듈

애플리케이션 전체에서 사용되는 사용자 정의 예외를 정의합니다.
"""


class LLMNightRunError(Exception):
    """LLMNightRun 기본 예외"""
    def __init__(self, message="LLMNightRun 오류가 발생했습니다"):
        self.message = message
        super().__init__(self.message)


class ConfigError(LLMNightRunError):
    """설정 관련 오류"""
    def __init__(self, message="설정 오류가 발생했습니다"):
        super().__init__(message)


class DatabaseError(LLMNightRunError):
    """데이터베이스 관련 오류"""
    def __init__(self, message="데이터베이스 오류가 발생했습니다"):
        super().__init__(message)


class LLMError(LLMNightRunError):
    """LLM 관련 오류"""
    def __init__(self, message="LLM 오류가 발생했습니다"):
        super().__init__(message)


class TokenLimitExceeded(LLMError):
    """토큰 제한 초과 오류"""
    def __init__(self, message="토큰 제한을 초과했습니다"):
        super().__init__(message)


class AgentError(LLMNightRunError):
    """에이전트 관련 오류"""
    def __init__(self, message="에이전트 오류가 발생했습니다"):
        super().__init__(message)


class ToolError(LLMNightRunError):
    """도구 관련 오류"""
    def __init__(self, message="도구 오류가 발생했습니다"):
        super().__init__(message)


class SandboxError(LLMNightRunError):
    """샌드박스 관련 오류"""
    def __init__(self, message="샌드박스 오류가 발생했습니다"):
        super().__init__(message)


class SandboxTimeoutError(SandboxError):
    """샌드박스 실행 타임아웃 오류"""
    def __init__(self, message="샌드박스 실행 시간이 초과되었습니다"):
        super().__init__(message)


class GitHubError(LLMNightRunError):
    """GitHub 관련 오류"""
    def __init__(self, message="GitHub 오류가 발생했습니다"):
        super().__init__(message)


class CodeError(LLMNightRunError):
    """코드 관련 오류"""
    def __init__(self, message="코드 처리 중 오류가 발생했습니다"):
        super().__init__(message)


class APIError(LLMNightRunError):
    """API 관련 오류"""
    def __init__(self, message="API 오류가 발생했습니다", status_code=500):
        self.status_code = status_code
        super().__init__(message)


class ValidationError(LLMNightRunError):
    """데이터 검증 오류"""
    def __init__(self, message="데이터 검증 오류가 발생했습니다"):
        super().__init__(message)


class NotFoundError(LLMNightRunError):
    """리소스 찾을 수 없음 오류"""
    def __init__(self, message="요청한 리소스를 찾을 수 없습니다"):
        super().__init__(message)