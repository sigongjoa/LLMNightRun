"""
CORS 문제 해결을 위한 스크립트
이 스크립트를 백엔드 폴더에서 실행하여 CORS 헤더를 추가하세요.
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os
import sys
from typing import Dict, Any

# 백엔드 폴더를 시스템 경로에 추가
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(backend_dir))

# 기존 앱 가져오기
from backend.main import app

# 기존 CORS 미들웨어 제거 (이미 추가되어 있어서 중복 방지)
try:
    app.user_middleware = [m for m in app.user_middleware if not isinstance(m.cls, CORSMiddleware)]
    print("기존 CORS 미들웨어 제거 완료")
except Exception as e:
    print(f"기존 CORS 미들웨어 제거 오류: {str(e)}")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("새로운 CORS 미들웨어 추가 완료")

# 모든 응답에 CORS 헤더를 추가하는 커스텀 미들웨어
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # 실제 요청 처리
        response = await call_next(request)
        
        # 모든 응답에 CORS 헤더 추가
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return response

# 커스텀 CORS 미들웨어 추가
app.add_middleware(CORSHeaderMiddleware)
print("커스텀 CORS 헤더 미들웨어 추가 완료")

# 애플리케이션 실행
if __name__ == "__main__":
    print("CORS 설정이 추가된 백엔드 서버 시작...")
    uvicorn.run(
        "cors_fix:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
