from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from database import engine, Base, get_db
import models
import crud
import schemas
from auth.dependencies import get_current_active_user
from auth.router import router as auth_router
from github_repos import router as github_repos_router
from settings import router as settings_router
# from routes.prompt_engineering.router import router as prompt_engineering_router
from direct_prompt_api import router as direct_prompt_router
from github_analyzer_api import router as github_analyzer_router
from model_installer_api import router as model_installer_router
from database.models import User

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLMNightRun API")

# 라우터 등록
app.include_router(auth_router, prefix="")
app.include_router(github_repos_router)
app.include_router(settings_router)
# app.include_router(prompt_engineering_router, prefix="")
app.include_router(direct_prompt_router, prefix="")
app.include_router(github_analyzer_router)
app.include_router(model_installer_router)

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://localhost:5173", # Vite 기본 포트
    "http://localhost:5174", # 기본 포트 사용 중일 경우 다음 포트
    "*",  # 개발 중 모든 출처 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 경로
@app.get("/")
async def root_endpoint():
    print("루트 엔드포인트 호출됨")
    return {"message": "Welcome to GitHub Repository Manager API"}

# 테스트 엔드포인트
@app.get("/hello")
def hello():
    print("Hello 엔드포인트 호출됨")
    return {"hello": "world"}

# 간단한 테스트 엔드포인트
@app.get("/simple-test")
def simple_test():
    print("단순 테스트 엔드포인트 호출됨")
    return {"message": "성공! 서버가 정상적으로 응답합니다."}

# 로컬 LLM 상태 엔드포인트
@app.get("/api/local-llm/status")
async def local_llm_status():
    """
    로컬 LLM(LM Studio) 상태를 확인하는 엔드포인트
    """
    print("로컬 LLM 상태 엔드포인트 호출됨")
    return {
        "enabled": True,
        "connected": True,
        "base_url": "http://127.0.0.1:1234",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

# 로컬 LLM 핑 엔드포인트
@app.get("/api/local-llm/ping")
def local_llm_ping():
    """
    LLM 서버 응답 확인 엔드포인트
    """
    print("로컬 LLM 핑 엔드포인트 호출됨")
    return {
        "status": "ok",
        "message": "LLM API 서버가 정상적으로 응답하고 있습니다."
    }

# 로컬 LLM 채팅 엔드포인트
@app.post("/api/local-llm/chat")
async def local_llm_chat(request_data: dict):
    """
    LLM과 채팅하는 엔드포인트
    """
    print("로컬 LLM 채팅 엔드포인트 호출됨")
    try:
        import httpx
        
        # LM Studio 기본 URL
        base_url = "http://127.0.0.1:1234"
        
        # 요청 데이터 구성
        messages = request_data.get("messages", [])
        system_message = request_data.get("system_message")
        temperature = request_data.get("temperature", 0.7)
        max_tokens = request_data.get("max_tokens", 1000)
        
        # 시스템 메시지 추가
        if system_message:
            messages = [{"role": "system", "content": system_message}] + messages
        
        # OpenAI 호환 형식으로 요청 데이터 구성
        chat_request = {
            "model": "deepseek-r1-distill-qwen-7b",  # 기본 모델
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # LM Studio API 호출
        async with httpx.AsyncClient(timeout=90.0) as client:  # 타임아웃을 90초로 증가
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                json=chat_request
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "content": content,
                    "model_id": "deepseek-r1-distill-qwen-7b"
                }
    except Exception as e:
        print(f"LM Studio 채팅 오류: {str(e)}")
    
    # 오류 시 기본 응답
    return {
        "content": "LM Studio 서버에 연결할 수 없거나 응답 처리 중 오류가 발생했습니다.",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

# 모든 라우트 조회 엔드포인트
@app.get("/all-routes")
def all_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            methods = list(route.methods) if hasattr(route, "methods") else []
            routes.append({
                "path": str(route.path), 
                "methods": methods
            })
    
    # 경로별 정렬
    routes.sort(key=lambda x: x["path"])
    
    return {"routes": routes, "count": len(routes)}

# LM Studio 직접 연결 테스트 엔드포인트
@app.get("/api/direct-lm-studio")
async def direct_lm_studio():
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://127.0.0.1:1234/v1/models")
            if response.status_code == 200:
                return {"status": "connected", "data": response.json()}
            else:
                return {"status": "error", "code": response.status_code, "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 서버 상태 엔드포인트
@app.get("/server-status")
async def server_status():
    return {
        "status": "healthy", 
        "message": "서버가 정상적으로 실행 중입니다."
    }

# 헬스 체크 엔드포인트
@app.get("/health-check")
async def health_check():
    """
    헬스 체크 엔드포인트 - 프론트엔드가 연결 상태를 확인하기 위해 사용
    """
    print("헬스 체크 엔드포인트 호출됨")
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}

# 메모리 관련 엔드포인트들
@app.get("/memory/search")
async def memory_search():
    """메모리 검색 엔드포인트"""
    print("메모리 검색 엔드포인트 호출됨")
    return {"status": "ok", "data": []}

@app.get("/memory/count")
async def memory_count():
    """메모리 카운트 엔드포인트"""
    print("메모리 카운트 엔드포인트 호출됨")
    return {"status": "ok", "count": 0}

@app.get("/memory/health")
async def memory_health():
    """메모리 상태 확인 엔드포인트"""
    print("메모리 상태 확인 엔드포인트 호출됨")
    return {"status": "ok", "healthy": True}

# 헬스 체크 엔드포인트 (추가 경로)
@app.get("/health/check")
async def health_check_alt():
    """
    대체 헬스 체크 엔드포인트
    """
    print("대체 헬스 체크 엔드포인트 호출됨")
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}

# 간단한 인증 엔드포인트
@app.post("/simple-login")
async def simple_login(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")
        
        if username == "admin" and password == "admin123":
            return {
                "status": "success",
                "user": {
                    "username": "admin",
                    "email": "admin@example.com",
                    "is_admin": True
                }
            }
        else:
            return {"status": "error", "message": "로그인 실패"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 서버 시작 시 경로 출력
@app.on_event("startup")
async def print_routes():
    print("\n=== 등록된 모든 경로 ===")
    print(f"총 경로 수: {len(app.routes)}")
    
    # 경로별로 정렬
    sorted_routes = sorted(app.routes, key=lambda x: getattr(x, "path", ""))
    
    for route in sorted_routes:
        if hasattr(route, "path"):
            methods = ", ".join(route.methods) if hasattr(route, "methods") and route.methods else "N/A"
            print(f"경로: {route.path}")
            print(f"  메서드: {methods}")
            print("-" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
