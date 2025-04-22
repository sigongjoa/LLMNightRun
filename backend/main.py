#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Night Run 백엔드 API 서버

FastAPI 기반 API 서버로, LLM과의 상호작용을 위한 엔드포인트를 제공합니다.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
import logging
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(title="LLM Night Run API", description="로컬 LLM을 위한 API 서버")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용, 프로덕션에서는 구체적으로 설정하세요)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("backend.api")

# 모델 정의
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    system_message: Optional[str] = None
    model: Optional[str] = "default_model"
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0

class ModelInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# 가상의 모델 데이터 (실제로는 설정에서 로드하거나 LLM 서비스에서 가져와야 함)
MODELS = [
    ModelInfo(id="default_model", name="Default Model", description="기본 LLM 모델"),
    ModelInfo(id="gpt-3.5-turbo", name="GPT 3.5 Turbo", description="OpenAI GPT-3.5 Turbo 모델"),
    ModelInfo(id="llama-2-7b", name="Llama 2 7B", description="Meta Llama 2 7B 모델"),
]

# 엔드포인트 정의
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "LLM Night Run API에 오신 것을 환영합니다!"}

@app.get("/v1/models")
async def get_models():
    """사용 가능한 모델 목록 가져오기"""
    return {"data": [model.dict() for model in MODELS]}

@app.get("/v1/ping")
async def ping():
    """서버 상태 확인"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """채팅 완료 요청 처리"""
    try:
        # 요청 로깅
        logger.info(f"채팅 요청 받음: 모델={request.model}, 메시지 수={len(request.messages)}")
        
        # 실제 구현에서는 여기서 LLM 모델로 요청을 보내고 응답을 받아야 함
        # 지금은 예시 응답만 반환
        
        # 마지막 사용자 메시지 가져오기
        last_user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        # 응답 생성
        if not last_user_message:
            response_text = "질문을 이해하지 못했습니다. 다시 말씀해 주세요."
        else:
            response_text = f"<think>\n현재 메시지: {last_user_message}\n</think>\n\n{last_user_message}에 대한 답변입니다. 이는 샘플 응답입니다."
        
        return {
            "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 50,  # 예시 값
                "completion_tokens": len(response_text.split()),  # 단어 수로 대략적인 토큰 수 추정
                "total_tokens": 50 + len(response_text.split())
            }
        }
    
    except Exception as e:
        logger.error(f"채팅 완료 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/status")
async def get_status():
    """LLM 서비스 상태 확인"""
    return {
        "status": "running",
        "models_loaded": [model.id for model in MODELS],
        "api_version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
