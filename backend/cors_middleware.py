"""
CORS 미들웨어 모듈

이 모듈은 HTTP 요청에 대한 CORS 헤더를 추가하는 커스텀 미들웨어를 제공합니다.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class CORSMiddleware(BaseHTTPMiddleware):
    """
    모든 응답에 CORS 헤더를 추가하는 커스텀 미들웨어
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials: bool = True,
        allow_methods: list = ["*"],
        allow_headers: list = ["*"],
    ) -> None:
        super().__init__(app)
        self.allow_origins = allow_origins
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        
        logger.info(f"커스텀 CORS 미들웨어 초기화: origins={allow_origins}")
    
    async def dispatch(self, request: Request, call_next):
        # 요청 처리 (OPTIONS 요청 처리 포함)
        if request.method == "OPTIONS":
            # Preflight 요청 처리
            headers = {
                "Access-Control-Allow-Origin": request.headers.get("Origin", self.allow_origins[0] if self.allow_origins else "*"),
                "Access-Control-Allow-Methods": ", ".join(self.allow_methods) if isinstance(self.allow_methods, list) else self.allow_methods,
                "Access-Control-Allow-Headers": ", ".join(self.allow_headers) if isinstance(self.allow_headers, list) else self.allow_headers,
                "Access-Control-Max-Age": "600",  # 캐시 시간(초)
            }
            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"
                
            response = Response(status_code=200, headers=headers)
            return response
        
        # 일반 요청 처리
        response = await call_next(request)
        
        # 응답 헤더에 CORS 헤더 추가
        origin = request.headers.get("Origin", "")
        
        # origin이 허용된 목록에 있는지 확인
        allow_origin = "*"  # 기본값
        if origin:
            if "*" in self.allow_origins:
                allow_origin = origin
            elif origin in self.allow_origins:
                allow_origin = origin
        
        # 헤더 설정
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
        # OPTIONS 이외의 요청에도 메서드/헤더 설정
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods) if isinstance(self.allow_methods, list) else self.allow_methods
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers) if isinstance(self.allow_headers, list) else self.allow_headers
        
        return response
