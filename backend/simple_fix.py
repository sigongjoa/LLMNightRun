from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="로컬 LLM 응급 서버")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 경로
@app.get("/")
async def root():
    print("루트 엔드포인트가 호출되었습니다")
    return {"message": "간단한 LLM 응급 서버가 실행 중입니다."}

# 로컬 LLM 상태 엔드포인트
@app.get("/api/local-llm/status")
async def llm_status():
    print("LLM 상태 엔드포인트가 호출되었습니다")
    return {
        "enabled": True,
        "connected": True,
        "base_url": "http://127.0.0.1:1234",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

# 로컬 LLM 핑 엔드포인트
@app.get("/api/local-llm/ping")
async def llm_ping():
    print("LLM 핑 엔드포인트가 호출되었습니다")
    return {"status": "ok", "message": "응급 LLM 서버가 응답 중입니다."}

# 로컬 LLM 채팅 엔드포인트
@app.post("/api/local-llm/chat")
async def llm_chat(request: Request):
    print("LLM 채팅 엔드포인트가 호출되었습니다")
    data = await request.json()
    
    return {
        "content": "이것은 응급 서버의 응답입니다. LM Studio가 연결되지 않았습니다.",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

if __name__ == "__main__":
    print("응급 LLM API 서버를 시작합니다...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
