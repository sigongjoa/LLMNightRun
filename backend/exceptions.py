"""
LLMNightRun 예외 모듈

애플리케이션 전체에서 사용되는 사용자 정의 예외 클래스 계층 구조를 정의합니다.
이 모듈을 통해 API 응답에서 적절한 오류 코드와 메시지를 반환할 수 있습니다.
"""

from typing import Optional, Any, Dict


class LLMNightRunError(Exception):
    """
    LLMNightRun 애플리케이션의 기본 예외 클래스입니다.
    모든 사용자 정의 예외는 이 클래스를 상속받습니다.
    """
    status_code: int = 500
    error_code: str = "general_error"
    
    def __init__(
        self, 
        message: str = "LLMNightRun 오류가 발생했습니다", 
        detail: Optional[Any] = None
    ):
        self.message = message
        self.detail = detail
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 API 응답용 사전 형식으로 변환합니다."""
        error_dict = {
            "error_code": self.error_code,
            "message": self.message
        }
        
        if self.detail:
            error_dict["detail"] = self.detail
            
        return error_dict


# 설정 관련 예외
class ConfigError(LLMNightRunError):
    """설정 관련 오류"""
    status_code = 500
    error_code = "config_error"
    
    def __init__(self, message: str = "설정 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 데이터베이스 관련 예외
class DatabaseError(LLMNightRunError):
    """데이터베이스 관련 오류"""
    status_code = 500
    error_code = "database_error"
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# LLM 관련 예외
class LLMError(LLMNightRunError):
    """LLM 관련 오류"""
    status_code = 503  # Service Unavailable
    error_code = "llm_error"
    
    def __init__(self, message: str = "LLM 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


class TokenLimitExceeded(LLMError):
    """토큰 제한 초과 오류"""
    status_code = 413  # Payload Too Large
    error_code = "token_limit_exceeded"
    
    def __init__(self, message: str = "토큰 제한을 초과했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 에이전트 관련 예외
class AgentError(LLMNightRunError):
    """에이전트 관련 오류"""
    status_code = 500
    error_code = "agent_error"
    
    def __init__(self, message: str = "에이전트 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


class AgentNotFoundError(AgentError):
    """에이전트를 찾을 수 없음 오류"""
    status_code = 404
    error_code = "agent_not_found"
    
    def __init__(self, message: str = "에이전트를 찾을 수 없습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 도구 관련 예외
class ToolError(LLMNightRunError):
    """도구 관련 오류"""
    status_code = 500
    error_code = "tool_error"
    
    def __init__(self, message: str = "도구 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 샌드박스 관련 예외
class SandboxError(LLMNightRunError):
    """샌드박스 관련 오류"""
    status_code = 500
    error_code = "sandbox_error"
    
    def __init__(self, message: str = "샌드박스 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


class SandboxTimeoutError(SandboxError):
    """샌드박스 실행 타임아웃 오류"""
    status_code = 408  # Request Timeout
    error_code = "sandbox_timeout"
    
    def __init__(self, message: str = "샌드박스 실행 시간이 초과되었습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# GitHub 관련 예외
class GitHubError(LLMNightRunError):
    """GitHub 관련 오류"""
    status_code = 502  # Bad Gateway
    error_code = "github_error"
    
    def __init__(self, message: str = "GitHub 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 코드 관련 예외
class CodeError(LLMNightRunError):
    """코드 관련 오류"""
    status_code = 500
    error_code = "code_error"
    
    def __init__(self, message: str = "코드 처리 중 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# API 관련 예외
class APIError(LLMNightRunError):
    """API 관련 오류"""
    status_code = 500
    error_code = "api_error"
    
    def __init__(
        self, 
        message: str = "API 오류가 발생했습니다", 
        detail: Optional[Any] = None,
        status_code: Optional[int] = None
    ):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message, detail)


# 데이터 검증 관련 예외
class ValidationError(LLMNightRunError):
    """데이터 검증 오류"""
    status_code = 400  # Bad Request
    error_code = "validation_error"
    
    def __init__(self, message: str = "데이터 검증 오류가 발생했습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)


# 리소스 찾을 수 없음 예외
class NotFoundError(LLMNightRunError):
    """리소스 찾을 수 없음 오류"""
    status_code = 404  # Not Found
    error_code = "not_found"
    
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다", detail: Optional[Any] = None):
        super().__init__(message, detail)
