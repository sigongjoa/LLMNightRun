from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    print("Root endpoint called")
    return {"message": "Server is running"}

@app.get("/api/local-llm/status")
async def local_llm_status():
    print("Local LLM status endpoint called")
    return {
        "enabled": True,
        "connected": True,
        "base_url": "http://127.0.0.1:1234",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

@app.get("/api/local-llm/ping")
async def local_llm_ping():
    print("Local LLM ping endpoint called")
    return {"status": "ok", "message": "LLM API server is responding"}

@app.post("/api/local-llm/chat")
async def local_llm_chat(request_data: dict):
    print(f"Local LLM chat endpoint called with: {request_data}")
    return {
        "content": "This is a test response from the LLM API.",
        "model_id": "deepseek-r1-distill-qwen-7b"
    }

if __name__ == "__main__":
    print("Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=9999)
