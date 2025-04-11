from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 새로운 FastAPI 앱 생성
app = FastAPI(title="로컬 LLM 서버")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 경로
@app.get("/")
async def root():
    logger.info("루트 경로 호출됨")
    return {"message": "로컬 LLM 서버가 실행 중입니다"}

# 로컬 LLM 상태 엔드포인트
@app.get("/api/local-llm/status")
async def local_llm_status():
    logger.info("LLM 상태 엔드포인트 호출됨")
    try:
        # LM Studio 기본 URL
        base_url = "http://127.0.0.