"""
로컬 LLM 구성 모듈

LM Studio 등 로컬에서 실행되는 LLM 관련 설정을 정의합니다.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234"

class LocalLLMConfig(BaseModel):
    """로컬 LLM 구성 모델"""
    
    enabled: bool = True
    base_url: str = DEFAULT_LM_STUDIO_URL
    name: str = "LM Studio DeepSeek"
    model_id: str = "deepseek-r1-distill-qwen-7b"
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60  # 초


# 기본 로컬 LLM 구성
default_local_llm_config = LocalLLMConfig()
