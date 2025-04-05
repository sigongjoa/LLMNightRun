"""
인덱싱 관련 모델 정의 모듈

코드베이스 인덱싱 관련 데이터 구조를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import IdentifiedModel
from .enums import IndexingStatus, IndexingFrequency


class CodebaseIndexingSettings(IdentifiedModel):
    """코드베이스 인덱싱 설정 모델"""
    codebase_id: int
    is_enabled: bool = True
    frequency: IndexingFrequency = IndexingFrequency.ON_COMMIT
    excluded_patterns: List[str] = Field(default_factory=list)  # e.g. ["*.log", "node_modules/*"]
    priority_patterns: List[str] = Field(default_factory=list)  # e.g. ["src/main/*", "*.py"]
    embedding_model: str = "openai/text-embedding-ada-002"  # 기본 임베딩 모델
    chunk_size: int = 1000  # 코드 청크 크기 (문자 수)
    chunk_overlap: int = 200  # 청크 간 겹침 정도
    include_comments: bool = True  # 주석 포함 여부
    max_files_per_run: int = 100  # 한 번의 인덱싱 실행당 최대 파일 수


class CodebaseIndexingRun(IdentifiedModel):
    """코드베이스 인덱싱 실행 기록 모델"""
    codebase_id: int
    status: IndexingStatus = IndexingStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    files_processed: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    error_message: Optional[str] = None
    is_full_index: bool = False  # 전체 인덱싱 vs 증분 인덱싱
    triggered_by: str = "manual"  # manual, scheduler, webhook 등


class CodeEmbedding(IdentifiedModel):
    """코드 임베딩 모델"""
    codebase_id: int
    file_id: int
    chunk_id: str  # 파일 내 청크 식별자 (e.g. "file.py:1-50")
    content: str  # 원본 코드 청크
    embedding: List[float] = Field(default_factory=list)  # 벡터 임베딩
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 추가 메타데이터


class EmbeddingSearchResult(BaseModel):
    """임베딩 검색 결과 모델"""
    file_id: int
    file_path: str
    chunk_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]


class CodeSearchQuery(BaseModel):
    """코드 검색 쿼리 모델"""
    codebase_id: int
    query: str
    limit: int = 10
    threshold: Optional[float] = 0.5  # 유사도 임계값
    file_patterns: Optional[List[str]] = None  # 검색할 파일 패턴
    exclude_patterns: Optional[List[str]] = None  # 제외할 파일 패턴


class IndexingSettingsUpdate(BaseModel):
    """인덱싱 설정 업데이트 모델"""
    is_enabled: Optional[bool] = None
    frequency: Optional[IndexingFrequency] = None
    excluded_patterns: Optional[List[str]] = None
    priority_patterns: Optional[List[str]] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    include_comments: Optional[bool] = None
    max_files_per_run: Optional[int] = None


class TriggerIndexingRequest(BaseModel):
    """인덱싱 트리거 요청 모델"""
    codebase_id: int
    is_full_index: bool = False
    priority_files: Optional[List[int]] = None  # 우선적으로 인덱싱할 파일 ID 목록


class IndexingRunResponse(BaseModel):
    """인덱싱 실행 응답 모델"""
    run_id: int
    status: IndexingStatus
    message: str
    start_time: Optional[datetime] = None