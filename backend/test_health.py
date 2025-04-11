from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# 테스트용 FastAPI 애플리케이션 생성
app = FastAPI(title="LLMNightRun Health Check Test")

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://localhost:5173",  # Vite 기본 포트
    "http://localhost:5174",  # 기본 포트 사용 중일 경우 다음 포트
    "*",  # 개발 중 모든 출처 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 생성
router = APIRouter()

# 헬스 체크 엔드포인트
@app.get("/health-check")
async def health_check():
    """
    헬스 체크 엔드포인트 - 프론트엔드가 연결 상태를 확인하기 위해 사용
    """
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}

# 테스트 엔드포인트
@app.get("/test")
async def test_endpoint():
    """
    테스트 엔드포인트 - 기본 테스트용
    """
    return {"message": "테스트 성공", "status": "ok"}

# 애플리케이션 시작 시 로그
@app.on_event("startup")
async def startup_event():
    print("=" * 40)
    print("테스트 서버가 시작되었습니다.")
    print("엔드포인트:")
    print("  - /health-check: 서버 상태 확인")
    print("  - /test: 테스트 엔드포인트")
    print("=" * 40)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
