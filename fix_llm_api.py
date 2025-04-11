"""
FastAPI 서버에 직접 LLM API 엔드포인트를 추가하는 스크립트
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/local-llm/status")
async def local_llm_status():
    """
    로컬 LLM 상태를 확인하는 직접 엔드포인트
    """
    return {
        "enabled": True,
        "connected": False,
        "base_url": "http://127.0.0.1:1234",
        "error": "LM Studio에 연결할 수 없습니다. LM Studio가 실행 중인지 확인해주세요."
    }

@app.get("/api/local-llm/ping")
async def local_llm_ping():
    """
    LLM API 핑 테스트
    """
    return {"status": "ok", "message": "LLM API 서버가 정상적으로 응답하고 있습니다."}

@app.get("/")
async def root():
    """
    기본 경로 테스트
    """
    return {"message": "임시 API 서버가 실행 중입니다."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
