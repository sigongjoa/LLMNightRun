"""
기본 컨트롤러 모듈

모든 컨트롤러의 기본 클래스를 제공합니다.
"""

from typing import TypeVar, Generic, Any, Dict, List, Optional, Union

from ..core.service_locator import get_service
from ..logger import get_logger

# 로거 설정
logger = get_logger(__name__)

T = TypeVar('T')


class BaseController:
    """
    모든 컨트롤러의 기본 클래스
    
    API 라우터와 서비스 레이어 사이의 중간 계층으로 동작합니다.
    요청 데이터 유효성 검사, 권한 검사, 비즈니스 로직 호출, 응답 포맷팅 등을 담당합니다.
    """
    
    def __init__(self):
        """
        컨트롤러 초기화
        """
        self.logger = logger
    
    def _get_service(self, service_type: type) -> Any:
        """
        서비스 인스턴스를 가져옵니다.
        
        Args:
            service_type: 가져올 서비스 타입
            
        Returns:
            서비스 인스턴스
        """
        return get_service(service_type)
    
    def _format_response(self, data: Any, message: Optional[str] = None) -> Dict[str, Any]:
        """
        응답 데이터를 표준 형식으로 포맷팅합니다.
        
        Args:
            data: 응답 데이터
            message: 응답 메시지 (선택 사항)
            
        Returns:
            포맷팅된 응답 데이터
        """
        response = {
            "success": True,
            "data": data
        }
        
        if message:
            response["message"] = message
            
        return response
    
    def _format_error(self, error_message: str, details: Any = None) -> Dict[str, Any]:
        """
        오류 응답을 표준 형식으로 포맷팅합니다.
        
        Args:
            error_message: 오류 메시지
            details: 상세 오류 정보 (선택 사항)
            
        Returns:
            포맷팅된 오류 응답 데이터
        """
        response = {
            "success": False,
            "error": error_message
        }
        
        if details:
            response["details"] = details
            
        return response
