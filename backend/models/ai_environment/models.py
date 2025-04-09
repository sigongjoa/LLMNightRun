"""
AI 환경설정 모델 정의
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

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
