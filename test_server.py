from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# 직접 API 가져오기
from backend.direct_prompt_api import router as prompt_router

# FastAPI 앱 생성
app = FastAPI(title="Test Prompt API Server")

# 라우터 등록
app.include_router(prompt_router, prefix="")

# CORS 미들웨어 설정
origins = ["*"]  # 개발 중 모든 출처 허용

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
    return {"message": "Test Prompt API Server"}

# 모든 라우트 조회 엔드포인트
@app.get("/all-routes")
def all_routes():
    return {
        "routes": [
            {
                "path": str(route.path), 
                "methods": list(route.methods) if hasattr(route, "methods") else [],
                "name": route.name if hasattr(route, "name") else None
            }
            for route in app.routes
            if hasattr(route, "path")
        ]
    }

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
    uvicorn.run("test_server:app", host="0.0.0.0", port=8000, reload=True)
