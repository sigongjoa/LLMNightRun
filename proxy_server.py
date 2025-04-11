from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import asyncio

app = FastAPI(title="LLM API 프록시")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 대상 서버 URL
TARGET_SERVER = "http://localhost:8008"

@app.get("/")
async def root():
    print("루트 엔드포인트 호출됨")
    return {"message": "API 프록시 서버가 실행 중입니다."}

@app.get("/{path:path}")
async def proxy_get(path: str, request: Request):
    print(f"GET 요청 프록시: /{path}")
    url = f"{TARGET_SERVER}/{path}"
    
    # 쿼리 파라미터 추가
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            print(f"프록시 응답: {response.status_code}")
            return response.json()
        except Exception as e:
            print(f"프록시 오류: {str(e)}")
            return {"error": str(e)}

@app.post("/{path:path}")
async def proxy_post(path: str, request: Request):
    print(f"POST 요청 프록시: /{path}")
    url = f"{TARGET_SERVER}/{path}"
    
    # 요청 본문 가져오기
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=body)
            print(f"프록시 응답: {response.status_code}")
            return response.json()
        except Exception as e:
            print(f"프록시 오류: {str(e)}")
            return {"error": str(e)}

@app.put("/{path:path}")
async def proxy_put(path: str, request: Request):
    print(f"PUT 요청 프록시: /{path}")
    url = f"{TARGET_SERVER}/{path}"
    
    # 요청 본문 가져오기
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, json=body)
            print(f"프록시 응답: {response.status_code}")
            return response.json()
        except Exception as e:
            print(f"프록시 오류: {str(e)}")
            return {"error": str(e)}

@app.delete("/{path:path}")
async def proxy_delete(path: str, request: Request):
    print(f"DELETE 요청 프록시: /{path}")
    url = f"{TARGET_SERVER}/{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(url)
            print(f"프록시 응답: {response.status_code}")
            return response.json()
        except Exception as e:
            print(f"프록시 오류: {str(e)}")
            return {"error": str(e)}

if __name__ == "__main__":
    # 노트: 8000번 포트가 이미 사용 중이므로 8080 포트를 사용합니다.
    print("프록시 서버 시작하는 중...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
