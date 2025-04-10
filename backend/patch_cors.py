"""
기존 FastAPI 애플리케이션에 CORS 해결 패치를 적용하는 스크립트
"""

import os
import sys
import importlib
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware

class CORSPatchMiddleware(BaseHTTPMiddleware):
    """
    모든 HTTP 요청에 CORS 헤더를 추가하는 미들웨어
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # OPTIONS 요청에 대한 특별 처리
        if request.method == "OPTIONS":
            response = Response(
                content="",
                status_code=200,
            )
            origin = request.headers.get("Origin", "*")
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"  # 10분 캐시
            return response
        
        # 일반 요청 처리
        response = await call_next(request)
        
        # 응답 헤더에 CORS 헤더 추가
        origin = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

def patch_app(app: FastAPI):
    """
    FastAPI 앱에 CORS 패치 적용
    """
    # 기존 CORS 미들웨어 제거
    app.user_middleware = [m for m in app.user_middleware if not isinstance(m.cls, CORSMiddleware)]
    print("기존 CORS 미들웨어 제거됨")
    
    # 새 CORS 패치 미들웨어 추가
    app.add_middleware(CORSPatchMiddleware)
    print("CORS 패치 미들웨어 추가됨")
    
    # OPTIONS 요청 전역 핸들러 추가
    @app.options("/{rest_of_path:path}")
    async def options_handler(request: Request):
        """CORS preflight 요청을 명시적으로 처리"""
        return JSONResponse(content={}, status_code=200)
    
    print("OPTIONS 전역 핸들러 추가됨")
    
    # GitHub 저장소 디버그 엔드포인트 추가
    @app.get("/debug/github-repos")
    async def debug_github_repos():
        """디버그용 GitHub 저장소 목록 반환"""
        return [
            {
                "id": 1,
                "name": "debug-repo-1",
                "owner": "debug-user",
                "description": "디버깅용 테스트 저장소 1",
                "is_default": True,
                "is_private": False,
                "url": "https://github.com/debug-user/debug-repo-1",
                "branch": "main"
            },
            {
                "id": 2,
                "name": "debug-repo-2",
                "owner": "debug-organization",
                "description": "디버깅용 테스트 저장소 2",
                "is_default": False,
                "is_private": True,
                "url": "https://github.com/debug-organization/debug-repo-2",
                "branch": "main"
            }
        ]
    
    print("디버그 엔드포인트 추가됨")
    
    return app

# 메인 함수
def main():
    # 백엔드 앱 가져오기
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.main import app
    
    # CORS 패치 적용
    patched_app = patch_app(app)
    
    # 서버 실행
    print("CORS 패치가 적용된 서버 시작 중...")
    uvicorn.run(
        patched_app,
        host="0.0.0.0",
        port=8000,
        reload=False  # 패치드 앱은 재로드하지 않음
    )

if __name__ == "__main__":
    main()
