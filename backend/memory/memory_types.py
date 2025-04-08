"""
Memory type definitions for LLMNightRun.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import datetime


class MemoryType(str, Enum):
    """Types of memory that can be stored."""
    
    CONVERSATION = "conversation"
    EXPERIMENT = "experiment"
    CODE = "code"
    RESULT = "result"
    NOTE = "note"


class Memory(BaseModel):
    """Base model for memory items."""
    
    id: Optional[str] = None
    content: str
    type: MemoryType
    timestamp: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        """Set timestamp if not provided."""
        return v or int(datetime.datetime.now().timestamp())


class MemorySearch(BaseModel):
    """Model for memory search parameters."""
    
    query: str
    top_k: int = 5
    memory_types: Optional[List[MemoryType]] = None
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    tags: Optional[List[str]] = None
    
    @validator('date_from', 'date_to', pre=True)
    def parse_datetime(cls, v):
        """Parse datetime from ISO format."""
        if isinstance(v, str):
            return datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class MemoryResponse(BaseModel):
    """Model for memory response."""
    
    id: str
    content: str
    type: MemoryType
    timestamp: int
    metadata: Dict[str, Any]
    score: Optional[float] = None


class MemoryBatch(BaseModel):
    """Model for batch memory operations."""
    
    memories: List[Memory]


class ExperimentMemory(Memory):
    """Model for experiment memory."""
    
    type: MemoryType = MemoryType.EXPERIMENT
    experiment_id: str
    model_name: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Experiment with GPT-4 showed 87% accuracy on task X",
                "experiment_id": "exp_123",
                "model_name": "gpt-4",
                "prompt": "Analyze the following text...",
                "response": "The analysis reveals...",
                "metrics": {"accuracy": 0.87, "latency": 3.2},
                "metadata": {
                    "tags": ["gpt-4", "analysis", "high-accuracy"]
                }
            }
        }


class ConversationMemory(Memory):
    """Model for conversation memory."""
    
    type: MemoryType = MemoryType.CONVERSATION
    conversation_id: str
    message_id: Optional[str] = None
    role: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "content": "User asked about prompt optimization techniques",
                "conversation_id": "conv_456",
                "message_id": "msg_123",
                "role": "user",
                "message": "What are some techniques for optimizing prompts?",
                "metadata": {
                    "tags": ["prompt-engineering", "question"]
                }
            }
        }


class CodeMemory(Memory):
    """Model for code memory."""
    
    type: MemoryType = MemoryType.CODE
    code: str
    language: str
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Function to preprocess text for embeddings",
                "code": "def preprocess_text(text):\n    return text.lower()",
                "language": "python",
                "description": "Removes case sensitivity from text",
                "metadata": {
                    "tags": ["preprocessing", "nlp"]
                }
            }
        }
