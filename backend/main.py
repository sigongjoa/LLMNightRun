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
from routes.ab_testing.routes import router as ab_testing_router

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
app.include_router(ab_testing_router)

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
# CAUTION: 다른 기능과 연결된 코드입니다. 수정 시 연관 기능(예: 프론트엔드 메모리 컴포넌트)에 영향이 있을 수 있습니다.
# TEMP: 메모리 관리 기능 구현 코드입니다. 현재는 JSON 파일 기반으로 동작하며, 추후 벡터 DB로 리팩토링 예정입니다.
# ------------------------------------------------------------------------------
# 메모리 모듈: 대화, 실험, 코드 등의 정보를 저장하고 검색하는 기능을 제공합니다.
# - 현재 구현: JSON 파일 기반 메모리 저장소
# - 향후 계획: FAISS 등의 벡터 DB를 활용한 고성능 시맨틱 검색 추가
# ------------------------------------------------------------------------------

import time
import uuid
from enum import Enum
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# 메모리 타입 정의 - 각 메모리의 종류를 구분하는 열거형
class MemoryType(str, Enum):
    CONVERSATION = "conversation"  # 대화 기록
    EXPERIMENT = "experiment"      # 실험 결과
    CODE = "code"                  # 코드 스니펫
    RESULT = "result"              # 연산 결과
    NOTE = "note"                  # 기타 메모

# 메모리 관리 클래스: 메모리의 저장, 검색, 삭제 기능을 구현합니다.
class MemoryData:
    def __init__(self):
        """메모리 관리자 초기화 및 기존 데이터 로드"""
        self.memories = []
        self.load_memories()
    
    def load_memories(self):
        """파일에서 메모리 데이터 로드
        
        JSON 파일에서 기존 메모리 데이터를 읽어들입니다.
        파일이 없거나 오류 발생 시 빈 메모리 배열로 초기화합니다.
        """
        try:
            memory_file = Path(__file__).parent / "memory_data.json"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
                print(f"메모리 {len(self.memories)}개 로드됨")
            else:
                print("메모리 파일이 없어 새로 생성합니다.")
                self.memories = []
                self.save_memories()
        except Exception as e:
            print(f"메모리 로드 오류: {str(e)}")
            self.memories = []
    
    def save_memories(self):
        """메모리 데이터를 파일에 저장
        
        현재 메모리 데이터를 JSON 형식으로 파일에 저장합니다.
        """
        try:
            memory_file = Path(__file__).parent / "memory_data.json"
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
            print(f"메모리 {len(self.memories)}개 저장됨")
        except Exception as e:
            print(f"메모리 저장 오류: {str(e)}")
    
    def add_memory(self, memory):
        """메모리 추가 또는 업데이트
        
        Args:
            memory: 메모리 데이터 (딕셔너리)
            
        Returns:
            저장된 메모리 데이터
            
        Notes:
            - ID가 이미 존재하면 해당 메모리를 업데이트합니다.
            - ID가 없으면 새 UUID를 생성합니다.
            - timestamp가 없으면 현재 시간으로 설정합니다.
        """
        # ID가 이미 있는지 확인하여 업데이트 또는 추가
        if "id" in memory and any(m.get("id") == memory["id"] for m in self.memories):
            # 업데이트 로직
            for i, m in enumerate(self.memories):
                if m.get("id") == memory["id"]:
                    self.memories[i] = memory
                    break
        else:
            # 새 메모리 추가
            if "id" not in memory:
                memory["id"] = str(uuid.uuid4())
            if "timestamp" not in memory:
                memory["timestamp"] = int(time.time())
            self.memories.append(memory)
        
        # 저장
        self.save_memories()
        return memory
    
    def delete_memory(self, memory_id):
        """메모리 삭제
        
        Args:
            memory_id: 삭제할 메모리의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        initial_length = len(self.memories)
        self.memories = [m for m in self.memories if m.get("id") != memory_id]
        if len(self.memories) < initial_length:
            self.save_memories()
            return True
        return False
    
    def search_memories(self, query="", memory_types=None, top_k=50):
        """메모리 검색
        
        Args:
            query: 검색 쿼리 (선택적)
            memory_types: 필터링할 메모리 타입 목록 (선택적)
            top_k: 반환할 최대 결과 수
            
        Returns:
            List: 검색 결과 메모리 목록
            
        Notes:
            - 텍스트 내용과 태그를 기반으로 검색합니다.
            - 최신 항목부터 정렬됩니다.
            - 검색 결과에 관련성 점수를 추가합니다.
        """
        results = self.memories.copy()
        
        # 타입 필터링
        if memory_types and len(memory_types) > 0:
            results = [m for m in results if m.get("type") in memory_types]
        
        # 쿼리 필터링 (간단한 텍스트 포함 검색)
        if query:
            query = query.lower()
            results = [
                m for m in results 
                if query in m.get("content", "").lower() or
                any(query in tag.lower() for tag in m.get("metadata", {}).get("tags", []))
            ]
        
        # 시간순 정렬 (최신순)
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # top_k 적용
        results = results[:min(top_k, len(results))]
        
        # 검색 점수 추가 (간단한 구현)
        for r in results:
            # 실제 구현에서는 벡터 유사도 점수 사용
            r["score"] = 0.95 - (results.index(r) * 0.05)
        
        return results

# 메모리 관리자 인스턴스 생성 - 애플리케이션 전체에서 사용
memory_manager = MemoryData()
# END-TEMP

# CAUTION: 다른 기능과 연결된 코드입니다. 메모리 검색 API 엔드포인트는 프론트엔드 메모리 컴포넌트와 직접 연결됩니다.
@app.get("/memory/search")
async def memory_search():
    """메모리 검색 엔드포인트 (GET 메서드)
    
    모든 메모리를 최신순으로 반환합니다(최대 50개).
    필터링 없이 전체 목록을 조회할 때 사용합니다.
    """
    print("메모리 검색 엔드포인트(GET) 호출됨")
    # 전체 메모리 반환 (최신순, 최대 50개)
    results = memory_manager.search_memories(top_k=50)
    return results

@app.post("/memory/search")
async def memory_search_post(request: Request):
    """메모리 검색 엔드포인트 (POST 메서드)
    
    고급 검색 옵션을 제공합니다:
    - 텍스트 검색 쿼리
    - 메모리 타입 필터링
    - 결과 개수 제한
    
    Request Body:
        query (str): 검색 쿼리 텍스트
        top_k (int): 최대 결과 개수
        memory_types (list): 필터링할 메모리 타입 목록
    """
    print("메모리 검색 엔드포인트(POST) 호출됨")
    try:
        data = await request.json()
        query = data.get("query", "")
        top_k = data.get("top_k", 50)
        memory_types = data.get("memory_types", [])
        
        print(f"검색 쿼리: {query}, top_k: {top_k}, memory_types: {memory_types}")
        
        # 메모리 검색 실행
        results = memory_manager.search_memories(
            query=query,
            memory_types=memory_types,
            top_k=top_k
        )
        
        return results
    except Exception as e:
        print(f"메모리 검색 오류: {str(e)}")
        return []
# END-CAUTION
# END-TEMP
# END-CAUTION

# CAUTION: 다른 기능과 연결된 코드입니다. 프론트엔드 메모리 대시보드와 연결됩니다.
@app.get("/memory/count")
async def memory_count():
    """메모리 카운트 엔드포인트
    
    전체 메모리 개수를 반환합니다.
    메모리 대시보드의 통계 표시에 사용됩니다.
    
    Returns:
        dict: 상태 및 메모리 개수 정보
    """
    print("메모리 카운트 엔드포인트 호출됨")
    return {"status": "ok", "count": len(memory_manager.memories)}

@app.get("/memory/health")
async def memory_health():
    """메모리 상태 확인 엔드포인트
    
    메모리 시스템의 상태를 확인합니다.
    프론트엔드에서 메모리 시스템 연결 상태를 확인하는 데 사용됩니다.
    
    Returns:
        dict: 상태 정보
    """
    print("메모리 상태 확인 엔드포인트 호출됨")
    return {"status": "ok", "healthy": True}
# END-CAUTION

# CAUTION: 다른 기능과 연결된 코드입니다. 변경 시 프론트엔드 메모리 컴포넌트와 연동에 주의하세요.
@app.delete("/memory/delete/{memory_id}")
async def delete_memory(memory_id: str):
    """메모리 삭제 엔드포인트
    
    지정된 ID의 메모리를 시스템에서 삭제합니다.
    
    Path Parameters:
        memory_id (str): 삭제할 메모리의 ID
    
    Returns:
        dict: 삭제 성공/실패 상태 및 메시지
    """
    print(f"메모리 삭제 엔드포인트 호출됨: memory_id={memory_id}")
    try:
        # 메모리 삭제 실행
        success = memory_manager.delete_memory(memory_id)
        
        if success:
            return {"status": "success", "message": f"메모리 ID {memory_id}가 성공적으로 삭제되었습니다."}
        else:
            return {"status": "error", "message": f"메모리 ID {memory_id}가 존재하지 않습니다."}
    except Exception as e:
        print(f"메모리 삭제 오류: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/memory/add")
async def add_memory(request: Request):
    """메모리 추가/수정 엔드포인트
    
    새 메모리를 추가하거나 기존 메모리를 수정합니다.
    ID가 제공되면 해당 메모리를 업데이트하고, 없으면 새로 생성합니다.
    
    Request Body:
        content (str): 메모리 내용 (필수)
        type (str): 메모리 타입 (기본값: "note")
        metadata (dict): 메타데이터 (태그, 추가 정보 등)
        id (str, 선택적): 업데이트할 메모리 ID
    
    Returns:
        dict: 성공/실패 상태, 메시지, 저장된 메모리 정보
    """
    print(f"메모리 추가 엔드포인트 호출됨")
    try:
        # 요청 데이터 파싱
        data = await request.json()
        content = data.get("content", "")
        memory_type = data.get("type", "note")
        metadata = data.get("metadata", {})
        memory_id = data.get("id")  # 기존 메모리면 ID 있음
        
        print(f"메모리 추가 요청: content={content[:30]}..., type={memory_type}, metadata={metadata}")
        
        # 유효성 검사
        if not content:
            return {"status": "error", "message": "메모리 내용(content)은 필수 항목입니다."}
        
        # 메모리 객체 생성
        memory = {
            "content": content,
            "type": memory_type,
            "metadata": metadata,
            "timestamp": int(time.time())
        }
        
        # ID가 있으면 설정 (업데이트)
        if memory_id:
            memory["id"] = memory_id
        
        # 메모리 저장
        result = memory_manager.add_memory(memory)
        
        # 성공 응답
        return {
            "status": "success", 
            "message": "메모리가 성공적으로 추가되었습니다.",
            "memory": result
        }
    except Exception as e:
        print(f"메모리 추가 오류: {str(e)}")
        return {"status": "error", "message": str(e)}
# END-CAUTION

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
