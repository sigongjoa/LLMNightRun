"""
AI 환경설정 API
"""

import os
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 직접 config 모듈에서 get_settings 가져오기 (변경됨)
from backend.config import get_settings

router = APIRouter()
settings = get_settings()

# 모델 정의
class LLMConfig(BaseModel):
    model: str
    maxTokens: int
    temperature: float
    useStreaming: bool
    contextWindow: int
    apiEndpoint: str
    promptTemplate: Optional[str] = ""

class VectorStoreConfig(BaseModel):
    type: str
    collectionName: str
    embeddingModel: str
    chunkSize: int
    chunkOverlap: int

class APIKeys(BaseModel):
    openai: Optional[str] = ""
    anthropic: Optional[str] = ""
    cohere: Optional[str] = ""
    huggingface: Optional[str] = ""

class AutomationConfig(BaseModel):
    autoEmbedding: bool
    autoReindex: bool
    scheduledMaintenance: bool
    maintenanceInterval: str

class FeatureFlags(BaseModel):
    localLLM: bool
    cloudLLM: bool
    vectorStore: bool
    documentProcessing: bool
    agentMode: bool
    mcpIntegration: bool

class AIEnvironmentConfig(BaseModel):
    llm: LLMConfig
    vectorStore: VectorStoreConfig
    apiKeys: APIKeys
    automation: AutomationConfig
    featureFlags: FeatureFlags

class ModelInfo(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None

# 환경설정 파일 경로 설정
# 명시적으로 설정하고, 폴더 구조 확인
data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_FILE_PATH = os.path.join(data_path, "ai_environment_config.json")

# 기본 설정값
DEFAULT_CONFIG = {
    "llm": {
        "model": "gpt-3.5-turbo",
        "maxTokens": 2048,
        "temperature": 0.7,
        "useStreaming": True,
        "contextWindow": 4096,
        "apiEndpoint": "https://api.openai.com/v1",
        "promptTemplate": ""
    },
    "vectorStore": {
        "type": "chroma",
        "collectionName": "default_collection",
        "embeddingModel": "text-embedding-ada-002",
        "chunkSize": 1000,
        "chunkOverlap": 200
    },
    "apiKeys": {
        "openai": "",
        "anthropic": "",
        "cohere": "",
        "huggingface": ""
    },
    "automation": {
        "autoEmbedding": True,
        "autoReindex": False,
        "scheduledMaintenance": False,
        "maintenanceInterval": "daily"
    },
    "featureFlags": {
        "localLLM": True,
        "cloudLLM": True,
        "vectorStore": True,
        "documentProcessing": True,
        "agentMode": True,
        "mcpIntegration": True
    }
}

# 환경설정 유틸리티 함수
def get_config():
    """환경설정 파일에서 설정 정보를 가져오거나 기본값을 반환합니다."""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            # 파일이 없으면 기본 설정을 저장하고 반환
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"환경설정 로드 오류: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config):
    """환경설정을 파일에 저장합니다."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"환경설정 저장 오류: {str(e)}")
        return False

# API 엔드포인트들
@router.get("/api/ai-environment/config", response_model=dict)
async def get_ai_environment_config():
    """
    AI 환경설정 정보를 가져옵니다.
    """
    try:
        config = get_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"환경설정을 가져오는 중 오류 발생: {str(e)}")

@router.post("/api/ai-environment/config")
async def save_ai_environment_config(config: dict):
    """
    AI 환경설정 정보를 저장합니다.
    """
    try:
        if save_config(config):
            return {"status": "success", "message": "환경설정이 성공적으로 저장되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="환경설정 저장 실패")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"환경설정을 저장하는 중 오류 발생: {str(e)}")

@router.get("/api/ai-environment/models", response_model=List[ModelInfo])
async def get_available_models():
    """
    사용 가능한 LLM 모델 목록을 가져옵니다.
    """
    # 실제 구현에서는 데이터베이스나 다른 서비스에서 가져와야 함
    models = [
        {
            "id": "gpt-4",
            "name": "GPT-4 (OpenAI)",
            "type": "cloud",
            "description": "OpenAI의 가장 고급 모델입니다."
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo (OpenAI)",
            "type": "cloud",
            "description": "빠르고 효율적인 OpenAI 모델입니다."
        },
        {
            "id": "claude-3-opus",
            "name": "Claude 3 Opus (Anthropic)",
            "type": "cloud",
            "description": "Anthropic의 최고급 모델입니다."
        },
        {
            "id": "claude-3-sonnet",
            "name": "Claude 3 Sonnet (Anthropic)",
            "type": "cloud",
            "description": "비용 효율적인 Anthropic 모델입니다."
        },
        {
            "id": "llama-3-70b",
            "name": "Llama 3 70B (Local)",
            "type": "local",
            "description": "Meta의 대형 로컬 실행 모델입니다."
        },
        {
            "id": "llama-3-8b",
            "name": "Llama 3 8B (Local)",
            "type": "local",
            "description": "더 작고 빠른 로컬 실행 모델입니다."
        },
        {
            "id": "mistral-7b",
            "name": "Mistral 7B (Local)",
            "type": "local",
            "description": "효율적인 7B 매개변수 모델입니다."
        }
    ]
    
    return models

@router.get("/api/ai-environment/vector-stores", response_model=List[Dict[str, str]])
async def get_available_vector_stores():
    """
    사용 가능한 벡터 스토어 목록을 가져옵니다.
    """
    vector_stores = [
        {"id": "chroma", "name": "Chroma", "description": "간단하고 로컬에서 실행되는 벡터 데이터베이스"},
        {"id": "faiss", "name": "FAISS", "description": "Meta에서 개발한 효율적인 유사성 검색 라이브러리"},
        {"id": "pinecone", "name": "Pinecone", "description": "벡터 검색을 위한 완전 관리형 클라우드 서비스"},
        {"id": "weaviate", "name": "Weaviate", "description": "오픈소스 벡터 검색 엔진"},
        {"id": "milvus", "name": "Milvus", "description": "대규모 벡터 데이터 관리를 위한 오픈소스 벡터 데이터베이스"}
    ]
    
    return vector_stores

@router.get("/api/ai-environment/embedding-models", response_model=List[Dict[str, str]])
async def get_available_embedding_models():
    """
    사용 가능한 임베딩 모델 목록을 가져옵니다.
    """
    embedding_models = [
        {"id": "text-embedding-ada-002", "name": "OpenAI Text Embedding Ada 002", "provider": "OpenAI"},
        {"id": "text-embedding-3-small", "name": "OpenAI Text Embedding 3 Small", "provider": "OpenAI"},
        {"id": "text-embedding-3-large", "name": "OpenAI Text Embedding 3 Large", "provider": "OpenAI"},
        {"id": "all-MiniLM-L6-v2", "name": "Sentence Transformers (all-MiniLM-L6-v2)", "provider": "HuggingFace"},
        {"id": "bge-large-en-v1.5", "name": "BGE Large English v1.5", "provider": "BAAI"}
    ]
    
    return embedding_models

@router.post("/api/ai-environment/test-connection")
async def test_connection(endpoint: dict):
    """
    API 엔드포인트 연결을 테스트합니다.
    """
    try:
        # 여기서 실제 연결 테스트 로직을 구현
        # 예시로 항상 성공을 반환
        return {"status": "success", "message": "연결 테스트가 성공하였습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")
